from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_roadmap(client: AsyncClient, auth_headers: dict):
    goal_payload = {
        "goal_text": "Become a full-stack developer",
        "target_company": "Startup",
        "target_role": "Full-Stack Developer",
        "duration_months": 4,
        "daily_study_hours": 3,
        "skill_level": "beginner",
        "start_date": "2025-01-01",
        "target_date": "2025-05-01",
    }
    goal_resp = await client.post("/api/v1/goals", json=goal_payload, headers=auth_headers)
    goal_id = goal_resp.json()["id"]
    response = await client.post(
        "/api/v1/roadmap/generate",
        json={"goal_id": goal_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_generate_roadmap_nonexistent_goal(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/roadmap/generate",
        json={"goal_id": "nonexistent-goal-id"},
        headers=auth_headers,
    )
    assert response.status_code in (404, 500)


@pytest.mark.asyncio
async def test_generate_without_auth(client: AsyncClient):
    response = await client.post("/api/v1/roadmap/generate", json={"goal_id": "x"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_roadmap(client: AsyncClient, auth_headers: dict):
    goal_payload = {
        "goal_text": "Get roadmap test",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 3,
        "daily_study_hours": 2,
        "skill_level": "beginner",
        "start_date": "2025-01-01",
        "target_date": "2025-04-01",
    }
    goal_resp = await client.post("/api/v1/goals", json=goal_payload, headers=auth_headers)
    goal_id = goal_resp.json()["id"]
    await client.post("/api/v1/roadmap/generate", json={"goal_id": goal_id}, headers=auth_headers)
    response = await client.get("/api/v1/roadmap", headers=auth_headers)
    assert response.status_code == 200
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_get_roadmap_when_none(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/roadmap", headers=auth_headers)
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_create_week(client: AsyncClient, auth_headers: dict):
    goal_payload = {
        "goal_text": "Week test",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 3,
        "daily_study_hours": 2,
        "skill_level": "beginner",
        "start_date": "2025-01-01",
        "target_date": "2025-04-01",
    }
    goal_resp = await client.post("/api/v1/goals", json=goal_payload, headers=auth_headers)
    goal_id = goal_resp.json()["id"]
    rm_resp = await client.post("/api/v1/roadmap/generate", json={"goal_id": goal_id}, headers=auth_headers)
    roadmap_id = rm_resp.json()["id"]
    response = await client.post(
        "/api/v1/roadmap/weeks",
        json={"roadmap_id": roadmap_id, "week_number": 5, "title": "Extra Week", "description": "Bonus content"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Extra Week"


@pytest.mark.asyncio
async def test_create_week_nonexistent_roadmap(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/roadmap/weeks",
        json={"roadmap_id": "bad-id", "week_number": 1, "title": "Week", "description": "Desc"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_week(client: AsyncClient, auth_headers: dict):
    goal_payload = {
        "goal_text": "Update week",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 2,
        "daily_study_hours": 2,
        "skill_level": "beginner",
        "start_date": "2025-01-01",
        "target_date": "2025-03-01",
    }
    goal_resp = await client.post("/api/v1/goals", json=goal_payload, headers=auth_headers)
    goal_id = goal_resp.json()["id"]
    rm_resp = await client.post("/api/v1/roadmap/generate", json={"goal_id": goal_id}, headers=auth_headers)
    week_id = rm_resp.json()["weeks"][0]["id"]
    response = await client.put(
        f"/api/v1/roadmap/weeks/{week_id}",
        json={"title": "Updated Title"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_week(client: AsyncClient, auth_headers: dict):
    goal_payload = {
        "goal_text": "Delete week",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 2,
        "daily_study_hours": 2,
        "skill_level": "beginner",
        "start_date": "2025-01-01",
        "target_date": "2025-03-01",
    }
    goal_resp = await client.post("/api/v1/goals", json=goal_payload, headers=auth_headers)
    goal_id = goal_resp.json()["id"]
    rm_resp = await client.post("/api/v1/roadmap/generate", json={"goal_id": goal_id}, headers=auth_headers)
    week_id = rm_resp.json()["weeks"][0]["id"]
    response = await client.delete(f"/api/v1/roadmap/weeks/{week_id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_reorder_weeks(client: AsyncClient, auth_headers: dict):
    goal_payload = {
        "goal_text": "Reorder",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 2,
        "daily_study_hours": 2,
        "skill_level": "beginner",
        "start_date": "2025-01-01",
        "target_date": "2025-03-01",
    }
    goal_resp = await client.post("/api/v1/goals", json=goal_payload, headers=auth_headers)
    goal_id = goal_resp.json()["id"]
    rm_resp = await client.post("/api/v1/roadmap/generate", json={"goal_id": goal_id}, headers=auth_headers)
    weeks = rm_resp.json()["weeks"]
    items = [{"week_id": w["id"], "sort_order": len(weeks) - i} for i, w in enumerate(weeks)]
    reorder_body = {"items": [{"id": i["week_id"], "sort_order": i["sort_order"]} for i in items]}
    response = await client.patch(
        "/api/v1/roadmap/weeks/reorder",
        json=reorder_body,
        headers=auth_headers,
    )
    assert response.status_code == 200
