from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    goal_text: str
    target_company: str = Field(..., max_length=255)
    target_role: str = Field(..., max_length=255)
    duration_months: int = Field(..., ge=1, le=36)
    daily_study_hours: int = Field(..., ge=1, le=16)
    skill_level: str = Field(..., max_length=50)
    weak_areas: list[str] = Field(default_factory=list)
    start_date: date
    target_date: Optional[date] = None


class GoalUpdate(BaseModel):
    goal_text: Optional[str] = None
    target_company: Optional[str] = Field(None, max_length=255)
    target_role: Optional[str] = Field(None, max_length=255)
    duration_months: Optional[int] = Field(None, ge=1, le=36)
    daily_study_hours: Optional[int] = Field(None, ge=1, le=16)
    skill_level: Optional[str] = Field(None, max_length=50)
    weak_areas: Optional[list[str]] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    is_active: Optional[bool] = None


class GoalResponse(BaseModel):
    id: str
    user_id: str
    goal_text: str
    target_company: str
    target_role: str
    duration_months: int
    daily_study_hours: int
    skill_level: str
    weak_areas: list[str]
    start_date: date
    target_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
