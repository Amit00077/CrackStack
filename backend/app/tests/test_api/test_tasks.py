from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_today_tasks(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/tasks/today", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "tasks" in data
    assert isinstance(data["tasks"], list)


@pytest.mark.asyncio
async def test_get_today_tasks_without_auth(client: AsyncClient):
    response = await client.get("/api/v1/tasks/today")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_ad_hoc_task(client: AsyncClient, auth_headers: dict):
    payload = {
        "task_text": "Review algorithms",
        "category": "study",
        "time_estimate": 120,
        "assigned_date": "2025-06-02",
    }
    response = await client.post("/api/v1/tasks", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["task_text"] == "Review algorithms"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_task_without_required_fields(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/v1/tasks", json={}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_toggle_task(client: AsyncClient, auth_headers: dict):
    payload = {
        "task_text": "Toggle me",
        "category": "study",
        "assigned_date": "2025-06-02",
    }
    create_resp = await client.post("/api/v1/tasks", json=payload, headers=auth_headers)
    task_id = create_resp.json()["id"]
    toggle_resp = await client.patch(f"/api/v1/tasks/{task_id}/toggle", headers=auth_headers)
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_done"] is True

    toggle_resp2 = await client.patch(f"/api/v1/tasks/{task_id}/toggle", headers=auth_headers)
    assert toggle_resp2.json()["is_done"] is False


@pytest.mark.asyncio
async def test_toggle_nonexistent_task(client: AsyncClient, auth_headers: dict):
    response = await client.patch("/api/v1/tasks/bad-id/toggle", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, auth_headers: dict):
    payload = {
        "task_text": "Original text",
        "category": "study",
        "assigned_date": "2025-06-02",
    }
    create_resp = await client.post("/api/v1/tasks", json=payload, headers=auth_headers)
    task_id = create_resp.json()["id"]
    update_resp = await client.put(
        f"/api/v1/tasks/{task_id}",
        json={"task_text": "Updated text"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["task_text"] == "Updated text"


@pytest.mark.asyncio
async def test_update_nonexistent_task(client: AsyncClient, auth_headers: dict):
    response = await client.put(
        "/api/v1/tasks/bad-id",
        json={"task_text": "Nope"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, auth_headers: dict):
    payload = {
        "task_text": "Delete me",
        "category": "study",
        "assigned_date": "2025-06-02",
    }
    create_resp = await client.post("/api/v1/tasks", json=payload, headers=auth_headers)
    task_id = create_resp.json()["id"]
    del_resp = await client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_nonexistent_task(client: AsyncClient, auth_headers: dict):
    response = await client.delete("/api/v1/tasks/bad-id", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_tasks_by_date_range(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/tasks?start_date=2025-01-01&end_date=2025-12-31", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
