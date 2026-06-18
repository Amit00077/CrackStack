from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai import get_active_ai_client

logger = logging.getLogger(__name__)


def _build_fallback_roadmap(duration_months: int) -> dict:
    weeks_per_phase = 4
    total_weeks = max(duration_months * 4, 4)
    phases = []
    week_num = 1

    phase_configs = [
        ("Foundation", "Build core understanding of fundamentals"),
        ("Skill Building", "Deepen knowledge through structured practice"),
        ("Advanced Topics", "Tackle complex concepts and real-world scenarios"),
        ("Revision & Mastery", "Consolidate learning with mock tests and review"),
    ]

    for phase_title, phase_desc in phase_configs:
        if week_num > total_weeks:
            break
        phase_weeks = []
        for i in range(min(weeks_per_phase, total_weeks - week_num + 1)):
            phase_weeks.append({
                "week_number": week_num,
                "title": f"{phase_title} - Week {i + 1}",
                "tasks": [
                    {"task_text": f"Review key {phase_title.lower()} topics", "category": "study", "time_estimate": 45},
                    {"task_text": "Practice with exercises and problems", "category": "practice", "time_estimate": 60},
                    {"task_text": "Track progress and adjust study plan", "category": "review", "time_estimate": 15},
                ],
            })
            week_num += 1
        phases.append({"title": phase_title, "description": phase_desc, "weeks": phase_weeks})

    remaining = total_weeks - week_num + 1
    if remaining > 0:
        extra_weeks = []
        for i in range(remaining):
            extra_weeks.append({
                "week_number": week_num,
                "title": f"Review Week {i + 1}",
                "tasks": [
                    {"task_text": "Review weak areas and past mistakes", "category": "review", "time_estimate": 45},
                    {"task_text": "Take a full-length mock test", "category": "mock_test", "time_estimate": 120},
                    {"task_text": "Analyze results and refine strategy", "category": "review", "time_estimate": 30},
                ],
            })
            week_num += 1
        phases.append({"title": "Final Review", "description": "Consolidate everything before the target date", "weeks": extra_weeks})

    return {"phases": phases}


FALLBACK_ROADMAP_CACHE: dict[int, dict] = {}


def _get_fallback_roadmap(duration_months: int) -> dict:
    if duration_months not in FALLBACK_ROADMAP_CACHE:
        FALLBACK_ROADMAP_CACHE[duration_months] = _build_fallback_roadmap(duration_months)
    return FALLBACK_ROADMAP_CACHE[duration_months]


async def _call_ai(system_prompt: str, user_prompt: str, db: AsyncSession, max_tokens: int = 2048) -> dict | None:
    client, model, default_max = await get_active_ai_client(db)
    if not client:
        logger.warning("No active AI provider for onboarding, using fallback")
        return None

    try:
        kwargs = dict(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        resp = await client.chat.completions.create(**kwargs)
        raw = resp.choices[0].message.content
        return json.loads(raw)
    except Exception as exc:
        logger.warning("AI onboarding call failed: %s", exc)
        return None


async def generate_onboarding_questions(goal: str, current_answers: dict) -> dict:
    return {"onboarding_complete": True, "questions": []}


async def evaluate_completion(goal: str, answers: dict) -> dict:
    return {"onboarding_complete": True}


async def generate_onboarding_roadmap(goal: str, all_answers: dict, db: AsyncSession) -> dict:
    system_prompt = """You are an expert preparation strategist that supports ANY preparation goal.
Generate a complete personalized preparation roadmap based on the user's goal and profile.

Rules:
1. Support ALL preparation goals (exams, interviews, certifications, skills, etc.).
2. Break roadmap into phases (Foundation, Building, Advanced, Revision).
3. Break phases into weekly plans.
4. Each week has 3-5 daily tasks appropriate for the goal.
5. Consider user's current level and available study time.
6. Include mock tests, practice sessions, and review cycles where relevant.
7. Duration is controlled by the number of months provided.
8. Return a roadmap that fits the exact duration.
9. Do NOT ask follow-up questions - infer what you can.

Return ONLY valid JSON matching:
{"phases": [{"title": str, "weeks": [{"week_number": int, "title": str, "tasks": [{"task_text": str, "category": "study"|"practice"|"project"|"review"|"mock_test", "time_estimate": int}]}]}]}"""

    user_prompt = f"""Goal:
{goal}

User Profile:
{json.dumps(all_answers, indent=2)}

Generate a complete preparation roadmap that fits the duration."""

    result = await _call_ai(system_prompt, user_prompt, db, 4096)
    if result and "phases" in result:
        return result
    duration = all_answers.get("duration_months", 3)
    logger.info("Using fallback roadmap for goal: %s", goal)
    return _get_fallback_roadmap(duration)
