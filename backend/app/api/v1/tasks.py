from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.daily import DayGrid, TodayTasksResponse, WeeklyGridResponse
from app.schemas.task import DailyTaskCreate, DailyTaskResponse, DailyTaskUpdate
from app.services.daily_task import daily_task_service
from app.services.roadmap import get_weeks_for_goal, sync_active_week
from app.services.task import task_service
from app.repositories.task import daily_task_repository
from app.repositories.roadmap import roadmap_task_repository
from app.utils.timezone import get_current_week_start, get_today_in_timezone, get_user_timezone

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/assign", response_model=list[DailyTaskResponse])
async def assign_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DailyTaskResponse]:
    tasks = await task_service.assign_weekly_tasks(db, current_user.id)
    return [DailyTaskResponse.model_validate(t) for t in tasks]


@router.post("/generate-week/{week_id}", response_model=list[DailyTaskResponse])
async def generate_week_tasks(
    week_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DailyTaskResponse]:
    tasks = await task_service.generate_daily_tasks_for_week(db, current_user.id, week_id=week_id)
    return [DailyTaskResponse.model_validate(t) for t in tasks]


@router.get("/today", response_model=TodayTasksResponse)
async def get_today_tasks(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TodayTasksResponse:
    tz = get_user_timezone(request)
    today = get_today_in_timezone(tz)

    goal = await task_service.get_active_goal(db, current_user.id)
    current_week_info = None

    if goal:
        await sync_active_week(db, current_user.id, goal.id, today)
        weeks = await get_weeks_for_goal(db, goal.id, current_user.id)
        active_week = next((w for w in weeks if w.status == "active"), None)
        if active_week:
            current_week_info = {
                "week_number": active_week.week_number,
                "title": active_week.title,
                "theme": active_week.description or "",
            }
            if active_week.start_date:
                await task_service.generate_daily_tasks_for_week(db, current_user.id, week_id=active_week.id)

    tasks = await daily_task_service.get_today(db, current_user, task_date=today)
    total_count = len(tasks)
    done_count = sum(1 for t in tasks if t.is_done)
    completion_pct = (done_count / total_count * 100) if total_count > 0 else 0

    return TodayTasksResponse(
        tasks=[DailyTaskResponse.model_validate(t) for t in tasks],
        completion_pct=completion_pct,
        done_count=done_count,
        total_count=total_count,
        message="Rest day! No tasks scheduled." if total_count == 0 else None,
        current_week=current_week_info,
    )


@router.get("/weekly-grid", response_model=WeeklyGridResponse)
async def get_weekly_grid(
    request: Request,
    week_start: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WeeklyGridResponse:
    tz = get_user_timezone(request)
    today = get_today_in_timezone(tz)

    if week_start is None:
        week_start = get_current_week_start(today, tz)

    goal = await task_service.get_active_goal(db, current_user.id)
    active_week = None
    if goal:
        await sync_active_week(db, current_user.id, goal.id, today)
        weeks = await get_weeks_for_goal(db, goal.id, current_user.id)
        active_week = next((w for w in weeks if w.status == "active"), None)

    if active_week and active_week.start_date:
        week_end = active_week.start_date + timedelta(days=6)
        existing = await daily_task_repository.get_by_date_range(db, current_user.id, active_week.start_date, week_end)
        weekly_task_count = await roadmap_task_repository.count_by_week(db, active_week.id)
        if len(existing) < weekly_task_count:
            await task_service.generate_daily_tasks_for_week(db, current_user.id, week_id=active_week.id)

    days: list[DayGrid] = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        day_tasks = await daily_task_service.get_today(db, current_user, task_date=d)
        days.append(
            DayGrid(
                date=d.isoformat(),
                day_name=d.strftime("%A"),
                is_today=(d == today),
                tasks=[DailyTaskResponse.model_validate(t) for t in day_tasks],
            )
        )

    return WeeklyGridResponse(
        week_start=week_start.isoformat(),
        days=days,
    )


@router.get("", response_model=list[DailyTaskResponse])
async def get_tasks(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DailyTaskResponse]:
    tasks = await daily_task_service.get_by_date_range(db, current_user, start_date, end_date)
    return [DailyTaskResponse.model_validate(t) for t in tasks]


@router.post("", response_model=DailyTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: DailyTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyTaskResponse:
    task = await daily_task_service.create(db, current_user, request)
    return DailyTaskResponse.model_validate(task)


@router.patch("/{task_id}/toggle", response_model=DailyTaskResponse)
async def toggle_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyTaskResponse:
    task = await daily_task_service.toggle(db, current_user, task_id)
    return DailyTaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=DailyTaskResponse)
async def update_task(
    task_id: str,
    request: DailyTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyTaskResponse:
    task = await daily_task_service.update(db, current_user, task_id, request)
    return DailyTaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await daily_task_service.delete(db, current_user, task_id)
