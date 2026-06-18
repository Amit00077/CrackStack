from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal
from app.repositories.base import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    def __init__(self):
        super().__init__(Goal)

    async def get_active_by_user(self, db: AsyncSession, user_id: str) -> Goal | None:
        query = select(Goal).filter_by(user_id=user_id, is_active=True)
        result = await db.execute(query)
        return result.scalar_one_or_none()


goal_repository = GoalRepository()
