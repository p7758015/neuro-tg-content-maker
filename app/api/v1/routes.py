# app/api/v1/routes.py
from app.schemas.plan import PlanGenerateRequest, PlanGenerateResponse
from app.services.plan_generator import generate_week_plan
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.db.session import get_session
from app.db.models import User, ContentPlan, PlanItem
from app.schemas.plan_confirm import PlanConfirmRequest, PlanConfirmResponse
from app.schemas.plan import PlanDetailResponse
from app.schemas.user import UserResponse, SetStyleRequest, SetStyleResponse
from datetime import datetime
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
from app.services.post_generator import generate_post
from app.services.tg_loader import fetch_channel_posts
from app.services.style_extractor import extract_style

router = APIRouter(prefix="/v1", tags=["content"])


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
async def generate_from_channel(payload: GenerateFromChannelRequest) -> GenerateFromChannelResponse:
    username = payload.channel_username.replace("https://t.me/", "").replace("@", "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="Некорректный username канала")

    style_name = suggest_style_name_from_username(username)

    style = load_style(style_name)
    style_was_created = False

    if style is None or payload.force_recreate_style:
        # тянем последние N сообщений канала
        posts = await fetch_channel_posts(username, limit=50)
        if not posts:
            raise HTTPException(
                status_code=404,
                detail=f"Не удалось получить сообщения из канала '{username}'",
            )

        # берём, например, последние 5–10 постов для анализа
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
        # маловероятно, но на всякий
        raise HTTPException(status_code=500, detail="Стиль не найден после переименования")
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
    # 1. создаём/находим пользователя
    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == payload.user_telegram_id)
        ).first()
        if not user:
            user = User(telegram_id=payload.user_telegram_id, active_style_name=payload.style_name)
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            # обновим активный стиль
            user.active_style_name = payload.style_name
            session.add(user)
            session.commit()
            session.refresh(user)

        # 2. создаём план
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

        # 3. добавляем items
        items_models = []
        for item in payload.items:
            items_models.append(
                PlanItem(
                    plan_id=plan.id,
                    day_index=item.day_index,
                    date=item.date,
                    time=item.time,
                    post_type=item.post_type,
                    topic=item.topic,
                    notes=item.notes or "",
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
            raise HTTPException(status_code=404, detail="Для пользователя нет планов")

        items = session.exec(
            select(PlanItem).where(PlanItem.plan_id == plan.id)
        ).all()

        # Преобразуем PlanItem -> схему PlanItem (из pydantic)
        from app.schemas.plan import PlanItem as PlanItemSchema

        items_schema = [
            PlanItemSchema(
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

@router.get("/user/{telegram_id}", response_model=UserResponse)
async def get_user(telegram_id: int) -> UserResponse:
    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == telegram_id)
        ).first()

        if not user:
            # пока просто возвращаем пустого пользователя без ошибки
            return UserResponse(telegram_id=telegram_id, active_style_name=None)

        return UserResponse(
            telegram_id=user.telegram_id,
            active_style_name=user.active_style_name,
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

@router.post("/autopost/next/{telegram_id}")
async def autopost_next(telegram_id: int):
    """
    Для демо: ищем ближайший запланированный пост для пользователя и отправляем его в Telegram.
    Пока отправляем в личный чат с пользователем (telegram_id как chat_id).
    """
    now = datetime.utcnow()

    with get_session() as session:
        user = session.exec(
            select(User).where(User.telegram_id == telegram_id)
        ).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # берём самый свежий план
        plan = session.exec(
            select(ContentPlan)
            .where(ContentPlan.user_id == user.id)
            .order_by(ContentPlan.created_at.desc())
        ).first()
        if not plan:
            raise HTTPException(status_code=404, detail="План для пользователя не найден")

        items = session.exec(
            select(PlanItem)
            .where(PlanItem.plan_id == plan.id, PlanItem.status == "planned")
            .order_by(PlanItem.date, PlanItem.time)
        ).all()

        if not items:
            raise HTTPException(status_code=404, detail="Нет запланированных постов")

        # для простоты берём самый ранний planned
        item = items[0]

        style = load_style(plan.style_name)
        if not style:
            raise HTTPException(status_code=500, detail="Стиль не найден на диске")

        # генерируем пост
        post_text = generate_post(
            style=style,
            topic=item.topic,
            goal=plan.goal,
            audience=plan.audience,
        )

        # отправляем в личку пользователю
        await send_telegram_message(chat_id=telegram_id, text=post_text)

        # обновляем статус
        item.status = "sent"
        item.generated_post = post_text
        item.sent_at = datetime.utcnow()
        session.add(item)
        session.commit()

        return {
            "status": "ok",
            "plan_id": plan.id,
            "item_id": item.id,
            "sent_to": telegram_id,
        }
