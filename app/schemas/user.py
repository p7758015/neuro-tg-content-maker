# app/schemas/user.py
from pydantic import BaseModel, Field
from typing import Optional

class UserResponse(BaseModel):
    telegram_id: int = Field(..., description="Telegram ID пользователя")
    active_style_name: Optional[str] = Field(
        None, description="Имя активного стиля, если выбрано"
    )

class SetStyleRequest(BaseModel):
    telegram_id: int
    style_name: str

class SetStyleResponse(BaseModel):
    telegram_id: int
    style_name: str
