# app/schemas/generate.py
from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    style_name: str = Field(..., description="Имя стиля (например, username канала)")
    topic: str = Field(..., description="Тема поста")
    goal: str = Field(..., description="Цель поста")
    audience: str = Field(..., description="Целевая аудитория")
    max_chars: int = Field(1200, description="Максимальная длина поста в символах")

class GenerateResponse(BaseModel):
    style_name: str
    topic: str
    goal: str
    audience: str
    post: str


class GenerateFromChannelRequest(BaseModel):
    channel_username: str = Field(..., description="Username канала без https://t.me/")
    topic: str
    goal: str
    audience: str
    max_chars: int = 1200
    force_recreate_style: bool = Field(
        False,
        description="Если true — стиль пересоздаётся даже если уже существует",
    )

class GenerateFromChannelResponse(BaseModel):
    style_name: str
    style_was_created: bool
    topic: str
    goal: str
    audience: str
    post: str
