from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    async def get(self, db: AsyncSession, **filters) -> Optional[User]:
        query = select(User).filter_by(**filters)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[User]:
        query = select(User).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, **kwargs) -> User:
        user = User(**kwargs)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def update(self, db: AsyncSession, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            setattr(user, key, value)
        await db.flush()
        await db.refresh(user)
        return user

    async def delete(self, db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.flush()

    async def count(self, db: AsyncSession) -> int:
        from sqlalchemy.func import count

        query = select(count(User.id))
        result = await db.execute(query)
        return result.scalar() or 0


user_repository = UserRepository()
