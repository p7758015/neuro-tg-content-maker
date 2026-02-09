# app/schemas/styles.py
from pydantic import BaseModel, Field
from typing import List, Dict

class StyleInfo(BaseModel):
    name: str = Field(..., description="Имя стиля (обычно username канала)")

class StylesListResponse(BaseModel):
    styles: List[StyleInfo]

class StyleDetailResponse(BaseModel):
    name: str
    style: Dict

class RenameStyleRequest(BaseModel):
    old_name: str
    new_name: str

class DeleteStyleResponse(BaseModel):
    name: str
    deleted: bool
