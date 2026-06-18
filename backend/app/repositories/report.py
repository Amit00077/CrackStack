from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import WeeklyReport
from app.repositories.base import BaseRepository


class WeeklyReportRepository(BaseRepository[WeeklyReport]):
    def __init__(self):
        super().__init__(WeeklyReport)

    async def get_by_week(self, db: AsyncSession, user_id: str, week_start: date) -> WeeklyReport | None:
        query = select(WeeklyReport).filter_by(user_id=user_id, week_start=week_start)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_current(self, db: AsyncSession, user_id: str) -> WeeklyReport | None:
        query = (
            select(WeeklyReport)
            .filter_by(user_id=user_id)
            .order_by(WeeklyReport.week_start.desc())
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_history(
        self, db: AsyncSession, user_id: str, page: int = 1, limit: int = 10
    ) -> tuple[list[WeeklyReport], int]:
        total_query = select(func.count()).select_from(WeeklyReport).filter_by(user_id=user_id)
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0

        query = (
            select(WeeklyReport)
            .filter_by(user_id=user_id)
            .order_by(WeeklyReport.week_start.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def get_by_week_range(self, db: AsyncSession, user_id: str, start: date, end: date) -> list[WeeklyReport]:
        query = (
            select(WeeklyReport)
            .filter_by(user_id=user_id)
            .where(WeeklyReport.week_start >= start, WeeklyReport.week_end <= end)
            .order_by(WeeklyReport.week_start)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def unset_current(self, db: AsyncSession, user_id: str) -> None:
        query = select(WeeklyReport).filter_by(user_id=user_id, is_current=True)
        result = await db.execute(query)
        for report in result.scalars().all():
            report.is_current = False
        await db.flush()


weekly_report_repository = WeeklyReportRepository()
