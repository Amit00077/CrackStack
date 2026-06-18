from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.schemas.task import DailyTaskResponse


class CurrentWeekInfo(BaseModel):
    week_number: int
    title: str
    theme: str = ""


class TodayTasksResponse(BaseModel):
    tasks: list[DailyTaskResponse]
    completion_pct: float
    done_count: int
    total_count: int
    message: Optional[str] = None
    current_week: Optional[CurrentWeekInfo] = None


class DayGrid(BaseModel):
    date: str
    day_name: str
    is_today: bool
    tasks: list[DailyTaskResponse]


class WeeklyGridResponse(BaseModel):
    week_start: str
    days: list[DayGrid]
