from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class WeeklyReportResponse(BaseModel):
    id: str
    user_id: str
    week_start: date
    week_end: date
    week_number: int
    letter_grade: str
    completion_rate: float = Field(validation_alias="completed_rate")
    readiness_score: float
    strengths: list[str]
    improvement_areas: list[str]
    recommendations: list[str]
    verdict: str
    ai_generated: bool
    is_current: bool
    created_at: datetime
    completed_tasks: int
    total_tasks: int
    summary: Optional[str] = None
    ai_feedback: Optional[str] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ReportGenerateResponse(BaseModel):
    message: str
    report_id: str


class PaginatedReportsResponse(BaseModel):
    items: list[WeeklyReportResponse]
    total: int
    page: int
    limit: int
    pages: int