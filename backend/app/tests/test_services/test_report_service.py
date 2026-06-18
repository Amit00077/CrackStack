from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import WeeklyReport
from app.repositories.report import weekly_report_repository
from app.repositories.task import daily_task_repository
from app.repositories.user import user_repository
from app.services.report import report_service


@pytest.mark.asyncio
async def test_generate_report_creates_report(db_session: AsyncSession, test_user):
    report = await report_service.generate_report(db_session, test_user.id)
    assert report is not None
    assert report.user_id == test_user.id
    assert report.completed_rate >= 0.0
    assert report.readiness_score >= 0.0
    assert report.streak_health >= 0
    assert report.week_start is not None
    assert report.week_end is not None


@pytest.mark.asyncio
async def test_generate_report_completed_rate_zero_with_no_tasks(db_session: AsyncSession, test_user):
    report = await report_service.generate_report(db_session, test_user.id)
    assert report.completed_rate == 0.0


@pytest.mark.asyncio
async def test_generate_report_computes_completed_rate(db_session: AsyncSession, test_user):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Done 1", category="study",
        time_estimate=30, task_date=week_start, source="ad-hoc", is_done=True,
    )
    await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Done 2", category="study",
        time_estimate=30, task_date=week_start, source="ad-hoc", is_done=True,
    )
    await daily_task_repository.create(
        db_session, user_id=test_user.id, task_text="Pending", category="study",
        time_estimate=30, task_date=week_start, source="ad-hoc", is_done=False,
    )
    report = await report_service.generate_report(db_session, test_user.id)
    assert report.completed_rate == pytest.approx(2 / 3, rel=1e-4)


@pytest.mark.asyncio
async def test_generate_report_nonexistent_user_raises(db_session: AsyncSession):
    with pytest.raises(Exception) as exc_info:
        await report_service.generate_report(db_session, "bad-id")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_current_report(db_session: AsyncSession, test_user):
    await report_service.generate_report(db_session, test_user.id)
    report = await report_service.get_current_report(db_session, test_user.id)
    assert report is not None
    assert report.user_id == test_user.id


@pytest.mark.asyncio
async def test_get_current_report_none(db_session: AsyncSession, test_user):
    report = await report_service.get_current_report(db_session, test_user.id)
    assert report is None


@pytest.mark.asyncio
async def test_get_report_history(db_session: AsyncSession, test_user):
    await report_service.generate_report(db_session, test_user.id)
    await report_service.generate_report(db_session, test_user.id)
    history = await report_service.get_report_history(db_session, test_user.id, limit=10)
    assert len(history) >= 1


@pytest.mark.asyncio
async def test_get_report_history_empty(db_session: AsyncSession, test_user):
    history = await report_service.get_report_history(db_session, test_user.id)
    assert history == []


@pytest.mark.asyncio
async def test_build_prompt_contains_goal_data(db_session: AsyncSession, test_user):
    prompt = report_service._build_prompt(None, 0.5, 3, 75.0)
    assert "N/A" in prompt
    assert "0.5" in prompt
