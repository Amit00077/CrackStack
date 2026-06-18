from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_provider import AIProvider

logger = logging.getLogger(__name__)

DEFAULT_PROVIDERS = [
    {
        "name": "groq",
        "display_name": "Groq",
        "api_key": settings.GROQ_API_KEY or "",
        "base_url": settings.GROQ_BASE_URL,
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "active_model": settings.GROQ_MODEL,
    },
    {
        "name": "deepseek",
        "display_name": "DeepSeek",
        "api_key": settings.DEEPSEEK_API_KEY or "",
        "base_url": settings.DEEPSEEK_BASE_URL,
        "models": ["deepseek-v4-flash", "deepseek-chat", "deepseek-reasoner"],
        "active_model": settings.DEEPSEEK_MODEL,
    },
    {
        "name": "openai",
        "display_name": "OpenAI",
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "active_model": "gpt-4o-mini",
    },
    {
        "name": "claude",
        "display_name": "Claude (Anthropic)",
        "api_key": "",
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        "active_model": "claude-3-5-sonnet-20240620",
    },
    {
        "name": "gemini",
        "display_name": "Google Gemini",
        "api_key": "",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": ["gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-pro"],
        "active_model": "gemini-2.0-flash",
    },
]


async def seed_default_providers(db: AsyncSession) -> None:
    for provider_data in DEFAULT_PROVIDERS:
        existing = await db.execute(
            select(AIProvider).where(AIProvider.name == provider_data["name"])
        )
        if existing.scalar_one_or_none():
            continue

        is_first = await db.execute(select(AIProvider).limit(1))
        first = is_first.scalar_one_or_none()
        is_active = first is None and bool(provider_data["api_key"])
        is_enabled = bool(provider_data["api_key"])

        provider = AIProvider(
            name=provider_data["name"],
            display_name=provider_data["display_name"],
            api_key=provider_data["api_key"],
            base_url=provider_data["base_url"],
            models=provider_data["models"],
            active_model=provider_data["active_model"],
            is_active=is_active,
            is_enabled=is_enabled,
        )
        db.add(provider)
        logger.info(
            "Seeded provider '%s' (active=%s, enabled=%s)",
            provider_data["name"], is_active, is_enabled,
        )

    await db.flush()
