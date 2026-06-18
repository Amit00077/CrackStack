from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_provider import AIProvider
from app.repositories.base import BaseRepository


class AIProviderRepository(BaseRepository[AIProvider]):
    async def get_by_name(self, db: AsyncSession, name: str) -> AIProvider | None:
        return await self.get(db, name=name)

    async def get_active(self, db: AsyncSession) -> AIProvider | None:
        return await self.get(db, is_active=True)

    async def set_active(self, db: AsyncSession, provider_id: str) -> AIProvider | None:
        await db.execute(
            update(AIProvider).where(AIProvider.is_active == True).values(is_active=False)
        )
        await db.execute(
            update(AIProvider).where(AIProvider.id == provider_id).values(is_active=True)
        )
        await db.flush()
        return await self.get(db, id=provider_id)

    async def get_enabled(self, db: AsyncSession) -> list[AIProvider]:
        query = select(AIProvider).where(AIProvider.is_enabled == True)
        result = await db.execute(query)
        return list(result.scalars().all())


ai_provider_repository = AIProviderRepository(AIProvider)
