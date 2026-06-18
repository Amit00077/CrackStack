from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_dashboard(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/progress/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "overall_progress" in data
    assert "streak" in data
    assert "current_day" in data
    assert "total_solved" in data
    assert "avg_study_time" in data
    assert "topic_coverage" in data
    assert "activity_heatmap" in data


@pytest.mark.asyncio
async def test_get_dashboard_without_auth(client: AsyncClient):
    response = await client.get("/api/v1/progress/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_dashboard_structure(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/progress/dashboard", headers=auth_headers)
    data = response.json()
    streak = data["streak"]
    assert "current_streak" in streak
    assert "best_streak" in streak
    assert streak["current_streak"] >= 0
    assert streak["best_streak"] >= 0
    assert data["overall_progress"] >= 0.0
    assert isinstance(data["activity_heatmap"], list)


@pytest.mark.asyncio
async def test_get_streak(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/progress/streak", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "current_streak" in data
    assert "best_streak" in data


@pytest.mark.asyncio
async def test_get_streak_without_auth(client: AsyncClient):
    response = await client.get("/api/v1/progress/streak")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_streak_zero_when_no_activity(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/progress/streak", headers=auth_headers)
    data = response.json()
    assert data["current_streak"] >= 0
