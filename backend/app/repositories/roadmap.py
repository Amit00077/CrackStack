from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.roadmap import Roadmap, RoadmapWeek, RoadmapTask
from app.repositories.base import BaseRepository


class RoadmapRepository(BaseRepository[Roadmap]):
    def __init__(self):
        super().__init__(Roadmap)

    async def get_active_by_user(self, db: AsyncSession, user_id: str) -> Roadmap | None:
        query = select(Roadmap).filter_by(user_id=user_id, is_active=True)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_with_weeks(self, db: AsyncSession, roadmap_id: str) -> Roadmap | None:
        query = (
            select(Roadmap)
            .options(joinedload(Roadmap.weeks))
            .filter_by(id=roadmap_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


class RoadmapWeekRepository(BaseRepository[RoadmapWeek]):
    def __init__(self):
        super().__init__(RoadmapWeek)

    async def get_by_roadmap(self, db: AsyncSession, roadmap_id: str, order_by_sort: bool = True) -> list[RoadmapWeek]:
        query = select(RoadmapWeek).filter_by(roadmap_id=roadmap_id)
        if order_by_sort:
            query = query.order_by(RoadmapWeek.sort_order)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def reorder(self, db: AsyncSession, items: list[dict]) -> list[RoadmapWeek]:
        for item in items:
            await db.execute(
                update(RoadmapWeek)
                .where(RoadmapWeek.id == item["id"])
                .values(sort_order=item["sort_order"])
            )
        await db.flush()
        ids = [item["id"] for item in items]
        result = await db.execute(select(RoadmapWeek).where(RoadmapWeek.id.in_(ids)))
        return list(result.scalars().all())


class RoadmapTaskRepository(BaseRepository[RoadmapTask]):
    def __init__(self):
        super().__init__(RoadmapTask)

    async def get_by_week(self, db: AsyncSession, week_id: str) -> list[RoadmapTask]:
        query = select(RoadmapTask).filter_by(week_id=week_id).order_by(RoadmapTask.sort_order)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def bulk_create(self, db: AsyncSession, week_id: str, tasks: list[dict]) -> list[RoadmapTask]:
        created = []
        for i, task_data in enumerate(tasks):
            task = RoadmapTask(
                week_id=week_id,
                task_text=task_data["task_text"],
                category=task_data.get("category", "study"),
                time_estimate=task_data.get("time_estimate", 60),
                sort_order=task_data.get("sort_order", i),
            )
            db.add(task)
            created.append(task)
        await db.flush()
        for task in created:
            await db.refresh(task)
        return created

    async def count_by_week(self, db: AsyncSession, week_id: str) -> int:
        query = select(func.count()).select_from(RoadmapTask).filter_by(week_id=week_id)
        result = await db.execute(query)
        return result.scalar() or 0

    async def delete_by_week(self, db: AsyncSession, week_id: str) -> None:
        query = select(RoadmapTask).filter_by(week_id=week_id)
        result = await db.execute(query)
        tasks = result.scalars().all()
        for task in tasks:
            await db.delete(task)
        await db.flush()


roadmap_repository = RoadmapRepository()
roadmap_week_repository = RoadmapWeekRepository()
roadmap_task_repository = RoadmapTaskRepository()
