from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_task import DailyTask
from app.repositories.base import BaseRepository


class DailyTaskRepository(BaseRepository[DailyTask]):
    def __init__(self):
        super().__init__(DailyTask)

    async def get_today(self, db: AsyncSession, user_id: str, task_date: date) -> list[DailyTask]:
        query = (
            select(DailyTask)
            .filter_by(user_id=user_id, task_date=task_date)
            .order_by(DailyTask.sort_order)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self, db: AsyncSession, user_id: str, start_date: date, end_date: date
    ) -> list[DailyTask]:
        query = (
            select(DailyTask)
            .filter_by(user_id=user_id)
            .where(and_(DailyTask.task_date >= start_date, DailyTask.task_date <= end_date))
            .order_by(DailyTask.task_date, DailyTask.sort_order)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_upcoming(self, db: AsyncSession, user_id: str, limit: int = 7) -> list[DailyTask]:
        today = date.today()
        query = (
            select(DailyTask)
            .filter_by(user_id=user_id)
            .where(DailyTask.task_date >= today, DailyTask.is_done == False)
            .order_by(DailyTask.task_date, DailyTask.sort_order)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def toggle(self, db: AsyncSession, task_id: str, user_id: str) -> DailyTask | None:
        query = select(DailyTask).filter_by(id=task_id, user_id=user_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        if not task:
            return None
        task.is_done = not task.is_done
        task.completed_at = datetime.now(timezone.utc) if task.is_done else None
        await db.flush()
        await db.refresh(task)
        return task

    async def count_completed_today(self, db: AsyncSession, user_id: str, task_date: date) -> int:
        query = select(func.count()).select_from(DailyTask).filter_by(
            user_id=user_id, task_date=task_date, is_done=True
        )
        result = await db.execute(query)
        return result.scalar() or 0

    async def count_total_today(self, db: AsyncSession, user_id: str, task_date: date) -> int:
        query = select(func.count()).select_from(DailyTask).filter_by(
            user_id=user_id, task_date=task_date
        )
        result = await db.execute(query)
        return result.scalar() or 0

    async def get_total_study_time(self, db: AsyncSession, user_id: str, task_date: date) -> int:
        query = select(func.coalesce(func.sum(DailyTask.time_estimate), 0)).filter_by(
            user_id=user_id, task_date=task_date
        )
        result = await db.execute(query)
        return result.scalar() or 0

    async def delete_by_week_and_source(
        self, db: AsyncSession, user_id: str, week_id: str, source: str
    ) -> None:
        query = select(DailyTask).filter_by(
            user_id=user_id, week_id=week_id, source=source
        )
        result = await db.execute(query)
        tasks = list(result.scalars().all())
        for t in tasks:
            await db.delete(t)
        if tasks:
            await db.flush()

    async def get_category_stats(
        self, db: AsyncSession, user_id: str, since: date, until: date
    ) -> list[dict]:
        all_tasks = await self.get_by_date_range(db, user_id, since, until)
        by_cat: dict[str, dict] = {}
        for t in all_tasks:
            cat = t.category or "study"
            if cat not in by_cat:
                by_cat[cat] = {"category": cat, "total": 0, "completed": 0}
            by_cat[cat]["total"] += 1
            if t.is_done:
                by_cat[cat]["completed"] += 1
        return sorted(by_cat.values(), key=lambda x: x["category"])


daily_task_repository = DailyTaskRepository()
