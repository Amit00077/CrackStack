from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.email_verification import EmailVerificationToken
from app.models.password_reset import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.repositories.user import user_repository


class TokenRepository:
    async def create_verification_token(self, db: AsyncSession, user_id: str) -> EmailVerificationToken:
        raw_token = secrets.token_urlsafe(48)
        hashed = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
        token = EmailVerificationToken(
            user_id=user_id,
            token=hashed,
            expires_at=expires_at,
        )
        db.add(token)
        await db.flush()
        await db.refresh(token)
        token._raw = raw_token
        return token

    async def verify_token(self, db: AsyncSession, token_str: str) -> bool:
        hashed = hashlib.sha256(token_str.encode()).hexdigest()
        query = select(EmailVerificationToken).filter_by(token=hashed, used=False)
        result = await db.execute(query)
        token = result.scalar_one_or_none()
        if not token:
            return False
        if token.expires_at < datetime.now(timezone.utc):
            return False
        token.used = True
        await db.flush()
        return True

    async def create_password_reset_token(self, db: AsyncSession, user_id: str) -> PasswordResetToken:
        raw_token = secrets.token_urlsafe(48)
        hashed = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        token = PasswordResetToken(
            user_id=user_id,
            token=hashed,
            expires_at=expires_at,
        )
        db.add(token)
        await db.flush()
        await db.refresh(token)
        token._raw = raw_token
        return token

    async def reset_password(self, db: AsyncSession, token_str: str, new_password: str) -> bool:
        hashed = hashlib.sha256(token_str.encode()).hexdigest()
        query = select(PasswordResetToken).filter_by(token=hashed, used=False)
        result = await db.execute(query)
        token = result.scalar_one_or_none()
        if not token:
            return False
        if token.expires_at < datetime.now(timezone.utc):
            return False
        user = await user_repository.get(db, id=token.user_id)
        if not user:
            return False
        token.used = True
        user.hashed_password = hash_password(new_password)
        await db.flush()
        return True

    async def store_refresh_token(self, db: AsyncSession, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(token)
        await db.flush()
        await db.refresh(token)
        return token

    async def revoke_refresh_token(self, db: AsyncSession, token_hash: str) -> bool:
        query = select(RefreshToken).filter_by(token_hash=token_hash, revoked=False)
        result = await db.execute(query)
        token = result.scalar_one_or_none()
        if not token:
            return False
        token.revoked = True
        await db.flush()
        return True

    async def revoke_all_user_tokens(self, db: AsyncSession, user_id: str) -> int:
        result = await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
            .values(revoked=True)
        )
        await db.flush()
        return result.rowcount


token_repository = TokenRepository()
