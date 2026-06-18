from __future__ import annotations

import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import joinedload

from app.core.database import async_session_factory
from app.models.goal import Goal
from app.models.roadmap import RoadmapWeek
from app.services.roadmap import sync_active_week
from app.services.task import task_service

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def daily_task_sync_job() -> None:
    logger.info("Running daily task sync job")
    today = date.today()
    try:
        async with async_session_factory() as db:
            result = await db.execute(select(Goal).where(Goal.is_active == True))
            goals = list(result.scalars().all())
            for goal in goals:
                try:
                    await sync_active_week(db, goal.user_id, goal.id, today)
                except Exception as exc:
                    logger.error("Failed to sync week for user %s goal %s: %s", goal.user_id, goal.id, exc)

            for goal in goals:
                try:
                    active_week = await _get_active_week(db, goal.user_id, goal.id)
                    if active_week:
                        await task_service.generate_daily_tasks_for_week(
                            db, goal.user_id, week_id=active_week.id
                        )
                except Exception as exc:
                    logger.error("Failed to generate daily tasks for user %s goal %s: %s", goal.user_id, goal.id, exc)

            await db.commit()
        logger.info("Daily task sync completed for %d active goals", len(goals))
    except Exception as exc:
        logger.error("Daily task sync job failed: %s", exc)


async def _get_active_week(db, user_id: str, goal_id: str) -> RoadmapWeek | None:
    query = (
        select(RoadmapWeek)
        .options(joinedload(RoadmapWeek.tasks))
        .join(Roadmap, Roadmap.id == RoadmapWeek.roadmap_id)
        .where(
            Roadmap.user_id == user_id,
            Roadmap.goal_id == goal_id,
            Roadmap.is_active == True,
            RoadmapWeek.status == "active",
        )
        .limit(1)
    )
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


def setup_scheduler() -> None:
    scheduler.add_job(
        daily_task_sync_job,
        "cron",
        hour=0,
        minute=1,
        id="daily_task_sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with daily task sync job at 00:01")
