from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.progress import progress_repository
from app.repositories.task import daily_task_repository
from app.services.dashboard import dashboard_service


@pytest.mark.asyncio
async def test_get_dashboard_returns_all_keys(db_session: AsyncSession, test_user):
    data = await dashboard_service.get_dashboard(db_session, test_user.id)
    assert "overall_progress" in data
    assert "current_day" in data
    assert "streak" in data
    assert "total_solved" in data
    assert "avg_study_time" in data
    assert "topic_coverage" in data
    assert "activity_heatmap" in data


@pytest.mark.asyncio
async def test_get_dashboard_defaults_when_no_data(db_session: AsyncSession, test_user):
    data = await dashboard_service.get_dashboard(db_session, test_user.id)
    assert data["overall_progress"] == 0.0
    assert data["current_day"] == 0
    assert data["total_solved"] == 0
    assert data["avg_study_time"] == 0.0
    assert data["topic_coverage"] == {"completed": 0, "total": 0}
    assert len(data["activity_heatmap"]) == 30


@pytest.mark.asyncio
async def test_get_dashboard_streak_data(db_session: AsyncSession, test_user):
    await progress_repository.update_streak(db_session, test_user.id, date.today())
    data = await dashboard_service.get_dashboard(db_session, test_user.id)
    assert data["streak"]["current_streak"] >= 1
    assert data["streak"]["best_streak"] >= 1
    assert data["streak"]["last_active_date"] is not None


@pytest.mark.asyncio
async def test_get_dashboard_progress_with_goal(db_session: AsyncSession, test_user):
    from app.repositories.goal import goal_repository
    goal = await goal_repository.create(
        db_session, user_id=test_user.id, goal_text="Test", target_company="Co",
        target_role="Dev", duration_months=6, daily_study_hours=3,
        skill_level="beginner", start_date=date.today() - timedelta(days=30),
        target_date=date.today() + timedelta(days=150),
    )
    data = await dashboard_service.get_dashboard(db_session, test_user.id)
    assert data["current_day"] >= 30


@pytest.mark.asyncio
async def test_get_dashboard_includes_heatmap_with_snapshots(db_session: AsyncSession, test_user):
    await progress_repository.update_snapshot(
        db_session, test_user.id, date.today(),
        tasks_completed=3, tasks_total=5, study_time_minutes=120,
    )
    data = await dashboard_service.get_dashboard(db_session, test_user.id)
    assert len(data["activity_heatmap"]) == 30
    entry = data["activity_heatmap"][29]
    assert entry["tasks_completed"] == 3
    assert entry["tasks_total"] == 5
    assert entry["study_time_minutes"] == 120


@pytest.mark.asyncio
async def test_get_dashboard_topic_coverage(db_session: AsyncSession, test_user):
    await progress_repository.update_snapshot(
        db_session, test_user.id, date.today(),
        tasks_completed=5, tasks_total=10, study_time_minutes=60,
        categories_completed=2, categories_total=4,
    )
    data = await dashboard_service.get_dashboard(db_session, test_user.id)
    assert data["topic_coverage"] == {"completed": 2, "total": 4}


@pytest.mark.asyncio
async def test_get_streak_zero_when_no_activity(db_session: AsyncSession, test_user):
    streak = await dashboard_service.get_streak(db_session, test_user.id)
    assert streak["current_streak"] == 0
    assert streak["best_streak"] == 0
    assert streak["last_active_date"] is None


@pytest.mark.asyncio
async def test_get_streak_after_activity(db_session: AsyncSession, test_user):
    await progress_repository.update_streak(db_session, test_user.id, date.today())
    streak = await dashboard_service.get_streak(db_session, test_user.id)
    assert streak["current_streak"] >= 1
    assert streak["last_active_date"] is not None


@pytest.mark.asyncio
async def test_get_streak_increments_on_consecutive_days(db_session: AsyncSession, test_user):
    today = date.today()
    await progress_repository.update_streak(db_session, test_user.id, today - timedelta(days=1))
    await progress_repository.update_streak(db_session, test_user.id, today)
    streak = await dashboard_service.get_streak(db_session, test_user.id)
    assert streak["current_streak"] >= 2
