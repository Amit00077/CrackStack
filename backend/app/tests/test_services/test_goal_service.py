from __future__ import annotations

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal
from app.repositories.goal import goal_repository
from app.repositories.user import user_repository
from app.services.goal import goal_service


@pytest.mark.asyncio
async def test_create_goal_derives_target_date(db_session: AsyncSession, test_user):
    data = {
        "goal_text": "Learn Python",
        "target_company": "TestCo",
        "target_role": "Python Dev",
        "duration_months": 6,
        "daily_study_hours": 3,
        "skill_level": "beginner",
        "weak_areas": ["async", "testing"],
        "start_date": date.today(),
    }
    goal = await goal_service.create_goal(db_session, test_user.id, data)
    assert goal.target_date == goal.start_date + relativedelta(months=+6)
    assert goal.goal_text == "Learn Python"
    assert goal.is_active is True
    assert goal.duration_months == 6


@pytest.mark.asyncio
async def test_create_goal_sets_default_start_date(db_session: AsyncSession, test_user):
    data = {
        "goal_text": "No start date",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 3,
        "daily_study_hours": 2,
        "skill_level": "beginner",
    }
    goal = await goal_service.create_goal(db_session, test_user.id, data)
    assert goal.start_date == date.today()


@pytest.mark.asyncio
async def test_create_goal_without_weak_areas(db_session: AsyncSession, test_user):
    data = {
        "goal_text": "No weak areas",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 2,
        "daily_study_hours": 1,
        "skill_level": "advanced",
    }
    goal = await goal_service.create_goal(db_session, test_user.id, data)
    assert goal.weak_areas == []


@pytest.mark.asyncio
async def test_create_goal_nonexistent_user_raises(db_session: AsyncSession):
    data = {
        "goal_text": "Test",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 3,
        "daily_study_hours": 2,
        "skill_level": "beginner",
    }
    with pytest.raises(Exception) as exc_info:
        await goal_service.create_goal(db_session, "nonexistent-user-id", data)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_only_one_active_goal_per_user(db_session: AsyncSession, test_user):
    base = {
        "goal_text": "First goal",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 3,
        "daily_study_hours": 2,
        "skill_level": "beginner",
        "start_date": date.today(),
    }
    g1 = await goal_service.create_goal(db_session, test_user.id, {**base, "goal_text": "First"})
    assert g1.is_active is True
    g2 = await goal_service.create_goal(db_session, test_user.id, {**base, "goal_text": "Second"})
    assert g2.is_active is True
    await db_session.refresh(g1)
    assert g1.is_active is False


@pytest.mark.asyncio
async def test_get_active_goal(db_session: AsyncSession, test_user):
    data = {
        "goal_text": "Active check",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 4,
        "daily_study_hours": 2,
        "skill_level": "intermediate",
        "start_date": date.today(),
    }
    await goal_service.create_goal(db_session, test_user.id, data)
    active = await goal_service.get_active(db_session, test_user.id)
    assert active is not None
    assert active.goal_text == "Active check"
    assert active.is_active is True


@pytest.mark.asyncio
async def test_get_active_goal_none(db_session: AsyncSession, test_user):
    active = await goal_service.get_active(db_session, test_user.id)
    assert active is None


@pytest.mark.asyncio
async def test_update_goal(db_session: AsyncSession, test_user):
    data = {
        "goal_text": "Original",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 3,
        "daily_study_hours": 2,
        "skill_level": "beginner",
        "start_date": date.today(),
    }
    goal = await goal_service.create_goal(db_session, test_user.id, data)
    updated = await goal_service.update_goal(db_session, goal.id, test_user.id, {"goal_text": "Updated"})
    assert updated.goal_text == "Updated"


@pytest.mark.asyncio
async def test_update_goal_updates_target_date_when_duration_changes(db_session: AsyncSession, test_user):
    start = date(2025, 1, 1)
    data = {
        "goal_text": "Duration change",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 3,
        "daily_study_hours": 2,
        "skill_level": "beginner",
        "start_date": start,
    }
    goal = await goal_service.create_goal(db_session, test_user.id, data)
    original_target = goal.target_date
    updated = await goal_service.update_goal(db_session, goal.id, test_user.id, {"duration_months": 6})
    assert updated.target_date > original_target


@pytest.mark.asyncio
async def test_update_nonexistent_goal_raises(db_session: AsyncSession, test_user):
    with pytest.raises(Exception) as exc_info:
        await goal_service.update_goal(db_session, "bad-id", test_user.id, {"goal_text": "X"})
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_goal(db_session: AsyncSession, test_user):
    data = {
        "goal_text": "To delete",
        "target_company": "Co",
        "target_role": "Dev",
        "duration_months": 2,
        "daily_study_hours": 1,
        "skill_level": "beginner",
        "start_date": date.today(),
    }
    goal = await goal_service.create_goal(db_session, test_user.id, data)
    await goal_service.delete_goal(db_session, goal.id, test_user.id)
    deleted = await goal_repository.get(db_session, id=goal.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_nonexistent_goal_raises(db_session: AsyncSession, test_user):
    with pytest.raises(Exception) as exc_info:
        await goal_service.delete_goal(db_session, "bad-id", test_user.id)
    assert exc_info.value.status_code == 404
