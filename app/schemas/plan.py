# app/schemas/plan.py
from typing import List, Optional
from pydantic import BaseModel, Field


class PlanItem(BaseModel):
    day_index: int = Field(..., ge=0, le=6)
    date: str = Field(..., description="Дата дня в формате YYYY-MM-DD")
    time: str = Field(..., description="Время публикации HH:MM")
    post_type: str = Field(..., description="Тип поста (прогрев, польза, продажа и т.п.)")
    topic: str = Field(..., description="Тема поста")
    notes: Optional[str] = Field("", description="Дополнительные пометки")

class PlanGenerateRequest(BaseModel):
    style_name: str = Field(..., description="Имя стиля")
    start_date: str = Field(..., description="Дата начала недели YYYY-MM-DD")
    goal: str = Field(..., description="Главная цель недели")
    audience: str = Field(..., description="Целевая аудитория")
    posts_per_day: int = Field(1, ge=1, le=3, description="Сколько постов в день планировать")

class PlanGenerateResponse(BaseModel):
    style_name: str
    start_date: str
    goal: str
    audience: str
    items: List[PlanItem]

class PlanDetailResponse(BaseModel):
    plan_id: int
    user_telegram_id: int
    style_name: str
    start_date: str
    goal: str
    audience: str
    items: List[PlanItem]
