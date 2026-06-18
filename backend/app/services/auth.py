from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import blacklist_token, is_token_blacklisted
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models.user import User
from app.repositories.token import token_repository
from app.repositories.user import user_repository
from app.schemas.auth import LoginRequest, RegisterRequest

logger = logging.getLogger(__name__)


class AuthService:
    async def register(self, db: AsyncSession, request: RegisterRequest) -> tuple[User, str, str]:
        existing = await user_repository.get(db, email=request.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Conflict",
                    "code": "EMAIL_ALREADY_EXISTS",
                    "details": "A user with this email already exists",
                },
            )
        user = await user_repository.create(
            db,
            email=request.email,
            hashed_password=hash_password(request.password),
            full_name=request.full_name,
        )
        ver_token = await token_repository.create_verification_token(db, user.id)
        logger.info("Created verification token for user %s", user.id)
        access = self._issue_access(user.id)
        refresh = await self._issue_refresh(db, user.id)
        return user, access, refresh

    async def login(self, db: AsyncSession, request: LoginRequest) -> tuple[User, str, str]:
        user = await user_repository.get(db, email=request.email)
        if not user or not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Unauthorized",
                    "code": "INVALID_CREDENTIALS",
                    "details": "Invalid email or password",
                },
            )
        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Unauthorized",
                    "code": "INVALID_CREDENTIALS",
                    "details": "Invalid email or password",
                },
            )
        access = self._issue_access(user.id)
        refresh = await self._issue_refresh(db, user.id)
        return user, access, refresh

    async def refresh(self, db: AsyncSession, refresh_token: str) -> tuple[str, str]:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Unauthorized",
                    "code": "INVALID_REFRESH_TOKEN",
                    "details": "Refresh token is invalid or expired",
                },
            )
        user_id = payload["sub"]
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await token_repository.revoke_refresh_token(db, token_hash)
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Unauthorized",
                    "code": "USER_NOT_FOUND",
                    "details": "User associated with token not found",
                },
            )
        new_access = self._issue_access(user_id)
        new_refresh = await self._issue_refresh(db, user_id)
        return new_access, new_refresh

    async def logout(self, db: AsyncSession, access_token: str, refresh_token: str) -> None:
        payload = decode_token(access_token)
        exp = payload.get("exp", 0)
        ttl = max(exp - datetime.now(timezone.utc).timestamp(), 0)
        if ttl > 0:
            await blacklist_token(access_token, int(ttl))
        refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await token_repository.revoke_refresh_token(db, refresh_hash)

    async def forgot_password(self, db: AsyncSession, email: str) -> None:
        user = await user_repository.get(db, email=email)
        if not user:
            logger.info("Password reset requested for non-existent email: %s", email)
            return
        token = await token_repository.create_password_reset_token(db, user.id)
        logger.info("Password reset token created for user %s: %s", user.id, token._raw)

    async def reset_password(self, db: AsyncSession, token_str: str, new_password: str) -> None:
        success = await token_repository.reset_password(db, token_str, new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Bad Request",
                    "code": "INVALID_RESET_TOKEN",
                    "details": "Reset token is invalid or expired",
                },
            )

    async def verify_email(self, db: AsyncSession, token_str: str) -> None:
        valid = await token_repository.verify_token(db, token_str)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Bad Request",
                    "code": "INVALID_VERIFICATION_TOKEN",
                    "details": "Verification token is invalid or expired",
                },
            )

    async def resend_verification(self, db: AsyncSession, user_id: str) -> str:
        token = await token_repository.create_verification_token(db, user_id)
        logger.info("New verification token created for user %s", user_id)
        return token._raw

    async def google_auth(self, db: AsyncSession, id_token_str: str) -> tuple[User, str, str]:
        try:
            from google.auth.transport import requests
            from google.oauth2 import id_token
            info = id_token.verify_oauth2_token(id_token_str, requests.Request(), settings.GOOGLE_CLIENT_ID)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Unauthorized",
                    "code": "INVALID_GOOGLE_TOKEN",
                    "details": "Google authentication failed",
                },
            )
        google_id = info["sub"]
        email = info.get("email", "")
        name = info.get("name", "")
        picture = info.get("picture", "")
        user = await user_repository.get(db, auth_provider="google", auth_provider_id=google_id)
        if not user:
            existing_email = await user_repository.get(db, email=email)
            if existing_email:
                existing_email.auth_provider = "google"
                existing_email.auth_provider_id = google_id
                existing_email.is_verified = True
                existing_email.avatar_url = existing_email.avatar_url or picture
                user = existing_email
            else:
                user = await user_repository.create(
                    db,
                    email=email,
                    full_name=name,
                    avatar_url=picture,
                    is_verified=True,
                    auth_provider="google",
                    auth_provider_id=google_id,
                )
            await db.flush()
            await db.refresh(user)
        access = self._issue_access(user.id)
        refresh = await self._issue_refresh(db, user.id)
        return user, access, refresh

    async def change_password(self, db: AsyncSession, user_id: str, current_password: str, new_password: str) -> None:
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not Found",
                    "code": "USER_NOT_FOUND",
                    "details": "User not found",
                },
            )
        if not user.hashed_password or not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Bad Request",
                    "code": "INVALID_PASSWORD",
                    "details": "Current password is incorrect",
                },
            )
        user.hashed_password = hash_password(new_password)
        await db.flush()

    async def get_current_user(self, db: AsyncSession, user_id: str) -> User | None:
        return await user_repository.get(db, id=user_id)

    def _issue_access(self, user_id: str) -> str:
        return create_token(
            user_id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

    async def _issue_refresh(self, db: AsyncSession, user_id: str) -> str:
        raw = create_token(
            user_id,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            token_type="refresh",
        )
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await token_repository.store_refresh_token(db, user_id, token_hash, expires_at)
        return raw


auth_service = AuthService()
