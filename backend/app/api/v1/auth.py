from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.redis import blacklist_token, get_redis
from app.core.security import decode_token
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserResponse
from app.services.auth import auth_service
from app.services.roadmap import sync_active_week
from app.services.task import task_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    _, access_token, refresh_token = await auth_service.register(db, request)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user, access_token, refresh_token = await auth_service.login(db, request)
    try:
        goal = await task_service.get_active_goal(db, user.id)
        if goal:
            await sync_active_week(db, user.id, goal.id, date.today())
    except Exception:
        logger.warning("Failed to sync active week during login", exc_info=True)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user, access_token, refresh_token = await auth_service.google_auth(db, request)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    access_token, refresh_token = await auth_service.refresh(db, request.refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    payload = decode_token(request.refresh_token)
    if payload and payload.get("type") == "refresh":
        r = await get_redis()
        await r.setex(f"revoked:refresh:{payload['sub']}:{payload.get('jti', '')}", 86400 * 30, "1")
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await auth_service.forgot_password(db, request.email)
    return {"message": "If email exists, reset link sent"}


@router.post("/reset-password", response_model=TokenResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    access_token, refresh_token = await auth_service.reset_password(db, request.token, request.new_password)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await auth_service.verify_email(db, request.token)
    return {"message": "Email verified"}


@router.post("/resend-verification")
async def resend_verification(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await auth_service.resend_verification(db, request.email)
    return {"message": "Verification email resent"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await auth_service.change_password(db, current_user.id, request.current_password, request.new_password)
    return {"message": "Password changed"}
