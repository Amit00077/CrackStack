from __future__ import annotations

import json
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap import Roadmap
from app.repositories.goal import goal_repository
from app.repositories.roadmap import roadmap_repository, roadmap_week_repository
from app.repositories.user import user_repository
from app.services.roadmap import roadmap_service


@pytest.mark.asyncio
async def test_generate_roadmap_creates_roadmap_with_weeks(db_session: AsyncSession, test_user):
    goal = await goal_repository.create(
        db_session, user_id=test_user.id, goal_text="Learn Go", target_company="Co",
        target_role="Go Dev", duration_months=3, daily_study_hours=2,
        skill_level="intermediate", weak_areas=["concurrency"],
        start_date=date.today(), target_date=date.today() + timedelta(days=90),
    )
    roadmap = await roadmap_service.generate_roadmap(db_session, test_user.id, goal.id)
    assert roadmap is not None
    assert roadmap.user_id == test_user.id
    assert roadmap.goal_id == goal.id
    assert roadmap.is_active is True
    assert roadmap.weeks_count > 0


@pytest.mark.asyncio
async def test_generate_roadmap_nonexistent_goal_raises(db_session: AsyncSession, test_user):
    with pytest.raises(Exception) as exc_info:
        await roadmap_service.generate_roadmap(db_session, test_user.id, "bad-goal-id")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_generate_roadmap_nonexistent_user_raises(db_session: AsyncSession):
    with pytest.raises(Exception) as exc_info:
        await roadmap_service.generate_roadmap(db_session, "bad-user-id", "some-goal-id")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_generate_deactivates_previous_active_roadmap(db_session: AsyncSession, test_user):
    goal1 = await goal_repository.create(
        db_session, user_id=test_user.id, goal_text="Goal 1", target_company="Co",
        target_role="Dev", duration_months=2, daily_study_hours=1, skill_level="beginner",
        start_date=date.today(), target_date=date.today() + timedelta(days=60),
    )
    goal2 = await goal_repository.create(
        db_session, user_id=test_user.id, goal_text="Goal 2", target_company="Co",
        target_role="Dev", duration_months=2, daily_study_hours=1, skill_level="beginner",
        start_date=date.today(), target_date=date.today() + timedelta(days=60),
    )
    rm1 = await roadmap_service.generate_roadmap(db_session, test_user.id, goal1.id)
    assert rm1.is_active is True
    rm2 = await roadmap_service.generate_roadmap(db_session, test_user.id, goal2.id)
    assert rm2.is_active is True
    await db_session.refresh(rm1)
    assert rm1.is_active is False


@pytest.mark.asyncio
async def test_get_roadmap_returns_active(db_session: AsyncSession, test_user):
    goal = await goal_repository.create(
        db_session, user_id=test_user.id, goal_text="Get roadmap", target_company="Co",
        target_role="Dev", duration_months=2, daily_study_hours=1, skill_level="beginner",
        start_date=date.today(), target_date=date.today() + timedelta(days=60),
    )
    await roadmap_service.generate_roadmap(db_session, test_user.id, goal.id)
    roadmap = await roadmap_service.get_roadmap(db_session, test_user.id)
    assert roadmap is not None
    assert roadmap.is_active is True
    assert len(roadmap.weeks) > 0


@pytest.mark.asyncio
async def test_get_roadmap_returns_none_when_no_active(db_session: AsyncSession, test_user):
    roadmap = await roadmap_service.get_roadmap(db_session, test_user.id)
    assert roadmap is None


@pytest.mark.asyncio
async def test_create_week(db_session: AsyncSession, test_user):
    goal = await goal_repository.create(
        db_session, user_id=test_user.id, goal_text="Week test", target_company="Co",
        target_role="Dev", duration_months=2, daily_study_hours=1, skill_level="beginner",
        start_date=date.today(), target_date=date.today() + timedelta(days=60),
    )
    rm = await roadmap_service.generate_roadmap(db_session, test_user.id, goal.id)
    week = await roadmap_service.create_week(db_session, test_user.id, {
        "week_number": 99, "title": "Bonus Week", "description": "Extra content", "roadmap_id": rm.id,
    })
    assert week.week_number == 99
    assert week.title == "Bonus Week"
    assert week.sort_order >= 0


@pytest.mark.asyncio
async def test_create_week_nonexistent_roadmap_raises(db_session: AsyncSession, test_user):
    with pytest.raises(Exception) as exc_info:
        await roadmap_service.create_week(db_session, test_user.id, {"week_number": 1, "title": "X", "description": "X", "roadmap_id": "bad-id"})
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_week(db_session: AsyncSession, test_user):
    goal = await goal_repository.create(
        db_session, user_id=test_user.id, goal_text="Update week", target_company="Co",
        target_role="Dev", duration_months=2, daily_study_hours=1, skill_level="beginner",
        start_date=date.today(), target_date=date.today() + timedelta(days=60),
    )
    rm = await roadmap_service.generate_roadmap(db_session, test_user.id, goal.id)
    week = rm.weeks[0]
    updated = await roadmap_service.update_week(db_session, test_user.id, week.id, {"title": "Updated Title"})
    assert updated.title == "Updated Title"


@pytest.mark.asyncio
async def test_update_week_not_owned_raises(db_session: AsyncSession, test_user):
    goal = await goal_repository.create(
        db_session, user_id=test_user.id, goal_text="Ownership", target_company="Co",
        target_role="Dev", duration_months=2, daily_study_hours=1, skill_level="beginner",
        start_date=date.today(), target_date=date.today() + timedelta(days=60),
    )
    rm = await roadmap_service.generate_roadmap(db_session, test_user.id, goal.id)
    week = rm.weeks[0]
    other_user = await user_repository.create(db_session, email="other@test.com", hashed_password="x")
    with pytest.raises(Exception) as exc_info:
        await roadmap_service.update_week(db_session, other_user.id, week.id, {"title": "Hack"})
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_week(db_session: AsyncSession, test_user):
    goal = await goal_repository.create(
        db_session, user_id=test_user.id, goal_text="Delete week", target_company="Co",
        target_role="Dev", duration_months=2, daily_study_hours=1, skill_level="beginner",
        start_date=date.today(), target_date=date.today() + timedelta(days=60),
    )
    rm = await roadmap_service.generate_roadmap(db_session, test_user.id, goal.id)
    week_id = rm.weeks[0].id
    await roadmap_service.delete_week(db_session, test_user.id, week_id)
    deleted = await roadmap_week_repository.get(db_session, id=week_id)
    assert deleted is None


@pytest.mark.asyncio
async def test_reorder_weeks(db_session: AsyncSession, test_user):
    goal = await goal_repository.create(
        db_session, user_id=test_user.id, goal_text="Reorder", target_company="Co",
        target_role="Dev", duration_months=2, daily_study_hours=1, skill_level="beginner",
        start_date=date.today(), target_date=date.today() + timedelta(days=60),
    )
    rm = await roadmap_service.generate_roadmap(db_session, test_user.id, goal.id)
    weeks = rm.weeks
    items = [{"id": w.id, "sort_order": len(weeks) - i} for i, w in enumerate(weeks)]
    reordered = await roadmap_service.reorder_weeks(db_session, test_user.id, items)
    assert len(reordered) == len(items)


@pytest.mark.asyncio
async def test_build_prompt_returns_json_with_goal_data(db_session: AsyncSession, test_user):
    goal = await goal_repository.create(
        db_session, user_id=test_user.id, goal_text="Master Python", target_company="Co",
        target_role="Python Dev", duration_months=4, daily_study_hours=3,
        skill_level="beginner", weak_areas=["async", "testing"],
        start_date=date.today(), target_date=date.today() + timedelta(days=120),
    )
    prompt = roadmap_service._build_prompt(goal)
    parsed = json.loads(prompt)
    assert parsed["goal_text"] == "Master Python"
    assert parsed["target_role"] == "Python Dev"
    assert parsed["duration_months"] == 4
    assert "async" in parsed["weak_areas"]
