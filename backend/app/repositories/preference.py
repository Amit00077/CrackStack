from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_preference import UserPreference
from app.repositories.base import BaseRepository


class UserPreferenceRepository(BaseRepository[UserPreference]):
    def __init__(self):
        super().__init__(UserPreference)

    async def get_by_user(self, db: AsyncSession, user_id: str) -> UserPreference | None:
        query = select(UserPreference).filter_by(user_id=user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create(self, db: AsyncSession, user_id: str) -> UserPreference:
        existing = await self.get_by_user(db, user_id)
        if existing:
            return existing
        return await self.create(db, user_id=user_id)


user_preference_repository = UserPreferenceRepository()
