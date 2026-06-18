from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.ai import get_active_ai_client
from app.models.goal import Goal
from app.models.roadmap import Roadmap, RoadmapWeek, RoadmapTask
from app.repositories.goal import goal_repository
from app.repositories.roadmap import roadmap_repository, roadmap_week_repository, roadmap_task_repository
from app.repositories.user import user_repository
from app.utils.timezone import get_week_start_from_goal

logger = logging.getLogger(__name__)


async def _call_ai_api(prompt: str, db: AsyncSession) -> dict:
    client, model, max_tokens = await get_active_ai_client(db)
    if not client:
        logger.warning("No active AI provider, using fallback template")
        return _fallback_roadmap()

    system_msg = (
        "You are a study roadmap generator. "
        "Return ONLY valid JSON matching this schema: "
        '{"weeks": [{"week_number": int, "title": str, "description": str, '
        '"tasks": [{"task_text": str, "category": "study"|"practice"|"project"|"review", '
        '"time_estimate": int}]}]}'
    )

    try:
        kwargs = dict(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        resp = await client.chat.completions.create(**kwargs)
        raw = resp.choices[0].message.content
        parsed = json.loads(raw)
        if "weeks" not in parsed or not isinstance(parsed["weeks"], list):
            raise ValueError("Response missing 'weeks' array")
        return parsed
    except Exception as exc:
        logger.warning("AI call failed, using fallback: %s", exc)
        return _fallback_roadmap()


def _fallback_roadmap() -> dict:
    weeks = []
    for w in range(1, 5):
        weeks.append({
            "week_number": w,
            "title": f"Week {w}: Foundation",
            "description": "Focus on core concepts",
            "tasks": [
                {"task_text": f"Study topic {t}", "category": "study", "time_estimate": 60}
                for t in range(1, 6)
            ],
        })
    return {"weeks": weeks}


class RoadmapService:
    async def generate_roadmap(self, db: AsyncSession, user_id: str, goal_id: str) -> Roadmap:
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "USER_NOT_FOUND", "details": "User not found"},
            )
        goal = await goal_repository.get(db, id=goal_id, user_id=user_id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "GOAL_NOT_FOUND", "details": "Goal not found"},
            )
        existing_active = await roadmap_repository.get_active_by_user(db, user_id)
        if existing_active:
            existing_active.is_active = False
            await db.flush()
        prompt = self._build_prompt(goal)
        try:
            ai_response = await _call_ai_api(prompt, db)
        except Exception as exc:
            logger.warning("AI call failed, using fallback template: %s", exc)
            ai_response = await _call_ai_api("", db)
        roadmap = await roadmap_repository.create(
            db,
            user_id=user_id,
            goal_id=goal_id,
            title=f"Roadmap to {goal.target_role} at {goal.target_company}",
            description=f"Study plan for {goal.goal_text}",
            weeks_count=len(ai_response.get("weeks", [])),
        )
        for week_data in ai_response.get("weeks", []):
            week_start = get_week_start_from_goal(goal.start_date, week_data["week_number"])
            week = await roadmap_week_repository.create(
                db,
                roadmap_id=roadmap.id,
                week_number=week_data["week_number"],
                title=week_data["title"],
                description=week_data.get("description", ""),
                sort_order=week_data["week_number"],
                start_date=week_start,
                status="pending",
            )
            tasks = week_data.get("tasks", [])
            created_tasks = await roadmap_task_repository.bulk_create(db, week.id, tasks)
            for i, rt in enumerate(created_tasks):
                day_offset = getattr(rt, "day_offset", None)
                if day_offset is None:
                    day_offset = i + 1
                if not (1 <= day_offset <= 7):
                    day_offset = i + 1
                assigned = week_start + timedelta(days=day_offset - 1)
                rt.day_offset = day_offset
                rt.assigned_date = assigned
                rt.goal_id = goal_id
                rt.user_id = user_id
            await db.flush()
        query = (
            select(Roadmap)
            .options(joinedload(Roadmap.weeks).joinedload(RoadmapWeek.tasks))
            .filter_by(id=roadmap.id)
        )
        result = await db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_roadmap(self, db: AsyncSession, user_id: str) -> Roadmap | None:
        roadmap = await roadmap_repository.get_active_by_user(db, user_id)
        if not roadmap:
            return None
        query = (
            select(Roadmap)
            .options(
                joinedload(Roadmap.weeks).joinedload(RoadmapWeek.tasks)
            )
            .filter_by(id=roadmap.id)
        )
        result = await db.execute(query)
        return result.unique().scalar_one_or_none()

    async def create_week_internal(self, db: AsyncSession, user_id: str, roadmap_id: str, data: dict) -> RoadmapWeek:
        roadmap = await roadmap_repository.get(db, id=roadmap_id, user_id=user_id)
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "ROADMAP_NOT_FOUND", "details": "Roadmap not found"},
            )
        if "start_date" not in data and roadmap.goal_id:
            goal = await goal_repository.get(db, id=roadmap.goal_id)
            if goal:
                data["start_date"] = get_week_start_from_goal(goal.start_date, data.get("week_number", 1))
        weeks = await roadmap_week_repository.get_by_roadmap(db, roadmap_id)
        week = await roadmap_week_repository.create(
            db,
            roadmap_id=roadmap_id,
            week_number=data.get("week_number", len(weeks) + 1),
            title=data.get("title", f"Week {len(weeks) + 1}"),
            description=data.get("description", ""),
            sort_order=len(weeks),
            start_date=data.get("start_date"),
        )
        roadmap.weeks_count = len(weeks) + 1
        await db.flush()
        await db.refresh(week, ["tasks"])
        return week

    async def _update_week_internal(self, db: AsyncSession, week_id: str, user_id: str, data: dict) -> RoadmapWeek:
        week = await roadmap_week_repository.get(db, id=week_id)
        if not week:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "WEEK_NOT_FOUND", "details": "Week not found"},
            )
        roadmap = await roadmap_repository.get(db, id=week.roadmap_id, user_id=user_id)
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "ROADMAP_NOT_FOUND", "details": "Roadmap not found"},
            )
        update_data = {}
        for key in ("week_number", "title", "description", "sort_order"):
            if key in data:
                update_data[key] = data[key]
        week = await roadmap_week_repository.update(db, week, **update_data)
        await db.refresh(week, ["tasks"])
        return week

    async def _delete_week_internal(self, db: AsyncSession, week_id: str, user_id: str) -> None:
        week = await roadmap_week_repository.get(db, id=week_id)
        if not week:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "WEEK_NOT_FOUND", "details": "Week not found"},
            )
        roadmap = await roadmap_repository.get(db, id=week.roadmap_id, user_id=user_id)
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "ROADMAP_NOT_FOUND", "details": "Roadmap not found"},
            )
        await roadmap_task_repository.delete_by_week(db, week_id)
        await roadmap_week_repository.delete(db, week)
        weeks = await roadmap_week_repository.get_by_roadmap(db, roadmap.id)
        roadmap.weeks_count = len(weeks)
        await db.flush()

    async def reorder_weeks_internal(self, db: AsyncSession, user_id: str, items: list[dict]) -> list[RoadmapWeek]:
        if not items:
            return []
        first = await roadmap_week_repository.get(db, id=items[0]["id"])
        if not first:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "WEEK_NOT_FOUND", "details": "Week not found"},
            )
        roadmap = await roadmap_repository.get(db, id=first.roadmap_id, user_id=user_id)
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "ROADMAP_NOT_FOUND", "details": "Roadmap not found"},
            )
        return await roadmap_week_repository.reorder(db, items)

    def _build_prompt(self, goal) -> str:
        return json.dumps({
            "goal_text": goal.goal_text,
            "target_company": goal.target_company,
            "target_role": goal.target_role,
            "duration_months": goal.duration_months,
            "daily_study_hours": goal.daily_study_hours,
            "skill_level": goal.skill_level,
            "weak_areas": goal.weak_areas,
        })


    async def delete(self, db: AsyncSession, user) -> None:
        uid = user.id if hasattr(user, "id") else user
        roadmap = await roadmap_repository.get_active_by_user(db, uid)
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "ROADMAP_NOT_FOUND", "details": "No active roadmap found"},
            )
        await roadmap_repository.delete(db, roadmap)

    async def generate(self, db: AsyncSession, user, goal_id: str) -> Roadmap:
        uid = user.id if hasattr(user, "id") else user
        return await self.generate_roadmap(db, uid, goal_id)

    async def get_active(self, db: AsyncSession, user) -> Roadmap | None:
        uid = user.id if hasattr(user, "id") else user
        return await self.get_roadmap(db, uid)

    async def create_week(self, db: AsyncSession, user, request) -> RoadmapWeek:
        data = request.model_dump() if hasattr(request, "model_dump") else dict(request)
        uid = user.id if hasattr(user, "id") else user
        return await self.create_week_internal(db, uid, data["roadmap_id"], data)

    async def update_week(self, db: AsyncSession, user, week_id: str, request) -> RoadmapWeek:
        data = request.model_dump(exclude_unset=True) if hasattr(request, "model_dump") else dict(request)
        uid = user.id if hasattr(user, "id") else user
        return await self._update_week_internal(db, week_id, uid, data)

    async def delete_week(self, db: AsyncSession, user, week_id: str) -> None:
        uid = user.id if hasattr(user, "id") else user
        return await self._delete_week_internal(db, week_id, uid)

    async def reorder_weeks(self, db: AsyncSession, user, items: list) -> list[RoadmapWeek]:
        uid = user.id if hasattr(user, "id") else user
        dict_items = [item.model_dump() if hasattr(item, "model_dump") else dict(item) for item in items]
        return await self.reorder_weeks_internal(db, uid, dict_items)

    async def create_task(self, db: AsyncSession, user, week_id: str, data: dict) -> RoadmapTask:
        uid = user.id if hasattr(user, "id") else user
        week = await roadmap_week_repository.get(db, id=week_id)
        if not week:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "WEEK_NOT_FOUND", "details": "Week not found"},
            )
        roadmap = await roadmap_repository.get(db, id=week.roadmap_id, user_id=uid)
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "ROADMAP_NOT_FOUND", "details": "Roadmap not found"},
            )
        tasks = await roadmap_task_repository.get_by_week(db, week_id)
        return await roadmap_task_repository.create(
            db,
            week_id=week_id,
            task_text=data["task_text"],
            category=data.get("category", "study"),
            time_estimate=data.get("time_estimate", 60),
            sort_order=len(tasks),
        )

    async def update_task(self, db: AsyncSession, user, task_id: str, request) -> RoadmapTask:
        data = request.model_dump(exclude_unset=True) if hasattr(request, "model_dump") else dict(request)
        task = await roadmap_task_repository.get(db, id=task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "TASK_NOT_FOUND", "details": "Roadmap task not found"},
            )
        return await roadmap_task_repository.update(db, task, **data)

    async def delete_task(self, db: AsyncSession, user, task_id: str) -> None:
        uid = user.id if hasattr(user, "id") else user
        task = await roadmap_task_repository.get(db, id=task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "TASK_NOT_FOUND", "details": "Roadmap task not found"},
            )
        week = await roadmap_week_repository.get(db, id=task.week_id)
        if week:
            roadmap = await roadmap_repository.get(db, id=week.roadmap_id, user_id=uid)
            if not roadmap:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "Not Found", "code": "ROADMAP_NOT_FOUND", "details": "Roadmap not found"},
                )
        await roadmap_task_repository.delete(db, task)


async def sync_active_week(
    db: AsyncSession,
    user_id: str,
    goal_id: str,
    today: date | None = None,
) -> None:
    if today is None:
        today = date.today()
    goal = await goal_repository.get(db, id=goal_id, user_id=user_id)
    if not goal:
        return
    query = (
        select(RoadmapWeek)
        .join(Roadmap, Roadmap.id == RoadmapWeek.roadmap_id)
        .where(
            Roadmap.user_id == user_id,
            Roadmap.goal_id == goal_id,
            Roadmap.is_active == True,
        )
    )
    result = await db.execute(query)
    weeks = list(result.scalars().all())
    for week in weeks:
        sd = week.start_date
        if sd is None:
            sd = get_week_start_from_goal(goal.start_date, week.week_number)
            week.start_date = sd
        if isinstance(sd, str):
            try:
                sd = date.fromisoformat(sd)
            except (ValueError, TypeError):
                continue
        week_end = sd + timedelta(days=6)
        if week_end < today:
            week.status = "done"
        elif sd <= today <= week_end:
            week.status = "active"
        else:
            week.status = "pending"
    await db.flush()


async def get_weeks_for_goal(db: AsyncSession, goal_id: str, user_id: str) -> list[RoadmapWeek]:
    query = (
        select(RoadmapWeek)
        .join(Roadmap, Roadmap.id == RoadmapWeek.roadmap_id)
        .where(
            Roadmap.user_id == user_id,
            Roadmap.goal_id == goal_id,
            Roadmap.is_active == True,
        )
        .order_by(RoadmapWeek.week_number)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


roadmap_service = RoadmapService()
