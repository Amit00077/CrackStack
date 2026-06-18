from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_task import DailyTask
from app.repositories.task import daily_task_repository
from app.repositories.user import user_repository
from app.services.task import task_service


@pytest.mark.asyncio
async def test_get_today_tasks_empty(db_session: AsyncSession, test_user):
    tasks = await task_service.get_today_tasks(db_session, test_user.id)
    assert tasks == []


@pytest.mark.asyncio
async def test_get_today_tasks_returns_todays_tasks(db_session: AsyncSession, test_user):
    today = date.today()
    await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Today's task", category="study",
        time_estimate=60, task_date=today, source="ad-hoc",
    )
    await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Tomorrow's task", category="study",
        time_estimate=30, task_date=date(2099, 1, 1), source="ad-hoc",
    )
    tasks = await task_service.get_today_tasks(db_session, test_user.id)
    assert len(tasks) == 1
    assert tasks[0].task_text == "Today's task"


@pytest.mark.asyncio
async def test_get_today_tasks_with_custom_date(db_session: AsyncSession, test_user):
    custom_date = date(2025, 6, 15)
    await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Custom date task", category="study",
        time_estimate=45, task_date=custom_date, source="ad-hoc",
    )
    tasks = await task_service.get_today_tasks(db_session, test_user.id, task_date=custom_date)
    assert len(tasks) == 1
    assert tasks[0].task_text == "Custom date task"


@pytest.mark.asyncio
async def test_create_ad_hoc_task(db_session: AsyncSession, test_user):
    data = {
        "task_text": "Practice algorithms",
        "category": "study",
        "time_estimate": 120,
        "task_date": date.today(),
        "source": "ad-hoc",
    }
    task = await task_service.create_task(db_session, test_user.id, data)
    assert task.task_text == "Practice algorithms"
    assert task.source == "ad-hoc"
    assert task.is_done is False
    assert task.user_id == test_user.id


@pytest.mark.asyncio
async def test_create_task_defaults(db_session: AsyncSession, test_user):
    data = {"task_text": "Minimal task"}
    task = await task_service.create_task(db_session, test_user.id, data)
    assert task.category == "study"
    assert task.time_estimate == 60
    assert task.task_date == date.today()


@pytest.mark.asyncio
async def test_create_task_nonexistent_user_raises(db_session: AsyncSession):
    data = {"task_text": "No user"}
    with pytest.raises(Exception) as exc_info:
        await task_service.create_task(db_session, "bad-id", data)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_toggle_task(db_session: AsyncSession, test_user):
    task = await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Toggle test", category="study",
        time_estimate=30, task_date=date.today(), source="ad-hoc", is_done=False,
    )
    toggled = await task_service.toggle_task(db_session, task.id, test_user.id)
    assert toggled.is_done is True
    assert toggled.completed_at is not None

    toggled_again = await task_service.toggle_task(db_session, task.id, test_user.id)
    assert toggled_again.is_done is False
    assert toggled_again.completed_at is None


@pytest.mark.asyncio
async def test_toggle_nonexistent_task_raises(db_session: AsyncSession, test_user):
    with pytest.raises(Exception) as exc_info:
        await task_service.toggle_task(db_session, "bad-id", test_user.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_task(db_session: AsyncSession, test_user):
    task = await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Original", category="study",
        time_estimate=30, task_date=date.today(), source="ad-hoc",
    )
    updated = await task_service.update_task(db_session, task.id, test_user.id, {"task_text": "Updated", "time_estimate": 90})
    assert updated.task_text == "Updated"
    assert updated.time_estimate == 90


@pytest.mark.asyncio
async def test_update_nonexistent_task_raises(db_session: AsyncSession, test_user):
    with pytest.raises(Exception) as exc_info:
        await task_service.update_task(db_session, "bad-id", test_user.id, {"task_text": "X"})
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_task(db_session: AsyncSession, test_user):
    task = await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Delete me", category="study",
        time_estimate=15, task_date=date.today(), source="ad-hoc",
    )
    await task_service.delete_task(db_session, task.id, test_user.id)
    deleted = await daily_task_repository.get(db_session, id=task.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_nonexistent_task_raises(db_session: AsyncSession, test_user):
    with pytest.raises(Exception) as exc_info:
        await task_service.delete_task(db_session, "bad-id", test_user.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_tasks_by_date_range(db_session: AsyncSession, test_user):
    d1 = date(2025, 6, 1)
    d2 = date(2025, 6, 2)
    d3 = date(2025, 6, 5)
    await daily_task_repository.create(db_session, user_id=test_user.id, task_text="Task 1", category="study", time_estimate=30, task_date=d1, source="ad-hoc")
    await daily_task_repository.create(db_session, user_id=test_user.id, task_text="Task 2", category="study", time_estimate=30, task_date=d2, source="ad-hoc")
    await daily_task_repository.create(db_session, user_id=test_user.id, task_text="Task 3", category="study", time_estimate=30, task_date=d3, source="ad-hoc")
    tasks = await task_service.get_tasks_by_date_range(db_session, test_user.id, date(2025, 6, 1), date(2025, 6, 2))
    assert len(tasks) == 2
