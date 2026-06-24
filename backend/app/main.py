from __future__ import annotations

import logging
from datetime import timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import admin, auth, chat, dashboard, goals, health, notifications, onboarding, reports, roadmap, tasks, users
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.core.rate_limit import setup_rate_limiting
from app.core.redis import close_redis
from app.tasks.scheduler import setup_scheduler

from app.core.database import async_session_factory
from app.core.seed_providers import seed_default_providers
from app.models.goal import Goal
from app.models.roadmap import Roadmap, RoadmapWeek
from app.models.user import User
from app.services.roadmap import sync_active_week
from app.utils.timezone import get_week_start_from_goal
from sqlalchemy import select


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(level=settings.LOG_LEVEL, fmt=settings.LOG_FORMAT)
    setup_scheduler()
    try:
        async with async_session_factory() as db:
            logger = logging.getLogger(__name__)
            await seed_default_providers(db)
            result = await db.execute(
                select(RoadmapWeek).where(RoadmapWeek.start_date.is_(None))
            )
            null_start_weeks = list(result.scalars().all())
            for week in null_start_weeks:
                roadmap = await db.get(Roadmap, week.roadmap_id)
                if roadmap and roadmap.goal_id:
                    goal = await db.get(Goal, roadmap.goal_id)
                    if goal:
                        week.start_date = get_week_start_from_goal(goal.start_date, week.week_number)
            if null_start_weeks:
                await db.flush()
            result = await db.execute(
                select(RoadmapTask).where(RoadmapTask.assigned_date.is_(None), RoadmapTask.week_id.isnot(None))
            )
            null_date_tasks = list(result.scalars().all())
            for task in null_date_tasks:
                week = await db.get(RoadmapWeek, task.week_id)
                if week and week.start_date:
                    day = task.sort_order % 7
                    task.assigned_date = week.start_date + timedelta(days=day)
                    task.day_offset = day + 1
            for goal in (await db.execute(select(Goal).where(Goal.is_active == True))).scalars().all():
                await sync_active_week(db, goal.user_id, goal.id)
            if settings.ADMIN_EMAIL:
                result = await db.execute(
                    select(User).where(User.email == settings.ADMIN_EMAIL)
                )
                admin_user = result.scalar_one_or_none()
                if admin_user and not admin_user.is_superuser:
                    admin_user.is_superuser = True
                    logger.info("Promoted %s to superuser", settings.ADMIN_EMAIL)
            await db.commit()
    except Exception as exc:
        logger = logging.getLogger(__name__)
        logger.warning("Startup initialization error: %s", exc)
    yield
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_rate_limiting(app)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "code": "INTERNAL_ERROR",
            "details": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(goals.router, prefix="/api/v1")
app.include_router(roadmap.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(onboarding.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
