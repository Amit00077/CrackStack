from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai import get_active_ai_client
from app.core.config import settings
from app.models.daily_task import DailyTask
from app.models.report import WeeklyReport
from app.repositories.goal import goal_repository
from app.repositories.progress import progress_repository
from app.repositories.report import weekly_report_repository
from app.repositories.task import daily_task_repository
from app.repositories.user import user_repository

logger = logging.getLogger(__name__)


async def _call_report_ai(prompt: str, db: AsyncSession) -> dict:
    client, model, max_tokens = await get_active_ai_client(db)
    if not client:
        logger.warning("No active AI provider, using fallback report")
        return _fallback_report()

    system_msg = (
        "You are a weekly study report analyst. "
        "Return ONLY valid JSON matching this schema: "
        '{"summary": str, "feedback": str, '
        '"strengths": [str], "improvement_areas": [str], '
        '"recommendations": [str]}'
    )

    try:
        kwargs: dict[str, Any] = dict(
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
        return parsed
    except Exception as exc:
        logger.warning("Report AI call failed, using fallback: %s", exc)
        return _fallback_report()


def _fallback_report() -> dict:
    return {
        "summary": "You made progress this week. Keep up the momentum and focus on your weak areas.",
        "feedback": "Consider increasing study time on challenging topics. Review concepts you found difficult.",
        "strengths": ["Consistency", "Task completion"],
        "improvement_areas": ["Advanced topics", "Practice frequency"],
        "recommendations": [
            "Set aside dedicated time for difficult topics",
            "Review completed tasks weekly",
            "Practice with mock tests",
        ],
    }


def _compute_letter_grade(rate: float) -> str:
    if rate >= 90:
        return "A"
    if rate >= 80:
        return "B"
    if rate >= 70:
        return "C"
    if rate >= 60:
        return "D"
    return "F"


def _compute_verdict(rate: float, week_number: int, expected_weeks: int) -> str:
    expected_progress = (week_number / max(expected_weeks, 1)) * 100
    if rate >= expected_progress:
        return "ahead"
    if rate >= expected_progress * 0.8:
        return "on_track"
    return "behind"


class ReportService:
    async def generate_report(self, db: AsyncSession, user_id: str) -> WeeklyReport:
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "USER_NOT_FOUND", "details": "User not found"},
            )

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        goal = await goal_repository.get_active_by_user(db, user_id)
        week_number = 1
        expected_weeks = 4
        if goal:
            days_since_start = (today - goal.start_date).days if goal.start_date else 0
            week_number = max(1, (days_since_start // 7) + 1)
            expected_weeks = goal.duration_months * 4 if goal.duration_months else 4

        tasks = await daily_task_repository.get_by_date_range(db, user_id, week_start, today)
        total = len(tasks)
        done = sum(1 for t in tasks if t.is_done)
        completed_rate = (done / total * 100) if total > 0 else 0.0

        category_stats: dict[str, dict[str, int]] = {}
        for t in tasks:
            cat = t.category or "general"
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "done": 0}
            category_stats[cat]["total"] += 1
            if t.is_done:
                category_stats[cat]["done"] += 1

        streak_obj = await progress_repository.get_streak(db, user_id)
        streak_health = streak_obj.current_streak if streak_obj else 0

        study_time_query = select(func.coalesce(func.sum(DailyTask.time_estimate), 0)).where(
            DailyTask.user_id == user_id,
            DailyTask.task_date >= week_start,
            DailyTask.task_date <= today,
        )
        study_result = await db.execute(study_time_query)
        total_study_time = study_result.scalar() or 0

        snapshots = await progress_repository.get_recent_snapshots(db, user_id, days=7)
        avg_study_time = round(
            sum(s.study_time_minutes for s in snapshots) / max(len(snapshots), 1), 1
        )

        readiness_score = round(
            completed_rate * 0.5
            + min(streak_health * 10, 100) * 0.2
            + min(total_study_time / 60, 100) * 0.15
            + min(avg_study_time * 2, 100) * 0.15
        )

        letter_grade = _compute_letter_grade(completed_rate)
        verdict = _compute_verdict(completed_rate, week_number, expected_weeks)

        prompt = self._build_prompt(
            goal, completed_rate, streak_health, readiness_score, letter_grade,
            verdict, week_number, expected_weeks, category_stats, total_study_time,
            avg_study_time,
        )
        ai_client, _, _ = await get_active_ai_client(db)
        ai_generated = ai_client is not None
        try:
            ai_result = await _call_report_ai(prompt, db)
        except Exception as exc:
            logger.warning("Report AI call failed: %s", exc)
            ai_result = _fallback_report()

        existing = await weekly_report_repository.get_by_week(db, user_id, week_start)
        if existing:
            existing.week_end = week_end
            existing.week_number = week_number
            existing.completed_rate = round(completed_rate, 4)
            existing.readiness_score = round(readiness_score, 2)
            existing.streak_health = streak_health
            existing.letter_grade = letter_grade
            existing.verdict = verdict
            existing.completed_tasks = done
            existing.total_tasks = total
            existing.strengths = ai_result.get("strengths", [])
            existing.improvement_areas = ai_result.get("improvement_areas", [])
            existing.recommendations = ai_result.get("recommendations", [])
            existing.ai_generated = ai_generated
            existing.summary = ai_result.get("summary", "")
            existing.ai_feedback = ai_result.get("feedback", "")
            await db.flush()
            await db.refresh(existing)
            report = existing
        else:
            report = await weekly_report_repository.create(
                db,
                user_id=user_id,
                week_start=week_start,
                week_end=week_end,
                week_number=week_number,
                completed_rate=round(completed_rate, 4),
                readiness_score=round(readiness_score, 2),
                streak_health=streak_health,
                letter_grade=letter_grade,
                verdict=verdict,
                completed_tasks=done,
                total_tasks=total,
                strengths=ai_result.get("strengths", []),
                improvement_areas=ai_result.get("improvement_areas", []),
                recommendations=ai_result.get("recommendations", []),
                ai_generated=ai_generated,
                summary=ai_result.get("summary", ""),
                ai_feedback=ai_result.get("feedback", ""),
            )

        await weekly_report_repository.unset_current(db, user_id)
        report.is_current = True
        await db.flush()
        await db.refresh(report)

        return report

    async def get_current_report(self, db: AsyncSession, user_id: str) -> WeeklyReport | None:
        return await weekly_report_repository.get_current(db, user_id)

    async def get_report_history(
        self, db: AsyncSession, user_id: str, page: int = 1, limit: int = 10
    ) -> tuple[list[WeeklyReport], int]:
        return await weekly_report_repository.get_history(db, user_id, page=page, limit=limit)

    def _build_prompt(
        self, goal, completed_rate: float, streak_health: int, readiness_score: float,
        letter_grade: str, verdict: str, week_number: int, expected_weeks: int,
        category_stats: dict, total_study_time: int, avg_study_time: float,
    ) -> str:
        goal_data = {
            "goal_text": goal.goal_text if goal else "N/A",
            "target_role": goal.target_role if goal else "N/A",
            "target_company": goal.target_company if goal else "N/A",
            "skill_level": goal.skill_level if goal else "N/A",
            "weak_areas": goal.weak_areas if goal else [],
        }
        return json.dumps({
            "goal": goal_data,
            "completed_rate": completed_rate,
            "letter_grade": letter_grade,
            "verdict": verdict,
            "week_number": week_number,
            "expected_weeks": expected_weeks,
            "streak_health": streak_health,
            "readiness_score": readiness_score,
            "total_study_time_minutes": total_study_time,
            "avg_study_time_minutes": avg_study_time,
            "category_stats": category_stats,
        })

    async def generate(self, db: AsyncSession, user) -> WeeklyReport:
        uid = user.id if hasattr(user, "id") else user
        return await self.generate_report(db, uid)

    async def get_current(self, db: AsyncSession, user) -> WeeklyReport | None:
        uid = user.id if hasattr(user, "id") else user
        return await self.get_current_report(db, uid)

    async def get_history(self, db: AsyncSession, user, page: int = 1, limit: int = 10) -> tuple[list[WeeklyReport], int]:
        uid = user.id if hasattr(user, "id") else user
        return await self.get_report_history(db, uid, page=page, limit=limit)


report_service = ReportService()