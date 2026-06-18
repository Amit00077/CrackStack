from __future__ import annotations

import logging

from fastapi import HTTPException, status
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_provider import AIProvider
from app.repositories.ai_provider import ai_provider_repository

logger = logging.getLogger(__name__)


class AIProviderService:
    async def get_all_providers(self, db: AsyncSession) -> list[AIProvider]:
        return await ai_provider_repository.get_multi(db)

    async def get_provider(self, db: AsyncSession, provider_id: str) -> AIProvider:
        provider = await ai_provider_repository.get(db, id=provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "PROVIDER_NOT_FOUND", "details": "AI provider not found"},
            )
        return provider

    async def create_provider(self, db: AsyncSession, data: dict) -> AIProvider:
        existing = await ai_provider_repository.get_by_name(db, data["name"])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Conflict", "code": "PROVIDER_EXISTS", "details": f"Provider '{data['name']}' already exists"},
            )
        provider = await ai_provider_repository.create(db, **data)
        return provider

    async def update_provider(
        self, db: AsyncSession, provider_id: str, data: dict
    ) -> AIProvider:
        provider = await self.get_provider(db, provider_id)
        provider = await ai_provider_repository.update(db, provider, **data)
        return provider

    async def delete_provider(self, db: AsyncSession, provider_id: str) -> None:
        provider = await self.get_provider(db, provider_id)
        await ai_provider_repository.delete(db, provider)

    async def set_active_provider(
        self, db: AsyncSession, provider_id: str, active_model: str | None = None
    ) -> AIProvider:
        provider = await self.get_provider(db, provider_id)
        if not provider.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "code": "PROVIDER_DISABLED", "details": "Cannot activate a disabled provider"},
            )
        if active_model and active_model not in provider.models:
            if provider.models:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "Bad Request", "code": "INVALID_MODEL", "details": f"Model '{active_model}' is not in the allowed models list"},
                )
            provider = await ai_provider_repository.update(db, provider, active_model=active_model)
        result = await ai_provider_repository.set_active(db, provider_id)
        return result

    async def get_active_provider(self, db: AsyncSession) -> AIProvider | None:
        return await ai_provider_repository.get_active(db)

    @staticmethod
    def build_openai_client(provider: AIProvider) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=provider.api_key,
            base_url=provider.base_url,
        )

    async def get_active_client(
        self, db: AsyncSession
    ) -> tuple[AsyncOpenAI, str, int] | tuple[None, None, None]:
        provider = await self.get_active_provider(db)
        if not provider:
            return None, None, None
        client = self.build_openai_client(provider)
        return client, provider.active_model, 4096


ai_provider_service = AIProviderService()
