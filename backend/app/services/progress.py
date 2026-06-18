from __future__ import annotations

from app.models.user import User
from app.services.dashboard import dashboard_service as ds


class ProgressService:
    async def get_dashboard(self, db, user: User) -> dict:
        return await ds.get_dashboard(db, user.id)

    async def get_streak(self, db, user: User):
        from app.repositories.progress import progress_repository
        return await progress_repository.get_streak(db, user.id)


progress_service = ProgressService()
