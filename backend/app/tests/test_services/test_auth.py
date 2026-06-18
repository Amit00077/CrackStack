from __future__ import annotations

import hashlib
from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models.user import User
from app.repositories.token import token_repository
from app.repositories.user import user_repository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth import auth_service


@pytest.mark.asyncio
async def test_hash_password_and_verify():
    password = "mySecurePass123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


@pytest.mark.asyncio
async def test_hash_password_unique_salts():
    h1 = hash_password("samepass")
    h2 = hash_password("samepass")
    assert h1 != h2


@pytest.mark.asyncio
async def test_create_access_token():
    token = create_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


@pytest.mark.asyncio
async def test_create_refresh_token():
    token = create_token("user-456", expires_delta=timedelta(days=30), token_type="refresh")
    payload = decode_token(token)
    assert payload["sub"] == "user-456"
    assert payload["type"] == "refresh"


@pytest.mark.asyncio
async def test_decode_invalid_token():
    payload = decode_token("invalid.token.data")
    assert payload == {}


@pytest.mark.asyncio
async def test_decode_expired_token():
    token = create_token("user-789", expires_delta=timedelta(days=-1))
    payload = decode_token(token)
    assert payload == {}


@pytest.mark.asyncio
async def test_register_creates_user_and_tokens(db_session: AsyncSession):
    request = RegisterRequest(email="register@test.com", password="strongpassword123", full_name="Test")
    user, access, refresh = await auth_service.register(db_session, request)
    assert user.email == "register@test.com"
    assert user.full_name == "Test"
    assert access is not None
    assert refresh is not None
    access_payload = decode_token(access)
    assert access_payload["sub"] == user.id


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(db_session: AsyncSession):
    request = RegisterRequest(email="dupe@test.com", password="strongpassword123")
    await auth_service.register(db_session, request)
    with pytest.raises(Exception) as exc_info:
        await auth_service.register(db_session, request)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_login_success(db_session: AsyncSession):
    reg = RegisterRequest(email="login@test.com", password="strongpassword123")
    await auth_service.register(db_session, reg)
    login_req = LoginRequest(email="login@test.com", password="strongpassword123")
    user, access, refresh = await auth_service.login(db_session, login_req)
    assert user.email == "login@test.com"
    assert access is not None


@pytest.mark.asyncio
async def test_login_wrong_password_raises(db_session: AsyncSession):
    reg = RegisterRequest(email="wrongpw@test.com", password="strongpassword123")
    await auth_service.register(db_session, reg)
    login_req = LoginRequest(email="wrongpw@test.com", password="wrongpassword")
    with pytest.raises(Exception) as exc_info:
        await auth_service.login(db_session, login_req)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email_raises(db_session: AsyncSession):
    login_req = LoginRequest(email="nobody@test.com", password="strongpassword123")
    with pytest.raises(Exception) as exc_info:
        await auth_service.login(db_session, login_req)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation(db_session: AsyncSession):
    reg = RegisterRequest(email="refresh@test.com", password="strongpassword123")
    _, _, old_refresh = await auth_service.register(db_session, reg)
    new_access, new_refresh = await auth_service.refresh(db_session, old_refresh)
    assert new_access is not None
    assert new_refresh is not None
    from app.models.refresh_token import RefreshToken
    from sqlalchemy import select
    all_tokens = (await db_session.execute(select(RefreshToken))).scalars().all()
    assert len(all_tokens) == 2
    assert any(t.revoked for t in all_tokens)


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_raises(db_session: AsyncSession):
    with pytest.raises(Exception) as exc_info:
        await auth_service.refresh(db_session, "invalidtoken")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(db_session: AsyncSession):
    reg = RegisterRequest(email="logout@test.com", password="strongpassword123")
    _, access, refresh = await auth_service.register(db_session, reg)
    await auth_service.logout(db_session, access, refresh)
    refresh_hash = hashlib.sha256(refresh.encode()).hexdigest()
    from app.models.refresh_token import RefreshToken
    from sqlalchemy import select
    result = await db_session.execute(select(RefreshToken).filter_by(token_hash=refresh_hash))
    stored = result.scalar_one_or_none()
    assert stored is not None
    assert stored.revoked is True


@pytest.mark.asyncio
async def test_forgot_password_silent_for_nonexistent(db_session: AsyncSession):
    await auth_service.forgot_password(db_session, "nobody@test.com")


@pytest.mark.asyncio
async def test_forgot_password_creates_token(db_session: AsyncSession):
    user = await user_repository.create(db_session, email="forgot@test.com", hashed_password=hash_password("pass123"))
    await auth_service.forgot_password(db_session, "forgot@test.com")
    from app.models.password_reset import PasswordResetToken
    from sqlalchemy import select
    result = await db_session.execute(select(PasswordResetToken).filter_by(user_id=user.id))
    token = result.scalar_one_or_none()
    assert token is not None
    assert token.used is False


@pytest.mark.asyncio
async def test_change_password_success(db_session: AsyncSession):
    user = await user_repository.create(
        db_session, email="changepw@test.com", hashed_password=hash_password("oldpass123")
    )
    await auth_service.change_password(db_session, user.id, "oldpass123", "newpass456")
    assert verify_password("newpass456", user.hashed_password)


@pytest.mark.asyncio
async def test_change_password_wrong_current_raises(db_session: AsyncSession):
    user = await user_repository.create(
        db_session, email="changepw2@test.com", hashed_password=hash_password("oldpass123")
    )
    with pytest.raises(Exception) as exc_info:
        await auth_service.change_password(db_session, user.id, "wrongpass", "newpass456")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_current_user(db_session: AsyncSession):
    user = await user_repository.create(db_session, email="current@test.com", hashed_password=hash_password("pass123"))
    result = await auth_service.get_current_user(db_session, user.id)
    assert result is not None
    assert result.id == user.id


@pytest.mark.asyncio
async def test_get_current_user_not_found(db_session: AsyncSession):
    result = await auth_service.get_current_user(db_session, "nonexistent-id")
    assert result is None
