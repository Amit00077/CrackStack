from __future__ import annotations

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.roadmap import Roadmap, RoadmapTask, RoadmapWeek
from app.models.user import User
from app.repositories.roadmap import (
    roadmap_repository,
    roadmap_task_repository,
    roadmap_week_repository,
)
from app.schemas.onboarding import (
    CreateOnboardingRequest,
    OnboardingPhase,
    OnboardingPhaseWeek,
    OnboardingRoadmapResponse,
    OnboardingQuestionsResponse,
    SubmitAnswersRequest,
)
from app.services.goal import goal_service
from app.services.onboarding import generate_onboarding_roadmap
from app.utils.timezone import get_week_start_from_goal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/questions", response_model=OnboardingQuestionsResponse)
async def get_questions(
    request: SubmitAnswersRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OnboardingQuestionsResponse:
    return OnboardingQuestionsResponse(
        onboarding_complete=True,
        questions=[],
    )


@router.post("/evaluate", response_model=OnboardingQuestionsResponse)
async def evaluate(
    request: SubmitAnswersRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OnboardingQuestionsResponse:
    return OnboardingQuestionsResponse(
        onboarding_complete=True,
        questions=[],
    )


@router.post("/complete", response_model=OnboardingRoadmapResponse)
async def complete_onboarding(
    request: CreateOnboardingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OnboardingRoadmapResponse:
    goal_text = request.goal
    skill_level = request.skill_level
    daily_study_hours = request.daily_study_hours
    target_date = request.target_date
    notes = request.notes

    try:
        today = date.today()
        duration_days = (target_date - today).days
        duration_months = max(round(duration_days / 30), 1)

        goal_data = dict(
            goal_text=goal_text,
            target_company=goal_text[:255],
            target_role=goal_text[:255],
            duration_months=duration_months,
            daily_study_hours=daily_study_hours,
            skill_level=skill_level,
            weak_areas=[],
            start_date=today,
            target_date=target_date,
        )

        if notes:
            goal_data["weak_areas"] = [notes]

        goal = await goal_service.create_goal(db, current_user.id, goal_data)
        roadmap_result = await generate_onboarding_roadmap(
            goal_text,
            {
                "skill_level": skill_level,
                "daily_study_hours": daily_study_hours,
                "duration_months": duration_months,
                "notes": notes or "",
            },
            db,
        )

        phases_out: list[OnboardingPhase] = []

        if roadmap_result.get("phases"):
            all_weeks = []
            for phase_data in roadmap_result["phases"]:
                for w in phase_data.get("weeks", []):
                    all_weeks.append(w)

            roadmap = await roadmap_repository.create(
                db,
                user_id=current_user.id,
                goal_id=goal.id,
                title=f"Roadmap to {goal_text}",
                description=f"Study plan for {goal_text}",
                weeks_count=len(all_weeks),
            )

            for week_data in all_weeks:
                week_start = get_week_start_from_goal(goal.start_date, week_data["week_number"])
                week = await roadmap_week_repository.create(
                    db,
                    roadmap_id=roadmap.id,
                    week_number=week_data["week_number"],
                    title=week_data["title"],
                    description=week_data.get("description", ""),
                    sort_order=week_data["week_number"],
                    start_date=week_start,
                    status="pending",
                )
                tasks = week_data.get("tasks", [])
                created_tasks = await roadmap_task_repository.bulk_create(db, week.id, tasks)
                for i, rt in enumerate(created_tasks):
                    day_offset = i + 1
                    rt.day_offset = day_offset
                    rt.assigned_date = week_start + timedelta(days=day_offset - 1)
                    rt.goal_id = goal.id
                    rt.user_id = current_user.id
                await db.flush()

            for phase_data in roadmap_result["phases"]:
                weeks = [OnboardingPhaseWeek(**w) for w in phase_data.get("weeks", [])]
                phases_out.append(OnboardingPhase(title=phase_data.get("title", ""), weeks=weeks))

        return OnboardingRoadmapResponse(phases=phases_out)
    except Exception:
        logger.exception("Failed to complete onboarding for user %s", current_user.id)
        raise
