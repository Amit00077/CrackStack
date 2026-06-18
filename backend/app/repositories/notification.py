from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self):
        super().__init__(Notification)

    async def get_unread(self, db: AsyncSession, user_id: str) -> list[Notification]:
        query = (
            select(Notification)
            .filter_by(user_id=user_id, is_read=False)
            .order_by(Notification.created_at.desc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_user(self, db: AsyncSession, user_id: str, limit: int = 20) -> list[Notification]:
        query = (
            select(Notification)
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def mark_read(self, db: AsyncSession, notification_id: str, user_id: str) -> Notification | None:
        query = select(Notification).filter_by(id=notification_id, user_id=user_id)
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        if not notification:
            return None
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(notification)
        return notification

    async def mark_all_read(self, db: AsyncSession, user_id: str) -> int:
        result = await db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        await db.flush()
        return result.rowcount

    async def get_unread_count(self, db: AsyncSession, user_id: str) -> int:
        query = select(func.count()).select_from(Notification).filter_by(user_id=user_id, is_read=False)
        result = await db.execute(query)
        return result.scalar() or 0


notification_repository = NotificationRepository()
