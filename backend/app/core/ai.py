from __future__ import annotations

import logging

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.ai_provider import ai_provider_repository

logger = logging.getLogger(__name__)


async def get_active_ai_client(
    db: AsyncSession,
) -> tuple[AsyncOpenAI | None, str | None, int | None]:
    try:
        provider = await ai_provider_repository.get_active(db)
        if not provider:
            logger.warning("No active AI provider configured")
            return None, None, None

        client = AsyncOpenAI(
            api_key=provider.api_key,
            base_url=provider.base_url,
        )
        return client, provider.active_model, 4096
    except Exception as exc:
        logger.warning("Failed to get active AI client: %s", exc)
        return None, None, None
