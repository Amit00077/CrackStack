from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_goal(client: AsyncClient, auth_headers: dict):
    payload = {
        "goal_text": "Become an ML engineer",
        "target_company": "OpenAI",
        "target_role": "ML Engineer",
        "duration_months": 6,
        "daily_study_hours": 4,
        "skill_level": "intermediate",
        "weak_areas": ["transformers", "reinforcement learning"],
        "start_date": "2025-01-01",
        "target_date": "2025-07-01",
    }
    response = await client.post("/api/v1/goals", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["goal_text"] == "Become an ML engineer"
    assert data["target_company"] == "OpenAI"
    assert data["target_role"] == "ML Engineer"
    assert data["is_active"] is True
    assert "id" in data
    assert "weak_areas" in data


@pytest.mark.asyncio
async def test_create_goal_without_auth(client: AsyncClient):
    payload = {
        "goal_text": "Test",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 3,
        "daily_study_hours": 2,
        "skill_level": "beginner",
        "start_date": "2025-01-01",
        "target_date": "2025-04-01",
    }
    response = await client.post("/api/v1/goals", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_active_goal(client: AsyncClient, auth_headers: dict):
    payload = {
        "goal_text": "Get active goal",
        "target_company": "Meta",
        "target_role": "SDE",
        "duration_months": 4,
        "daily_study_hours": 3,
        "skill_level": "advanced",
        "start_date": "2025-02-01",
        "target_date": "2025-06-01",
    }
    await client.post("/api/v1/goals", json=payload, headers=auth_headers)
    response = await client.get("/api/v1/goals/active", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["goal_text"] == "Get active goal"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_active_goal_none(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/goals/active", headers=auth_headers)
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_only_one_active_goal(client: AsyncClient, auth_headers: dict):
    base = {
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 3,
        "daily_study_hours": 2,
        "skill_level": "beginner",
    }
    g1 = {**base, "goal_text": "First", "start_date": "2025-01-01", "target_date": "2025-04-01"}
    g2 = {**base, "goal_text": "Second", "start_date": "2025-05-01", "target_date": "2025-08-01"}
    await client.post("/api/v1/goals", json=g1, headers=auth_headers)
    await client.post("/api/v1/goals", json=g2, headers=auth_headers)
    resp = await client.get("/api/v1/goals/active", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["goal_text"] == "Second"


@pytest.mark.asyncio
async def test_update_goal(client: AsyncClient, auth_headers: dict):
    payload = {
        "goal_text": "Original",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 3,
        "daily_study_hours": 2,
        "skill_level": "beginner",
        "start_date": "2025-01-01",
        "target_date": "2025-04-01",
    }
    create_resp = await client.post("/api/v1/goals", json=payload, headers=auth_headers)
    goal_id = create_resp.json()["id"]
    update_resp = await client.put(
        f"/api/v1/goals/{goal_id}",
        json={"goal_text": "Updated goal text"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["goal_text"] == "Updated goal text"


@pytest.mark.asyncio
async def test_update_nonexistent_goal(client: AsyncClient, auth_headers: dict):
    response = await client.put(
        "/api/v1/goals/nonexistent-id",
        json={"goal_text": "Nope"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_goal(client: AsyncClient, auth_headers: dict):
    payload = {
        "goal_text": "To delete",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 2,
        "daily_study_hours": 1,
        "skill_level": "beginner",
        "start_date": "2025-01-01",
        "target_date": "2025-03-01",
    }
    create_resp = await client.post("/api/v1/goals", json=payload, headers=auth_headers)
    goal_id = create_resp.json()["id"]
    del_resp = await client.delete(f"/api/v1/goals/{goal_id}", headers=auth_headers)
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_nonexistent_goal(client: AsyncClient, auth_headers: dict):
    response = await client.delete("/api/v1/goals/bad-id", headers=auth_headers)
    assert response.status_code == 404
