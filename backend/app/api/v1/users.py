from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.schemas.user import UserResponse, UserUpdate
from app.services.notification import notification_service
from app.services.user import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    user = await user_service.update_profile(db, current_user, update)
    return UserResponse.model_validate(user)


@router.get("/me/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationPreferenceResponse:
    prefs = await notification_service.get_preferences(db, current_user)
    return NotificationPreferenceResponse.model_validate(prefs)


@router.put("/me/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    update: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationPreferenceResponse:
    prefs = await notification_service.update_preferences(db, current_user, update)
    return NotificationPreferenceResponse.model_validate(prefs)


@router.delete("/me")
async def delete_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await user_service.anonymize_account(db, current_user)
    return {"message": "Account deleted"}


@router.get("/me/export")
async def export_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    data = await user_service.export_user_data(db, current_user)
    return {"data": data}
