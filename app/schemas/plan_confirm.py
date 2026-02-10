# app/schemas/plan_confirm.py
from pydantic import BaseModel, Field
from typing import List
from app.schemas.plan import PlanItem

class PlanConfirmRequest(BaseModel):
    user_telegram_id: int = Field(..., description="Telegram ID пользователя")
    style_name: str
    start_date: str
    goal: str
    audience: str
    items: List[PlanItem]

class PlanConfirmResponse(BaseModel):
    plan_id: int
    user_telegram_id: int
    style_name: str
    items_count: int
