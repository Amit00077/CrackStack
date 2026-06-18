from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class DailyTaskCreate(BaseModel):
    task_text: str
    category: Optional[str] = Field(None, max_length=100)
    time_estimate: Optional[int] = None
    assigned_date: date


class DailyTaskUpdate(BaseModel):
    task_text: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    time_estimate: Optional[int] = None
    sort_order: Optional[int] = None


class DailyTaskResponse(BaseModel):
    id: str
    user_id: str
    week_id: Optional[str] = None
    task_text: str
    category: Optional[str] = None
    time_estimate: int
    task_date: date
    is_done: bool
    completed_at: Optional[datetime] = None
    source: str
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
