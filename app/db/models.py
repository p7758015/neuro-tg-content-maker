from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: int = Field(index=True, unique=True)
    active_style_name: Optional[str] = Field(default=None)
    channel_username: Optional[str] = Field(default=None)  # @username без @
    channel_chat_id: Optional[int] = Field(default=None)   # числовой chat_id канала
    autopost_enabled: bool = Field(default=False)          # включён ли автопостинг для пользователя

    plans: List["ContentPlan"] = Relationship(back_populates="user")


class ContentPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    style_name: str
    start_date: str
    goal: str
    audience: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="plans")
    items: List["PlanItem"] = Relationship(back_populates="plan")


class PlanItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="contentplan.id")
    day_index: int
    date: str
    time: str
    post_type: str
    topic: str
    notes: str = ""
    status: str = Field(default="planned")  # planned / generated / sent
    generated_post: Optional[str] = None
    sent_at: Optional[datetime] = None

    plan: ContentPlan = Relationship(back_populates="items")
