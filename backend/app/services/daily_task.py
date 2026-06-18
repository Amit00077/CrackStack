from __future__ import annotations

from datetime import date

from app.models.user import User
from app.services.task import task_service as ts


def _user_id(user: User) -> str:
    return user.id


class DailyTaskService:
    async def get_today(self, db, user: User, task_date: date | None = None) -> list:
        uid = _user_id(user) if hasattr(user, "id") else user
        return await ts.get_today_tasks(db, uid, task_date)

    async def get_by_date_range(self, db, user: User, start_date: date | None, end_date: date | None) -> list:
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = start_date
        return await ts.get_tasks_by_date_range(db, _user_id(user), start_date, end_date)

    async def create(self, db, user: User, request) -> object:
        data = request.model_dump()
        data["task_date"] = data.pop("assigned_date", date.today())
        if data.get("is_ad_hoc"):
            data["source"] = "ad-hoc"
        return await ts.create_task(db, _user_id(user), data)

    async def toggle(self, db, user: User, task_id: str) -> object:
        return await ts.toggle_task(db, task_id, _user_id(user))

    async def update(self, db, user: User, task_id: str, request) -> object:
        data = request.model_dump(exclude_unset=True)
        if "assigned_date" in data:
            data["task_date"] = data.pop("assigned_date")
        return await ts.update_task(db, task_id, _user_id(user), data)

    async def delete(self, db, user: User, task_id: str) -> None:
        await ts.delete_task(db, task_id, _user_id(user))


daily_task_service = DailyTaskService()
