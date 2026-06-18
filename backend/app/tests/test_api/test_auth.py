from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    payload = {
        "email": "newuser@example.com",
        "password": "strongpassword123",
        "full_name": "New User",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dupe@example.com",
        "password": "strongpassword123",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "EMAIL_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_register_validation_errors(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={"email": "invalid", "password": "short"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_fields(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    reg = {"email": "login@example.com", "password": "strongpassword123"}
    await client.post("/api/v1/auth/register", json=reg)
    response = await client.post("/api/v1/auth/login", json=reg)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    reg = {"email": "wrongpw@example.com", "password": "strongpassword123"}
    await client.post("/api/v1/auth/register", json=reg)
    response = await client.post("/api/v1/auth/login", json={"email": "wrongpw@example.com", "password": "wrongpassword"})
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "strongpassword123"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient):
    reg = {"email": "refresh@example.com", "password": "strongpassword123"}
    reg_resp = await client.post("/api/v1/auth/register", json=reg)
    refresh_token = reg_resp.json()["refresh_token"]
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "invalidtokendata"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient):
    reg = {"email": "logout@example.com", "password": "strongpassword123"}
    reg_resp = await client.post("/api/v1/auth/register", json=reg)
    token = reg_resp.json()["access_token"]
    refresh = reg_resp.json()["refresh_token"]
    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


@pytest.mark.asyncio
async def test_logout_without_auth(client: AsyncClient):
    response = await client.post("/api/v1/auth/logout", json={"refresh_token": "sometoken"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_forgot_password_existing_email(client: AsyncClient):
    reg = {"email": "forgot@example.com", "password": "strongpassword123"}
    await client.post("/api/v1/auth/register", json=reg)
    response = await client.post("/api/v1/auth/forgot-password", json={"email": "forgot@example.com"})
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email_silent(client: AsyncClient):
    response = await client.post("/api/v1/auth/forgot-password", json={"email": "doesnotexist@example.com"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    response = await client.post("/api/v1/auth/reset-password", json={"token": "invalidtoken", "new_password": "newstrongpass123"})
    assert response.status_code in (400, 401, 500)


@pytest.mark.asyncio
async def test_verify_email_invalid_token(client: AsyncClient):
    response = await client.post("/api/v1/auth/verify-email", json={"token": "invalidtoken"})
    assert response.status_code in (400, 500)


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient):
    reg = {"email": "changepw@example.com", "password": "strongpassword123"}
    reg_resp = await client.post("/api/v1/auth/register", json=reg)
    token = reg_resp.json()["access_token"]
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "strongpassword123", "new_password": "newstrongpass456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient):
    reg = {"email": "changepw2@example.com", "password": "strongpassword123"}
    reg_resp = await client.post("/api/v1/auth/register", json=reg)
    token = reg_resp.json()["access_token"]
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "wrongpassword", "new_password": "newstrongpass456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (400, 401)


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient):
    reg = {"email": "me@example.com", "password": "strongpassword123"}
    reg_resp = await client.post("/api/v1/auth/register", json=reg)
    token = reg_resp.json()["access_token"]
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
