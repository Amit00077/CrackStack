from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "id" in data


@pytest.mark.asyncio
async def test_get_me_without_auth(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, auth_headers: dict):
    response = await client.patch(
        "/api/v1/users/me",
        json={"full_name": "Updated Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_profile_without_auth(client: AsyncClient):
    response = await client.patch("/api/v1/users/me", json={"full_name": "X"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_preferences(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/users/me/preferences", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "email_notifications" in data
    assert "push_notifications" in data


@pytest.mark.asyncio
async def test_get_preferences_without_auth(client: AsyncClient):
    response = await client.get("/api/v1/users/me/preferences")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_preferences(client: AsyncClient, auth_headers: dict):
    response = await client.put(
        "/api/v1/users/me/preferences",
        json={"email_notifications": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email_notifications"] is False


@pytest.mark.asyncio
async def test_update_preferences_without_auth(client: AsyncClient):
    response = await client.put("/api/v1/users/me/preferences", json={"email_notifications": False})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_account(client: AsyncClient, auth_headers: dict):
    response = await client.delete("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_delete_account_without_auth(client: AsyncClient):
    response = await client.delete("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_shows_correct_email(client: AsyncClient):
    reg = {"email": "userme@example.com", "password": "strongpassword123"}
    reg_resp = await client.post("/api/v1/auth/register", json=reg)
    token = reg_resp.json()["access_token"]
    response = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.json()["email"] == "userme@example.com"
