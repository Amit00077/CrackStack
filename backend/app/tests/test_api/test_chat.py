from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_message(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/chat/message",
        json={"message": "Hello, what should I study today?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/event-stream")


@pytest.mark.asyncio
async def test_chat_message_with_session(client: AsyncClient, auth_headers: dict):
    sessions_resp = await client.get("/api/v1/chat/sessions", headers=auth_headers)
    sessions = sessions_resp.json()
    if sessions:
        session_id = sessions[0]["id"]
    else:
        session_resp = await client.post(
            "/api/v1/chat/message",
            json={"message": "Start session"},
            headers=auth_headers,
        )
        assert session_resp.status_code == 200
        sessions_resp2 = await client.get("/api/v1/chat/sessions", headers=auth_headers)
        session_id = sessions_resp2.json()[0]["id"]
    response = await client.post(
        "/api/v1/chat/message",
        json={"message": "Follow up question", "session_id": session_id},
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_message_without_auth(client: AsyncClient):
    response = await client.post("/api/v1/chat/message", json={"message": "Hi"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/chat/sessions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_sessions_without_auth(client: AsyncClient):
    response = await client.get("/api/v1/chat/sessions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_session(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/v1/chat/message",
        json={"message": "Create session for get"},
        headers=auth_headers,
    )
    sessions_resp = await client.get("/api/v1/chat/sessions", headers=auth_headers)
    sessions = sessions_resp.json()
    if sessions:
        session_id = sessions[0]["id"]
        response = await client.get(f"/api/v1/chat/sessions/{session_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "messages" in data


@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/chat/sessions/bad-id", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_session(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/v1/chat/message",
        json={"message": "Delete this session"},
        headers=auth_headers,
    )
    sessions_resp = await client.get("/api/v1/chat/sessions", headers=auth_headers)
    sessions = sessions_resp.json()
    if sessions:
        session_id = sessions[0]["id"]
        del_resp = await client.delete(f"/api/v1/chat/sessions/{session_id}", headers=auth_headers)
        assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_session_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.delete("/api/v1/chat/sessions/bad-id", headers=auth_headers)
    assert response.status_code == 404
