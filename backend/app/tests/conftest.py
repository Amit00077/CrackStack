from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import AsyncGenerator, Tuple
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
settings.RATE_LIMIT_ENABLED = False
from app.core.database import Base, get_db
from app.core.security import create_token, hash_password
from app.main import app
from app.models.user import User
from app.models.goal import Goal
from app.models.daily_task import DailyTask
from app.models.roadmap import Roadmap, RoadmapWeek, RoadmapTask
from app.models.notification import Notification
from app.models.progress import UserStreak, ProgressSnapshot
from app.models.report import WeeklyReport
from app.models.chat import ChatSession, ChatMessage
from app.models.email_verification import EmailVerificationToken
from app.models.password_reset import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.repositories.goal import goal_repository
from app.repositories.task import daily_task_repository
from app.repositories.user import user_repository
from app.repositories.progress import progress_repository

TEST_DATABASE_URL = "sqlite+aiosqlite://"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_test_session_factory = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("DROP INDEX IF EXISTS ix_unique_active_goal_per_user"))
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with _test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    blacklisted: set[str] = set()

    async def mock_is_blacklisted(token: str) -> bool:
        return token in blacklisted

    async def mock_blacklist(token: str, ttl: int) -> None:
        blacklisted.add(token)

    async def mock_get_redis():
        m = MagicMock()
        m.setex = AsyncMock()
        m.exists = AsyncMock(return_value=0)
        return m

    monkeypatch.setattr("app.core.redis.is_token_blacklisted", mock_is_blacklisted)
    monkeypatch.setattr("app.core.redis.blacklist_token", mock_blacklist)
    monkeypatch.setattr("app.core.redis.get_redis", mock_get_redis)
    monkeypatch.setattr("app.api.v1.auth.get_redis", mock_get_redis)
    monkeypatch.setattr("app.core.security._get_rsa_key", lambda _: None)

    return blacklisted


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "email": "testuser@example.com",
        "password": "strongpassword123",
        "full_name": "Test User",
    })
    data = resp.json()
    return {
        "email": "testuser@example.com",
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, registered_user: dict) -> Tuple[AsyncClient, str, str]:
    client.headers["Authorization"] = f"Bearer {registered_user['access_token']}"
    return client, registered_user["access_token"], registered_user["refresh_token"]


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, registered_user: dict) -> dict:
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


@pytest_asyncio.fixture
async def test_user(client: AsyncClient, db_session: AsyncSession) -> User:
    user = await user_repository.create(
        db_session,
        email="factory@example.com",
        hashed_password=hash_password("strongpassword123"),
        full_name="Factory User",
        is_verified=True,
    )
    return user


@pytest_asyncio.fixture
async def test_goal(auth_headers: dict, client: AsyncClient) -> dict:
    start = date.today().isoformat()
    target = (date.today() + timedelta(days=180)).isoformat()
    resp = await client.post("/api/v1/goals", json={
        "goal_text": "Become a senior engineer",
        "target_company": "Google",
        "target_role": "Senior Software Engineer",
        "duration_months": 6,
        "daily_study_hours": 4,
        "skill_level": "intermediate",
        "weak_areas": ["system design", "algorithms"],
        "start_date": start,
        "target_date": target,
    }, headers=auth_headers)
    return resp.json()


@pytest_asyncio.fixture
async def test_task(auth_headers: dict, client: AsyncClient) -> dict:
    resp = await client.post("/api/v1/tasks", json={
        "task_text": "Test task",
        "category": "study",
        "time_estimate": 60,
        "assigned_date": date.today().isoformat(),
    }, headers=auth_headers)
    return resp.json()


async def create_notification(db_session: AsyncSession, user_id: str, **kwargs) -> Notification:
    n = Notification(
        user_id=user_id,
        type=kwargs.get("type", "system"),
        title=kwargs.get("title", "Test Notification"),
        message=kwargs.get("message", "Test message"),
        channel=kwargs.get("channel", "in_app"),
        is_read=kwargs.get("is_read", False),
    )
    db_session.add(n)
    await db_session.flush()
    await db_session.refresh(n)
    return n
