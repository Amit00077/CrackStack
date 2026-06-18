from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class RoadmapWeekCreate(BaseModel):
    roadmap_id: str
    week_number: int
    title: str = Field(..., max_length=255)
    description: str


class RoadmapWeekUpdate(BaseModel):
    week_number: Optional[int] = None
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    sort_order: Optional[int] = None


class RoadmapTaskCreate(BaseModel):
    task_text: str
    category: str = "study"
    time_estimate: int = 60


class RoadmapTaskUpdate(BaseModel):
    task_text: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    time_estimate: Optional[int] = None
    is_completed: Optional[bool] = None
    sort_order: Optional[int] = None


class RoadmapTaskResponse(BaseModel):
    id: str
    week_id: str
    goal_id: Optional[str] = None
    user_id: Optional[str] = None
    task_text: str
    category: str
    time_estimate: int
    day_offset: Optional[int] = None
    assigned_date: Optional[date] = None
    is_completed: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RoadmapWeekResponse(BaseModel):
    id: str
    roadmap_id: str
    week_number: int
    title: str
    description: Optional[str] = None
    sort_order: int
    start_date: Optional[date] = None
    status: str = "pending"
    tasks: list[RoadmapTaskResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ReorderItem(BaseModel):
    id: str
    sort_order: int


class ReorderRequest(BaseModel):
    items: list[ReorderItem]


class RoadmapResponse(BaseModel):
    id: str
    goal_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    is_active: bool
    weeks_count: int
    weeks: list[RoadmapWeekResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
