from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.progress import progress_service

router = APIRouter(prefix="/progress", tags=["dashboard"])


@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    data = await progress_service.get_dashboard(db, current_user)
    return data


@router.get("/streak")
async def get_streak(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    streak = await progress_service.get_streak(db, current_user)
    if not streak:
        return {"current_streak": 0, "best_streak": 0, "last_active_date": None}
    return {
        "current_streak": streak.current_streak,
        "best_streak": streak.best_streak,
        "last_active_date": streak.last_active_date,
    }
