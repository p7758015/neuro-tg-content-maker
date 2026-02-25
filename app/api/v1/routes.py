from app.schemas.plan import PlanGenerateRequest, PlanGenerateResponse
from app.services.plan_generator import generate_week_plan
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from pydantic import BaseModel, validator
from datetime import datetime
from typing import List
from app.db.session import get_session
from app.db.models import User, ContentPlan, PlanItem
from app.schemas.plan_confirm import PlanConfirmRequest, PlanConfirmResponse
from app.schemas.plan import PlanDetailResponse
from app.schemas.user import UserResponse, SetStyleRequest, SetStyleResponse
from app.services.telegram_sender import send_telegram_message
from app.services.post_generator import generate_post
from app.services.style_store import load_style
from app.schemas.generate import (
    GenerateRequest,
    GenerateResponse,
    GenerateFromChannelRequest,
    GenerateFromChannelResponse,
)
from app.schemas.styles import (
    StylesListResponse,
    StyleInfo,
    StyleDetailResponse,
    RenameStyleRequest,
    DeleteStyleResponse,
)
from app.services.style_store import (
    load_style,
    save_style,
    list_styles,
    delete_style,
    rename_style,
    suggest_style_name_from_username,
)
from app.services.tg_loader import fetch_channel_posts
from app.services.style_extractor import extract_style

router = APIRouter(tags=["content"])


class SetChannelRequest(BaseModel):
    telegram_id: int
    channel_username: str


class PlanUpdateItem(BaseModel):
    item_id: int
    time: str  # формат HH:MM

    @validator("time")
    def validate_time(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("time must be in format HH:MM")
        return v


class PlanUpdateTimesRequest(BaseModel):
    plan_id: int
    items: list[PlanUpdateItem]


class SetChannelChatIdRequest(BaseModel):
    telegram_id: int
    channel_chat_id: int


class LinkChannelRequest(BaseModel):
    telegram_id: int
    channel_chat_id: int


class AutopostUser(BaseModel):
    telegram_id: int


@router.post("/generate", response_model=GenerateResponse)
async def generate_content(payload: GenerateRequest) -> GenerateResponse:
    style = load_style(payload.style_name)
    if not style:
        raise HTTPException(
            status_code=404,
            detail=f"Стиль '{payload.style_name}' не найден. Сначала создайте его.",
        )

    post = generate_post(
        style=style,
        topic=payload.topic,
        goal=payload.goal,
        audience=payload.audience,
    )

    return GenerateResponse(
        style_name=payload.style_name,
        topic=payload.topic,
        goal=payload.goal,
        audience=payload.audience,
        post=post,
    )


@router.post("/generate-from-channel", response_model=GenerateFromChannelResponse)
async def generate_from_channel(
    payload: GenerateFromChannelRequest,
) -> GenerateFromChannelResponse:
    username = (
        payload.channel_username.replace("https://t.me/", "")
        .replace("@", "")
        .strip()
    )
    if not username:
        raise HTTPException(status_code=400, detail="Некорректный username канала")

    style_name = suggest_style_name_from_username(username)

    style = load_style(style_name)
    style_was_created = False

    if style is None or payload.force_recreate_style:
        posts = await fetch_channel_posts(username, limit=50)
        if not posts:
            raise HTTPException(
                status_code=404,
                detail=f"Не удалось получить сообщения из канала '{username}'",
            )

        sample_posts = posts[-10:] if len(posts) >= 10 else posts
        style = extract_style(sample_posts)
        save_style(style_name, style)
        style_was_created = True

    post = generate_post(
        style=style,
        topic=payload.topic,
        goal=payload.goal,
        audience=payload.audience,
    )

    return GenerateFromChannelResponse(
        style_name=style_name,
        style_was_created=style_was_created,
        topic=payload.topic,
        goal=payload.goal,
        audience=payload.audience,
        post=post,
    )


@router.get("/styles", response_model=StylesListResponse)
async def get_styles() -> StylesListResponse:
    names = list_styles()
    return StylesListResponse(styles=[StyleInfo(name=n) for n in names])


@router.get("/styles/{name}", response_model=StyleDetailResponse)
async def get_style(name: str) -> StyleDetailResponse:
    style = load_style(name)
    if not style:
        raise HTTPException(status_code=404, detail=f"Стиль '{name}' не найден")
    return StyleDetailResponse(name=name, style=style)


@router.post("/styles/rename", response_model=StyleDetailResponse)
async def rename_style_endpoint(payload: RenameStyleRequest) -> StyleDetailResponse:
    ok = rename_style(payload.old_name, payload.new_name)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Не удалось переименовать стиль. "
            "Проверь, что старое имя существует, а новое ещё не занято.",
        )
    style = load_style(payload.new_name)
    if not style:
        raise HTTPException(
            status_code=500, detail="Стиль не найден после переименования"
        )
    return StyleDetailResponse(name=payload.new_name, style=style)


@router.delete("/styles/{name}", response_model=DeleteStyleResponse)
async def delete_style_endpoint(name: str) -> DeleteStyleResponse:
    deleted = delete_style(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Стиль '{name}' не найден")
    return DeleteStyleResponse(name=name, deleted=True)


@router.post("/plan/generate", response_model=PlanGenerateResponse)
async def generate_plan(payload: PlanGenerateRequest) -> PlanGenerateResponse:
    style = load_style(payload.style_name)
    if not style:
        raise HTTPException(
            status_code=404,
            detail=f"Стиль '{payload.style_name}' не найден. Сначала создайте его.",
        )

    items = generate_week_plan(style, payload)

    return PlanGenerateResponse(
        style_name=payload.style_name,
        start_date=payload.start_date,
        goal=payload.goal,
        audience=payload.audience,
        items=items,
    )


@router.post("/plan/confirm", response_model=PlanConfirmResponse)
async def confirm_plan(payload: PlanConfirmRequest) -> PlanConfirmResponse:
    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == payload.user_telegram_id)
        ).first()
        if not user:
            user = User(
                telegram_id=payload.user_telegram_id,
                active_style_name=payload.style_name,
                autopost_enabled=True,  # включаем автопостинг при первом плане
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            user.active_style_name = payload.style_name
            user.autopost_enabled = True  # гарантируем включение при новом плане
            session.add(user)
            session.commit()
            session.refresh(user)

        plan = ContentPlan(
            user_id=user.id,
            style_name=payload.style_name,
            start_date=payload.start_date,
            goal=payload.goal,
            audience=payload.audience,
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)

        items_models = []
        for item in payload.items:
            # собираем datetime для расписания
            scheduled_at = datetime.strptime(
                f"{item.date} {item.time}", "%Y-%m-%d %H:%M"
            )

            items_models.append(
                PlanItem(
                    plan_id=plan.id,
                    day_index=item.day_index,
                    date=item.date,
                    time=item.time,
                    post_type=item.post_type,
                    topic=item.topic,
                    notes=item.notes or "",
                    scheduled_at=scheduled_at,
                )
            )
        session.add_all(items_models)
        session.commit()

        return PlanConfirmResponse(
            plan_id=plan.id,
            user_telegram_id=user.telegram_id,
            style_name=plan.style_name,
            items_count=len(items_models),
        )


@router.get("/plan/current/{user_telegram_id}", response_model=PlanDetailResponse)
async def get_current_plan(user_telegram_id: int) -> PlanDetailResponse:
    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == user_telegram_id)
        ).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        plan = session.exec(
            select(ContentPlan)
            .where(ContentPlan.user_id == user.id)
            .order_by(ContentPlan.created_at.desc())
        ).first()
        if not plan:
            raise HTTPException(
                status_code=404, detail="Для пользователя нет планов"
            )

        items = session.exec(
            select(PlanItem).where(PlanItem.plan_id == plan.id)
        ).all()

        from app.schemas.plan import PlanItem as PlanItemSchema

        items_schema = [
            PlanItemSchema(
                item_id=i.id,
                day_index=i.day_index,
                date=i.date,
                time=i.time,
                post_type=i.post_type,
                topic=i.topic,
                notes=i.notes,
            )
            for i in items
        ]

        return PlanDetailResponse(
            plan_id=plan.id,
            user_telegram_id=user.telegram_id,
            style_name=plan.style_name,
            start_date=plan.start_date,
            goal=plan.goal,
            audience=plan.audience,
            items=items_schema,
        )


@router.post("/plan/update-times")
async def update_plan_times(payload: PlanUpdateTimesRequest):
    with get_session() as session:
        plan = session.exec(
            select(ContentPlan).where(ContentPlan.id == payload.plan_id)
        ).first()
        if not plan:
            raise HTTPException(status_code=404, detail="План не найден")

        items_map = {
            i.id: i
            for i in session.exec(
                select(PlanItem).where(PlanItem.plan_id == plan.id)
            ).all()
        }

        if not items_map:
            raise HTTPException(status_code=404, detail="В плане нет пунктов")

        for upd in payload.items:
            item = items_map.get(upd.item_id)
            if not item:
                raise HTTPException(
                    status_code=400,
                    detail=f"Пункт плана с id={upd.item_id} не найден в этом плане",
                )
            item.time = upd.time
            # обновляем и datetime для расписания
            item.scheduled_at = datetime.strptime(
                f"{item.date} {item.time}", "%Y-%m-%d %H:%M"
            )
            session.add(item)

        session.commit()

        return {"status": "ok", "plan_id": plan.id, "updated": len(payload.items)}


@router.get("/user/{telegram_id}", response_model=UserResponse)
async def get_user(telegram_id: int) -> UserResponse:
    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == telegram_id)
        ).first()

        if not user:
            return UserResponse(
                telegram_id=telegram_id,
                active_style_name=None,
                channel_username=None,
                channel_chat_id=None,
            )

        return UserResponse(
            telegram_id=user.telegram_id,
            active_style_name=user.active_style_name,
            channel_username=user.channel_username,
            channel_chat_id=user.channel_chat_id,
        )


@router.post("/user/set-style", response_model=SetStyleResponse)
async def set_user_style(payload: SetStyleRequest) -> SetStyleResponse:
    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == payload.telegram_id)
        ).first()
        if not user:
            user = User(
                telegram_id=payload.telegram_id,
                active_style_name=payload.style_name,
            )
        else:
            user.active_style_name = payload.style_name

        session.add(user)
        session.commit()
        session.refresh(user)

        return SetStyleResponse(
            telegram_id=user.telegram_id,
            style_name=user.active_style_name,
        )


@router.post("/user/set-channel", response_model=UserResponse)
async def set_user_channel(payload: SetChannelRequest) -> UserResponse:
    username = (
        payload.channel_username.replace("https://t.me/", "")
        .replace("@", "")
        .strip()
    )
    if not username:
        raise HTTPException(status_code=400, detail="Некорректный username канала")

    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == payload.telegram_id)
        ).first()

        if not user:
            user = User(
                telegram_id=payload.telegram_id,
                channel_username=username,
            )
        else:
            user.channel_username = username

        session.add(user)
        session.commit()
        session.refresh(user)

        return UserResponse(
            telegram_id=user.telegram_id,
            active_style_name=user.active_style_name,
            channel_username=user.channel_username,
            channel_chat_id=user.channel_chat_id,
        )


@router.post("/user/link-channel", response_model=UserResponse)
async def link_channel(payload: LinkChannelRequest) -> UserResponse:
    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == payload.telegram_id)
        ).first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Пользователь не найден. "
                    "Сначала выполни /plan_week или /connect_channel в личке с ботом."
                ),
            )

        user.channel_chat_id = payload.channel_chat_id
        session.add(user)
        session.commit()
        session.refresh(user)

        return UserResponse(
            telegram_id=user.telegram_id,
            active_style_name=user.active_style_name,
            channel_username=user.channel_username,
            channel_chat_id=user.channel_chat_id,
        )


@router.post("/user/set-channel-chat-id", response_model=UserResponse)
async def set_user_channel_chat_id(
    payload: SetChannelChatIdRequest,
) -> UserResponse:
    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == payload.telegram_id)
        ).first()

        if not user:
            user = User(
                telegram_id=payload.telegram_id,
                channel_chat_id=payload.channel_chat_id,
            )
        else:
            user.channel_chat_id = payload.channel_chat_id

        session.add(user)
        session.commit()
        session.refresh(user)

        return UserResponse(
            telegram_id=user.telegram_id,
            active_style_name=user.active_style_name,
            channel_username=user.channel_username,
            channel_chat_id=user.channel_chat_id,
        )


@router.post("/autopost/next/{telegram_id}")
async def autopost_next(telegram_id: int):
    now = datetime.now()

    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        plan = session.exec(
            select(ContentPlan)
            .where(ContentPlan.user_id == user.id)
            .order_by(ContentPlan.created_at.desc())
        ).first()
        if not plan:
            raise HTTPException(
                status_code=404, detail="План для пользователя не найден"
            )

        # берём только те посты, время которых уже наступило
        item = session.exec(
            select(PlanItem)
            .where(
                PlanItem.plan_id == plan.id,
                PlanItem.status == "planned",
                PlanItem.scheduled_at <= now,
            )
            .order_by(PlanItem.scheduled_at)
        ).first()
        if not item:
            raise HTTPException(
                status_code=404, detail="Нет запланированных постов к отправке"
            )

        if item.generated_post:
            post_text = item.generated_post
        else:
            style = load_style(plan.style_name)
            if not style:
                raise HTTPException(
                    status_code=500, detail="Стиль не найден на диске"
                )

            post_text = generate_post(
                style=style,
                topic=item.topic,
                goal=plan.goal,
                audience=plan.audience,
            )
            item.generated_post = post_text

        target_chat_id = user.channel_chat_id or telegram_id

        await send_telegram_message(chat_id=target_chat_id, text=post_text)

        item.status = "sent"
        item.sent_at = datetime.utcnow()
        session.add(item)
        session.commit()

        return {
            "status": "ok",
            "plan_id": plan.id,
            "item_id": item.id,
            "sent_to": target_chat_id,
        }


@router.get("/autopost/preview/{telegram_id}")
async def autopost_preview(telegram_id: int):
    # now = datetime.now()  # тут теперь не нужен
    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        plan = session.exec(
            select(ContentPlan)
            .where(ContentPlan.user_id == user.id)
            .order_by(ContentPlan.created_at.desc())
        ).first()
        if not plan:
            raise HTTPException(
                status_code=404, detail="План для пользователя не найден"
            )

        # Берём просто ближайший planned-пост независимо от времени
        item = session.exec(
            select(PlanItem)
            .where(
                PlanItem.plan_id == plan.id,
                PlanItem.status == "planned",
            )
            .order_by(PlanItem.scheduled_at)  # или (PlanItem.date, PlanItem.time)
        ).first()
        if not item:
            raise HTTPException(
                status_code=404, detail="Нет запланированных постов к показу"
            )

        if item.generated_post:
            post_text = item.generated_post
        else:
            style = load_style(plan.style_name)
            if not style:
                raise HTTPException(
                    status_code=500, detail="Стиль не найден на диске"
                )

            post_text = generate_post(
                style=style,
                topic=item.topic,
                goal=plan.goal,
                audience=plan.audience,
            )
            item.generated_post = post_text
            session.add(item)
            session.commit()

        return {
            "plan_id": plan.id,
            "item_id": item.id,
            "post_text": post_text,
        }



@router.get("/users/autopost-enabled", response_model=List[AutopostUser])
async def get_autopost_enabled_users() -> list[AutopostUser]:
    with get_session() as session:
        users = session.exec(
            select(User).where(User.autopost_enabled == True)  # noqa: E712
        ).all()

        return [AutopostUser(telegram_id=u.telegram_id) for u in users]
