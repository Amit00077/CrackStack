from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.goal import goal_repository
from app.repositories.progress import progress_repository
from app.repositories.task import daily_task_repository
from app.services.task import task_service


class DashboardService:
    async def get_dashboard(self, db: AsyncSession, user_id: str) -> dict:
        today = date.today()
        goal = await goal_repository.get_active_by_user(db, user_id)
        streak_obj = await progress_repository.get_streak(db, user_id)
        snapshots = await progress_repository.get_recent_snapshots(db, user_id, days=30)
        today_tasks_db = await daily_task_repository.get_today(db, user_id, today)
        if not today_tasks_db:
            try:
                today_tasks_db = await task_service.assign_weekly_tasks(db, user_id)
            except Exception:
                today_tasks_db = []

        if goal:
            active_goal = {
                "id": goal.id,
                "goal_text": goal.goal_text,
                "target_company": goal.target_company,
                "target_role": goal.target_role,
            }
            days_elapsed = (today - goal.start_date).days
            total_days = (goal.target_date - goal.start_date).days
            time_progress = min(days_elapsed / total_days, 1.0) if total_days > 0 else 0
        else:
            active_goal = None
            time_progress = 0

        total_tasks = 0
        total_done = 0
        total_study = 0
        snap_count = len(snapshots)

        for s in snapshots:
            total_tasks += s.tasks_total
            total_done += s.tasks_completed
            total_study += s.study_time_minutes

        task_progress = total_done / total_tasks if total_tasks > 0 else 0
        overall_progress = max(time_progress, task_progress)
        completion_rate = round(overall_progress * 100, 1)

        avg_study_time = round(total_study / snap_count, 1) if snap_count > 0 else 0

        categories = await daily_task_repository.get_category_stats(
            db, user_id, today - timedelta(days=29), today
        )
        cat_total = len(categories)
        cat_done = sum(1 for c in categories if c["completed"] > 0)
        topic_cov = round(cat_done / cat_total, 4) if cat_total > 0 else 0

        current_streak = streak_obj.current_streak if streak_obj else 0
        best_streak = streak_obj.best_streak if streak_obj else 0

        today_tasks = [
            {
                "id": t.id,
                "title": t.task_text,
                "is_completed": t.is_done,
                "task_type": t.category,
                "duration_minutes": t.time_estimate,
            }
            for t in today_tasks_db
        ]

        heatmap = []
        seen = {s.snapshot_date: s for s in snapshots}
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            s = seen.get(d)
            heatmap.append({
                "date": d.isoformat(),
                "tasks_completed": s.tasks_completed if s else 0,
                "tasks_total": s.tasks_total if s else 0,
                "study_time_minutes": s.study_time_minutes if s else 0,
            })

        return {
            "overall_progress": round(overall_progress, 4),
            "current_day": max(0, (today - goal.start_date).days) if goal else 0,
            "streak": {
                "current_streak": current_streak,
                "best_streak": best_streak,
                "last_active_date": streak_obj.last_active_date.isoformat() if streak_obj and streak_obj.last_active_date else None,
            },
            "total_solved": total_done,
            "avg_study_time": avg_study_time,
            "topic_coverage": {"completed": cat_done, "total": cat_total, "categories": categories},
            "activity_heatmap": heatmap,
            "today_tasks": today_tasks,
            "active_goal": active_goal,
            "completion_rate": completion_rate,
            "streak_days": current_streak,
            "total_study_hours": round(total_study / max(snap_count, 1), 1),
        }

    async def get_streak(self, db: AsyncSession, user_id: str) -> dict:
        streak_obj = await progress_repository.get_streak(db, user_id)
        if not streak_obj:
            return {"current_streak": 0, "best_streak": 0, "last_active_date": None}
        return {
            "current_streak": streak_obj.current_streak,
            "best_streak": streak_obj.best_streak,
            "last_active_date": streak_obj.last_active_date.isoformat() if streak_obj.last_active_date else None,
        }


dashboard_service = DashboardService()
