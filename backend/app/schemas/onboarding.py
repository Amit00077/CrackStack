from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class OnboardingQuestion(BaseModel):
    id: str
    question: str
    type: str = Field(..., pattern="^(text|select|multi-select|radio|number|date)$")
    required: bool = True
    options: Optional[list[str]] = None
    placeholder: Optional[str] = None


class OnboardingQuestionsResponse(BaseModel):
    onboarding_complete: bool
    questions: list[OnboardingQuestion] = []
    session_id: Optional[str] = None


class SubmitAnswersRequest(BaseModel):
    goal: str
    session_id: Optional[str] = None
    answers: dict[str, str | list[str] | int | None] = {}


class CreateOnboardingRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=500)
    skill_level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    daily_study_hours: int = Field(..., ge=1, le=24)
    target_date: date
    notes: Optional[str] = Field(None, max_length=1000)


class OnboardingCompleteResponse(BaseModel):
    onboarding_complete: bool
    missing_information: Optional[list[str]] = None


class OnboardingPhaseWeek(BaseModel):
    week_number: int
    title: str
    tasks: list[dict] = []


class OnboardingPhase(BaseModel):
    title: str
    weeks: list[OnboardingPhaseWeek] = []


class OnboardingRoadmapResponse(BaseModel):
    phases: list[OnboardingPhase] = []
