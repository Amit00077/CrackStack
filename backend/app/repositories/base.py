from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model: type[T]):
        self.model = model

    async def get(self, db: AsyncSession, **filters) -> T | None:
        query = select(self.model).filter_by(**filters)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100, **filters) -> list[T]:
        query = select(self.model).filter_by(**filters).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, **kwargs) -> T:
        obj = self.model(**kwargs)
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def update(self, db: AsyncSession, obj: T, **kwargs) -> T:
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def delete(self, db: AsyncSession, obj: T) -> None:
        await db.delete(obj)
        await db.flush()

    async def count(self, db: AsyncSession, **filters) -> int:
        query = select(func.count()).select_from(self.model).filter_by(**filters)
        result = await db.execute(query)
        return result.scalar() or 0
