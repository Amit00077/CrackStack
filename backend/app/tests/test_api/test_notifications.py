from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_notifications(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_notifications_without_auth(client: AsyncClient):
    response = await client.get("/api/v1/notifications")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unread_count(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert isinstance(data["count"], int)


@pytest.mark.asyncio
async def test_unread_count_without_auth(client: AsyncClient):
    response = await client.get("/api/v1/notifications/unread-count")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mark_read_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.patch("/api/v1/notifications/bad-id/read", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient, auth_headers: dict):
    response = await client.patch("/api/v1/notifications/read-all", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_mark_all_read_without_auth(client: AsyncClient):
    response = await client.patch("/api/v1/notifications/read-all")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_notifications_empty_by_default(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/notifications", headers=auth_headers)
    assert response.json() == []
