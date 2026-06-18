from __future__ import annotations

from datetime import date, datetime, timezone

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal
from app.repositories.goal import goal_repository
from app.repositories.user import user_repository


class GoalService:
    async def create_goal(self, db: AsyncSession, user_id: str, data: dict) -> Goal:
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "USER_NOT_FOUND", "details": "User not found"},
            )
        active = await goal_repository.get_active_by_user(db, user_id)
        if active:
            active.is_active = False
            await db.flush()
        start_date = data.get("start_date", date.today())
        duration = data["duration_months"]
        target_date = start_date + relativedelta(months=+duration)
        goal = await goal_repository.create(
            db,
            user_id=user_id,
            goal_text=data["goal_text"],
            target_company=data["target_company"],
            target_role=data["target_role"],
            duration_months=duration,
            daily_study_hours=data["daily_study_hours"],
            skill_level=data["skill_level"],
            weak_areas=data.get("weak_areas", []),
            start_date=start_date,
            target_date=target_date,
        )
        return goal

    async def update_goal(self, db: AsyncSession, goal_id: str, user_id: str, data: dict) -> Goal:
        goal = await goal_repository.get(db, id=goal_id, user_id=user_id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "GOAL_NOT_FOUND", "details": "Goal not found"},
            )
        update_data = {}
        for key in ("goal_text", "target_company", "target_role", "daily_study_hours", "skill_level", "weak_areas"):
            if key in data:
                update_data[key] = data[key]
        if "duration_months" in data:
            update_data["duration_months"] = data["duration_months"]
            update_data["target_date"] = goal.start_date + relativedelta(months=+data["duration_months"])
        goal = await goal_repository.update(db, goal, **update_data)
        return goal

    async def delete_goal(self, db: AsyncSession, goal_id: str, user_id: str) -> None:
        goal = await goal_repository.get(db, id=goal_id, user_id=user_id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "GOAL_NOT_FOUND", "details": "Goal not found"},
            )
        await goal_repository.delete(db, goal)

    async def create(self, db: AsyncSession, user, request) -> Goal:
        data = request.model_dump() if hasattr(request, "model_dump") else dict(request)
        return await self.create_goal(db, user.id if hasattr(user, "id") else user, data)

    async def get_active(self, db: AsyncSession, user) -> Goal | None:
        uid = user.id if hasattr(user, "id") else user
        return await goal_repository.get_active_by_user(db, uid)

    async def update(self, db: AsyncSession, user, goal_id: str, request) -> Goal:
        data = request.model_dump(exclude_unset=True) if hasattr(request, "model_dump") else dict(request)
        uid = user.id if hasattr(user, "id") else user
        return await self.update_goal(db, goal_id, uid, data)

    async def delete(self, db: AsyncSession, user, goal_id: str) -> None:
        uid = user.id if hasattr(user, "id") else user
        return await self.delete_goal(db, goal_id, uid)


goal_service = GoalService()
