# app/schemas/user.py
from pydantic import BaseModel, Field
from typing import Optional


class UserResponse(BaseModel):
    telegram_id: int = Field(..., description="Telegram ID пользователя")
    active_style_name: Optional[str] = Field(
        None, description="Имя активного стиля, если выбрано"
    )
    channel_username: Optional[str] = Field(
        None, description="Username канала (без @), если сохранён"
    )
    channel_chat_id: Optional[int] = Field(
        None, description="Числовой chat_id канала для автопостинга, если привязан"
    )


class SetStyleRequest(BaseModel):
    telegram_id: int
    style_name: str


class SetStyleResponse(BaseModel):
    telegram_id: int
    style_name: str
