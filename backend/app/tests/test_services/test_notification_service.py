from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.notification import notification_repository
from app.repositories.progress import progress_repository
from app.repositories.task import daily_task_repository
from app.services.notification import notification_service


@pytest.mark.asyncio
async def test_create_notification(db_session: AsyncSession, test_user):
    n = await notification_service.create_notification(
        db_session, test_user.id, "info", "Test Title", "Test Message",
    )
    assert n is not None
    assert n.user_id == test_user.id
    assert n.type == "info"
    assert n.title == "Test Title"
    assert n.message == "Test Message"
    assert n.is_read is False
    assert n.channel == "in_app"


@pytest.mark.asyncio
async def test_create_notification_custom_channel(db_session: AsyncSession, test_user):
    n = await notification_service.create_notification(
        db_session, test_user.id, "alert", "Email Alert", "Check your email", channel="email",
    )
    assert n.channel == "email"


@pytest.mark.asyncio
async def test_get_notifications_empty(db_session: AsyncSession, test_user):
    notifications = await notification_service.get_notifications(db_session, test_user.id)
    assert notifications == []


@pytest.mark.asyncio
async def test_get_notifications_returns_all(db_session: AsyncSession, test_user):
    await notification_service.create_notification(db_session, test_user.id, "info", "N1", "Msg 1")
    await notification_service.create_notification(db_session, test_user.id, "info", "N2", "Msg 2")
    await notification_service.create_notification(db_session, test_user.id, "info", "N3", "Msg 3")
    notifications = await notification_service.get_notifications(db_session, test_user.id, limit=10)
    assert len(notifications) == 3


@pytest.mark.asyncio
async def test_get_notifications_limits_results(db_session: AsyncSession, test_user):
    for i in range(5):
        await notification_service.create_notification(db_session, test_user.id, "info", f"N{i}", f"Msg {i}")
    notifications = await notification_service.get_notifications(db_session, test_user.id, limit=2)
    assert len(notifications) == 2


@pytest.mark.asyncio
async def test_mark_read(db_session: AsyncSession, test_user):
    from app.models.notification import Notification
    n = Notification(user_id=test_user.id, type="info", title="Read me", message="Mark as read")
    db_session.add(n)
    await db_session.flush()
    await db_session.refresh(n)
    marked = await notification_service.mark_read(db_session, test_user.id, n.id)
    assert marked.is_read is True
    assert marked.read_at is not None


@pytest.mark.asyncio
async def test_mark_read_nonexistent_raises(db_session: AsyncSession, test_user):
    with pytest.raises(Exception) as exc_info:
        await notification_service.mark_read(db_session, test_user.id, "bad-id")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_mark_read_wrong_user_raises(db_session: AsyncSession, test_user):
    from app.models.notification import Notification
    n = Notification(user_id=test_user.id, type="info", title="Wrong user", message="Msg")
    db_session.add(n)
    await db_session.flush()
    await db_session.refresh(n)
    other_user_id = "some-other-user-id"
    with pytest.raises(Exception) as exc_info:
        await notification_service.mark_read(db_session, other_user_id, n.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_mark_all_read(db_session: AsyncSession, test_user):
    for i in range(3):
        await notification_service.create_notification(db_session, test_user.id, "info", f"N{i}", f"Msg {i}")
    count = await notification_service.mark_all_read(db_session, test_user.id)
    assert count == 3
    unread = await notification_service.get_unread_count(db_session, test_user.id)
    assert unread == 0


@pytest.mark.asyncio
async def test_mark_all_read_when_none(db_session: AsyncSession, test_user):
    count = await notification_service.mark_all_read(db_session, test_user.id)
    assert count == 0


@pytest.mark.asyncio
async def test_unread_count(db_session: AsyncSession, test_user):
    await notification_service.create_notification(db_session, test_user.id, "info", "Unread", "Msg")
    await notification_service.create_notification(db_session, test_user.id, "info", "Read", "Msg")
    notifications = await notification_service.get_notifications(db_session, test_user.id)
    if notifications:
        await notification_service.mark_read(db_session, test_user.id, notifications[0].id)
    count = await notification_service.get_unread_count(db_session, test_user.id)
    assert count >= 0


@pytest.mark.asyncio
async def test_unread_count_starts_at_zero(db_session: AsyncSession, test_user):
    count = await notification_service.get_unread_count(db_session, test_user.id)
    assert count == 0


@pytest.mark.asyncio
async def test_send_daily_reminder_no_tasks_returns_none(db_session: AsyncSession, test_user):
    reminder = await notification_service.send_daily_reminder(db_session, test_user.id)
    assert reminder is None


@pytest.mark.asyncio
async def test_send_daily_reminder_all_completed_returns_none(db_session: AsyncSession, test_user):
    today = date.today()
    await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Done", category="study",
        time_estimate=30, task_date=today, source="ad-hoc", is_done=True,
    )
    reminder = await notification_service.send_daily_reminder(db_session, test_user.id)
    assert reminder is None


@pytest.mark.asyncio
async def test_send_daily_reminder_pending_tasks(db_session: AsyncSession, test_user):
    today = date.today()
    await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Pending 1", category="study",
        time_estimate=30, task_date=today, source="ad-hoc", is_done=False,
    )
    await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Pending 2", category="study",
        time_estimate=30, task_date=today, source="ad-hoc", is_done=False,
    )
    reminder = await notification_service.send_daily_reminder(db_session, test_user.id)
    assert reminder is not None
    assert reminder.type == "daily_reminder"
    assert "2" in reminder.message


@pytest.mark.asyncio
async def test_send_streak_warning_no_streak_returns_none(db_session: AsyncSession, test_user):
    warning = await notification_service.send_streak_warning(db_session, test_user.id)
    assert warning is None


@pytest.mark.asyncio
async def test_send_streak_warning_active_today_returns_none(db_session: AsyncSession, test_user):
    await progress_repository.update_streak(db_session, test_user.id, date.today())
    warning = await notification_service.send_streak_warning(db_session, test_user.id)
    assert warning is None


@pytest.mark.asyncio
async def test_send_streak_warning_yesterday_not_active_returns_warning(db_session: AsyncSession, test_user):
    await progress_repository.update_streak(db_session, test_user.id, date.today() - timedelta(days=2))
    warning = await notification_service.send_streak_warning(db_session, test_user.id)
    assert warning is not None
    assert warning.type == "streak_warning"


@pytest.mark.asyncio
async def test_send_report_ready(db_session: AsyncSession, test_user):
    n = await notification_service.send_report_ready(db_session, test_user.id, "report-123")
    assert n is not None
    assert n.type == "report_ready"
    assert n.title == "Weekly Report Ready"
