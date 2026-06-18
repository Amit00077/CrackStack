from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.notification import notification_repository
from app.repositories.progress import progress_repository
from app.repositories.task import daily_task_repository
from app.repositories.user import user_repository


class NotificationService:
    async def create_notification(
        self, db: AsyncSession, user_id: str, type: str, title: str, message: str, channel: str = "in_app"
    ) -> Notification:
        return await notification_repository.create(
            db, user_id=user_id, type=type, title=title, message=message, channel=channel,
        )

    async def get_notifications(self, db: AsyncSession, user_id: str, limit: int = 20) -> list[Notification]:
        return await notification_repository.get_by_user(db, user_id, limit=limit)

    async def mark_notification_read(self, db: AsyncSession, notification_id: str, user_id: str) -> Notification:
        notification = await notification_repository.mark_read(db, notification_id, user_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "NOTIFICATION_NOT_FOUND", "details": "Notification not found"},
            )
        return notification

    async def mark_all_read_for_user(self, db: AsyncSession, user_id: str) -> int:
        return await notification_repository.mark_all_read(db, user_id)

    async def get_unread_count_by_user(self, db: AsyncSession, user_id: str) -> int:
        return await notification_repository.get_unread_count(db, user_id)

    async def send_daily_reminder(self, db: AsyncSession, user_id: str) -> Notification | None:
        user = await user_repository.get(db, id=user_id)
        if not user:
            return None
        today = date.today()
        total = await daily_task_repository.count_total_today(db, user_id, today)
        if total == 0:
            return None
        completed = await daily_task_repository.count_completed_today(db, user_id, today)
        pending = total - completed
        if pending == 0:
            return None
        return await self.create_notification(
            db, user_id, "daily_reminder", "Tasks Pending",
            f"You have {pending} task(s) remaining for today.",
        )

    async def send_streak_warning(self, db: AsyncSession, user_id: str) -> Notification | None:
        streak = await progress_repository.get_streak(db, user_id)
        if not streak or not streak.last_active_date:
            return None
        if streak.last_active_date < date.today() - timedelta(days=1):
            return await self.create_notification(
                db, user_id, "streak_warning", "Streak at Risk",
                "Complete your tasks today to keep your streak alive!",
            )
        return None

    async def send_report_ready(self, db: AsyncSession, user_id: str, report_id: str) -> Notification:
        return await self.create_notification(
            db, user_id, "report_ready", "Weekly Report Ready",
            "Your weekly report has been generated. Check it out!",
        )


    async def get_all(self, db: AsyncSession, user, limit: int = 20) -> list[Notification]:
        uid = user.id if hasattr(user, "id") else user
        return await self.get_notifications(db, uid, limit=limit)

    async def get_unread_count(self, db: AsyncSession, user) -> int:
        uid = user.id if hasattr(user, "id") else user
        return await self.get_unread_count_by_user(db, uid)

    async def mark_read(self, db: AsyncSession, user, notification_id: str) -> Notification:
        uid = user.id if hasattr(user, "id") else user
        return await self.mark_notification_read(db, notification_id, uid)

    async def mark_all_read(self, db: AsyncSession, user) -> int:
        uid = user.id if hasattr(user, "id") else user
        return await self.mark_all_read_for_user(db, uid)

    async def get_preferences(self, db: AsyncSession, user):
        uid = user.id if hasattr(user, "id") else user
        from app.repositories.preference import user_preference_repository
        prefs = await user_preference_repository.get_or_create(db, uid)
        return prefs

    async def update_preferences(self, db: AsyncSession, user, update):
        uid = user.id if hasattr(user, "id") else user
        from app.repositories.preference import user_preference_repository
        prefs = await user_preference_repository.get_or_create(db, uid)
        data = update.model_dump(exclude_unset=True) if hasattr(update, "model_dump") else dict(update)
        for key, value in data.items():
            setattr(prefs, key, value)
        await db.flush()
        await db.refresh(prefs)
        return prefs


notification_service = NotificationService()
