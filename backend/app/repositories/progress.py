from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress import ProgressSnapshot, UserStreak
from app.models.daily_task import DailyTask


class ProgressRepository:
    async def get_or_create_snapshot(self, db: AsyncSession, user_id: str, snapshot_date: date) -> ProgressSnapshot:
        query = select(ProgressSnapshot).filter_by(user_id=user_id, snapshot_date=snapshot_date)
        result = await db.execute(query)
        snapshot = result.scalar_one_or_none()
        if snapshot:
            return snapshot
        snapshot = ProgressSnapshot(user_id=user_id, snapshot_date=snapshot_date)
        db.add(snapshot)
        await db.flush()
        await db.refresh(snapshot)
        return snapshot

    async def update_snapshot(self, db: AsyncSession, user_id: str, snapshot_date: date, **kwargs) -> ProgressSnapshot:
        snapshot = await self.get_or_create_snapshot(db, user_id, snapshot_date)
        for key, value in kwargs.items():
            setattr(snapshot, key, value)
        await db.flush()
        await db.refresh(snapshot)
        return snapshot

    async def get_streak(self, db: AsyncSession, user_id: str) -> UserStreak | None:
        query = select(UserStreak).filter_by(user_id=user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update_streak(self, db: AsyncSession, user_id: str, streak_date: date) -> UserStreak:
        query = select(UserStreak).filter_by(user_id=user_id)
        result = await db.execute(query)
        streak = result.scalar_one_or_none()
        if not streak:
            streak = UserStreak(user_id=user_id, current_streak=1, best_streak=1, last_active_date=streak_date)
            db.add(streak)
            await db.flush()
            await db.refresh(streak)
            return streak

        yesterday = streak_date - timedelta(days=1)
        if streak.last_active_date == yesterday or streak.last_active_date == streak_date:
            if streak.last_active_date != streak_date:
                streak.current_streak += 1
            if streak.current_streak > streak.best_streak:
                streak.best_streak = streak.current_streak
            streak.last_active_date = streak_date
        else:
            streak.current_streak = 1
            streak.last_active_date = streak_date
        await db.flush()
        await db.refresh(streak)
        return streak

    async def get_recent_snapshots(self, db: AsyncSession, user_id: str, days: int = 30) -> list[ProgressSnapshot]:
        cutoff = date.today() - timedelta(days=days)
        query = (
            select(ProgressSnapshot)
            .filter_by(user_id=user_id)
            .where(ProgressSnapshot.snapshot_date >= cutoff)
            .order_by(ProgressSnapshot.snapshot_date)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


progress_repository = ProgressRepository()
