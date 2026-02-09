# app/api/v1/routes.py
from fastapi import APIRouter, HTTPException

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