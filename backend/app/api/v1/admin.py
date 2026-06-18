from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_superuser
from app.core.database import get_db
from app.models.user import User
from app.schemas.admin import PaginatedAuditLogs
from app.schemas.ai_provider import (
    AIProviderCreate,
    AIProviderListResponse,
    AIProviderResponse,
    AIProviderUpdate,
    SetActiveProviderRequest,
)
from app.services.admin import admin_service
from app.services.ai_provider import ai_provider_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit-logs", response_model=PaginatedAuditLogs)
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> PaginatedAuditLogs:
    result = await admin_service.get_audit_logs(db, current_user, skip=skip, limit=limit, user_id=user_id)
    return PaginatedAuditLogs(
        items=result["items"],
        total=result["total"],
        page=(skip // limit) + 1,
        page_size=limit,
        total_pages=-(-result["total"] // limit),
    )


@router.get("/providers", response_model=AIProviderListResponse)
async def list_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> AIProviderListResponse:
    providers = await ai_provider_service.get_all_providers(db)
    items = [_mask_provider(p) for p in providers]
    return AIProviderListResponse(items=items)


@router.post("/providers", response_model=AIProviderResponse, status_code=201)
async def create_provider(
    body: AIProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> AIProviderResponse:
    provider = await ai_provider_service.create_provider(db, body.model_dump())
    return _mask_provider(provider)


@router.get("/providers/{provider_id}", response_model=AIProviderResponse)
async def get_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> AIProviderResponse:
    provider = await ai_provider_service.get_provider(db, provider_id)
    return _mask_provider(provider)


@router.put("/providers/{provider_id}", response_model=AIProviderResponse)
async def update_provider(
    provider_id: str,
    body: AIProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> AIProviderResponse:
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    provider = await ai_provider_service.update_provider(db, provider_id, data)
    return _mask_provider(provider)


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> None:
    await ai_provider_service.delete_provider(db, provider_id)


@router.post("/providers/active", response_model=AIProviderResponse)
async def set_active_provider(
    body: SetActiveProviderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> AIProviderResponse:
    provider = await ai_provider_service.set_active_provider(
        db, body.provider_id, active_model=body.active_model
    )
    return _mask_provider(provider)


@router.get("/providers/active/current", response_model=AIProviderResponse | None)
async def get_active_provider(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser),
) -> AIProviderResponse | None:
    provider = await ai_provider_service.get_active_provider(db)
    if not provider:
        return None
    return _mask_provider(provider)


def _mask_provider(provider) -> AIProviderResponse:
    key = provider.api_key
    if len(key) > 8:
        preview = key[:4] + "*" * (len(key) - 8) + key[-4:]
    elif len(key) > 4:
        preview = key[:2] + "*" * (len(key) - 4) + key[-2:]
    else:
        preview = "****"
    return AIProviderResponse(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        api_key_preview=preview,
        base_url=provider.base_url,
        models=provider.models,
        active_model=provider.active_model,
        is_active=provider.is_active,
        is_enabled=provider.is_enabled,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )
