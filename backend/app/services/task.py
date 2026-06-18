from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.daily_task import DailyTask
from app.models.goal import Goal
from app.models.roadmap import Roadmap, RoadmapWeek, RoadmapTask
from app.repositories.goal import goal_repository
from app.repositories.progress import progress_repository
from app.repositories.roadmap import roadmap_repository, roadmap_task_repository
from app.repositories.task import daily_task_repository
from app.repositories.user import user_repository

logger = logging.getLogger(__name__)


class TaskService:
    async def get_today_tasks(self, db: AsyncSession, user_id: str, task_date: date | None = None) -> list[DailyTask]:
        if task_date is None:
            task_date = date.today()
        return await daily_task_repository.get_today(db, user_id, task_date)

    async def create_task(self, db: AsyncSession, user_id: str, data: dict) -> DailyTask:
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "USER_NOT_FOUND", "details": "User not found"},
            )
        task = await daily_task_repository.create(
            db,
            user_id=user_id,
            task_text=data["task_text"],
            category=data.get("category", "study"),
            time_estimate=data.get("time_estimate", 60),
            task_date=data.get("task_date", date.today()),
            source=data.get("source", "ad-hoc"),
            week_id=data.get("week_id"),
            source_task_id=data.get("source_task_id"),
        )
        return task

    async def update_task(self, db: AsyncSession, task_id: str, user_id: str, data: dict) -> DailyTask:
        task = await daily_task_repository.get(db, id=task_id, user_id=user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "TASK_NOT_FOUND", "details": "Task not found"},
            )
        update_data = {}
        for key in ("task_text", "category", "time_estimate", "task_date", "sort_order", "is_done", "week_id"):
            if key in data:
                update_data[key] = data[key]
        return await daily_task_repository.update(db, task, **update_data)

    async def delete_task(self, db: AsyncSession, task_id: str, user_id: str) -> None:
        task = await daily_task_repository.get(db, id=task_id, user_id=user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "TASK_NOT_FOUND", "details": "Task not found"},
            )
        await daily_task_repository.delete(db, task)

    async def toggle_task(self, db: AsyncSession, task_id: str, user_id: str) -> DailyTask:
        task = await daily_task_repository.toggle(db, task_id, user_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "TASK_NOT_FOUND", "details": "Task not found"},
            )
        today = date.today()
        completed = await daily_task_repository.count_completed_today(db, user_id, today)
        total = await daily_task_repository.count_total_today(db, user_id, today)
        study_time = await daily_task_repository.get_total_study_time(db, user_id, today)
        await progress_repository.update_snapshot(
            db, user_id, today,
            tasks_completed=completed,
            tasks_total=total,
            study_time_minutes=study_time,
        )
        await progress_repository.update_streak(db, user_id, today)
        return task

    async def get_tasks_by_date_range(self, db: AsyncSession, user_id: str, start: date, end: date) -> list[DailyTask]:
        return await daily_task_repository.get_by_date_range(db, user_id, start, end)

    async def assign_weekly_tasks(self, db: AsyncSession, user_id: str) -> list[DailyTask]:
        return await self.generate_daily_tasks_for_week(db, user_id, auto_select_week=True)

    async def generate_daily_tasks_for_week(
        self, db: AsyncSession, user_id: str, week_id: str | None = None, auto_select_week: bool = False
    ) -> list[DailyTask]:
        roadmap = await roadmap_repository.get_active_by_user(db, user_id)
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "code": "NO_ACTIVE_ROADMAP", "details": "No active roadmap found"},
            )

        daily_hours = 2
        if roadmap.goal_id:
            q = select(Goal).filter_by(id=roadmap.goal_id)
            r = await db.execute(q)
            goal = r.scalar_one_or_none()
            if goal:
                daily_hours = goal.daily_study_hours

        query = (
            select(RoadmapWeek)
            .options(joinedload(RoadmapWeek.tasks))
            .filter_by(roadmap_id=roadmap.id)
            .order_by(RoadmapWeek.sort_order)
        )
        result = await db.execute(query)
        weeks = result.unique().scalars().all()
        if not weeks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "code": "NO_WEEKS", "details": "Roadmap has no weeks"},
            )

        target_week: RoadmapWeek
        if week_id:
            target_week = next((w for w in weeks if w.id == week_id), None)
            if not target_week:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "Not Found", "code": "WEEK_NOT_FOUND", "details": "Week not found in active roadmap"},
                )
        elif auto_select_week:
            today = date.today()
            days_since_start = 0
            if roadmap.goal_id:
                q = select(Goal).filter_by(id=roadmap.goal_id)
                r = await db.execute(q)
                goal = r.scalar_one_or_none()
                if goal:
                    days_since_start = (today - goal.start_date).days
            week_index = min(days_since_start // 7, len(weeks) - 1) if weeks else 0
            target_week = weeks[week_index]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "code": "WEEK_REQUIRED", "details": "Either week_id or auto_select_week must be provided"},
            )

        if not target_week.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "code": "WEEK_NO_START_DATE", "details": "Week has no start date"},
            )

        week_start = target_week.start_date
        week_end = target_week.start_date + timedelta(days=6)

        logger.info(f"Generating daily tasks for week {target_week.id} (week_number={target_week.week_number}), "
                    f"date range: {week_start} to {week_end}, roadmap_tasks_count={len(target_week.tasks)}, "
                    f"daily_hours={daily_hours}")

        existing = await daily_task_repository.get_by_date_range(db, user_id, week_start, week_end)
        existing_for_week = [t for t in existing if t.week_id == target_week.id and t.source == "roadmap"]
        logger.info(f"Found {len(existing)} total daily tasks in date range, "
                    f"{len(existing_for_week)} for this week (source=roadmap)")

        sorted_tasks = sorted(target_week.tasks, key=lambda t: t.sort_order)

        tasks_without_date = [rt for rt in sorted_tasks if not rt.assigned_date]
        for i, rt in enumerate(tasks_without_date):
            day = i % 7
            rt.assigned_date = week_start + timedelta(days=day)
            rt.day_offset = day + 1

        if len(existing_for_week) >= len(sorted_tasks):
            updated = False
            for rt in sorted_tasks:
                task_date = rt.assigned_date
                if not task_date or task_date < week_start or task_date > week_end:
                    task_date = week_start
                match = next((t for t in existing_for_week if t.source_task_id == rt.id), None)
                if match and match.task_date != task_date:
                    match.task_date = task_date
                    updated = True
            if updated:
                await db.flush()
            all_tasks = [t for t in existing if t.week_id == target_week.id]
            await self._fill_daily_target(db, user_id, target_week, week_start, week_end, all_tasks, daily_hours)
            return all_tasks

        created = []

        for rt in sorted_tasks:
            task_date = rt.assigned_date
            if not task_date or task_date < week_start or task_date > week_end:
                task_date = week_start

            existing_match = next((t for t in existing_for_week if t.source_task_id == rt.id), None)
            if existing_match:
                if existing_match.task_date != task_date:
                    existing_match.task_date = task_date
                    logger.info(f"Updated daily task {existing_match.id} date to {task_date}")
                    await db.flush()
                created.append(existing_match)
                continue

            existing_on_date = [t for t in existing if t.task_date == task_date]
            sort_order = rt.sort_order if rt.sort_order is not None else len(existing_on_date)

            logger.info(f"Creating daily task for roadmap task {rt.id} on {task_date}")
            task = await daily_task_repository.create(
                db,
                user_id=user_id,
                week_id=target_week.id,
                source_task_id=rt.id,
                task_text=rt.task_text,
                category=rt.category,
                time_estimate=rt.time_estimate,
                sort_order=sort_order,
                source="roadmap",
                task_date=task_date,
            )
            created.append(task)
            existing.append(task)
            existing_for_week.append(task)

        all_tasks = [t for t in existing if t.week_id == target_week.id]
        created += await self._fill_daily_target(db, user_id, target_week, week_start, week_end, all_tasks, daily_hours)

        today = date.today()
        today_tasks = [t for t in all_tasks if t.task_date == today]
        today_total = len(today_tasks)
        today_study = sum(t.time_estimate or 0 for t in today_tasks)
        await progress_repository.update_snapshot(
            db, user_id, today,
            tasks_completed=0,
            tasks_total=today_total,
            study_time_minutes=today_study,
        )
        logger.info(f"Created {len(created)} daily tasks for week {target_week.id}")
        return all_tasks

    async def _fill_daily_target(
        self, db: AsyncSession, user_id: str, week: RoadmapWeek,
        week_start: date, week_end: date, all_tasks: list[DailyTask],
        daily_hours: int,
    ) -> list[DailyTask]:
        await daily_task_repository.delete_by_week_and_source(
            db, user_id, week.id, "ad-hoc"
        )
        all_tasks[:] = [t for t in all_tasks if not (t.week_id == week.id and t.source == "ad-hoc")]
        daily_target = daily_hours * 60
        created = []
        week_title = week.title or "Study"
        for day_offset in range(7):
            day = week_start + timedelta(days=day_offset)
            if day > week_end:
                break
            day_tasks = [t for t in all_tasks if t.task_date == day]
            day_total = sum(t.time_estimate or 0 for t in day_tasks)
            if day_total >= daily_target:
                continue
            remaining = daily_target - day_total
            sort_order = len(day_tasks)
            while remaining >= 30:
                filler_minutes = min(remaining, 90)
                task = await daily_task_repository.create(
                    db, user_id=user_id, week_id=week.id,
                    task_text=f"Self-study: {week_title}",
                    category="study", time_estimate=filler_minutes,
                    sort_order=sort_order, source="ad-hoc", task_date=day,
                )
                created.append(task)
                all_tasks.append(task)
                remaining -= filler_minutes
                sort_order += 1
        if created:
            await db.flush()
        return created

    async def get_active_goal(self, db: AsyncSession, user_id: str) -> Goal | None:
        return await goal_repository.get_active_by_user(db, user_id)


task_service = TaskService()
