from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_report(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/v1/reports/generate", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "report_id" in data


@pytest.mark.asyncio
async def test_generate_report_without_auth(client: AsyncClient):
    response = await client.post("/api/v1/reports/generate")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_report(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/reports/generate", headers=auth_headers)
    response = await client.get("/api/v1/reports/current", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "week_start" in data
    assert "week_end" in data


@pytest.mark.asyncio
async def test_get_current_report_when_none(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/reports/current", headers=auth_headers)
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_get_report_history(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/reports/generate", headers=auth_headers)
    response = await client.get("/api/v1/reports/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_report_history_empty(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/reports/history", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_report_history_without_auth(client: AsyncClient):
    response = await client.get("/api/v1/reports/history")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_report_without_auth(client: AsyncClient):
    response = await client.get("/api/v1/reports/current")
    assert response.status_code == 401
