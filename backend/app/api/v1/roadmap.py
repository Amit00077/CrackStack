from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.roadmap import (
    ReorderRequest,
    RoadmapResponse,
    RoadmapTaskCreate,
    RoadmapTaskResponse,
    RoadmapTaskUpdate,
    RoadmapWeekCreate,
    RoadmapWeekResponse,
    RoadmapWeekUpdate,
)
from app.services.roadmap import roadmap_service

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.post("/generate", response_model=RoadmapResponse)
async def generate_roadmap(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoadmapResponse:
    roadmap = await roadmap_service.generate(db, current_user, body["goal_id"])
    return RoadmapResponse.model_validate(roadmap)


@router.get("", response_model=RoadmapResponse)
async def get_roadmap(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoadmapResponse:
    roadmap = await roadmap_service.get_active(db, current_user)
    if not roadmap:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Not Found", "code": "ROADMAP_NOT_FOUND", "details": "No active roadmap found"})
    return RoadmapResponse.model_validate(roadmap)


@router.post("/weeks", response_model=RoadmapWeekResponse, status_code=status.HTTP_201_CREATED)
async def create_week(
    request: RoadmapWeekCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoadmapWeekResponse:
    week = await roadmap_service.create_week(db, current_user, request)
    return RoadmapWeekResponse.model_validate(week)


@router.put("/weeks/{week_id}", response_model=RoadmapWeekResponse)
async def update_week(
    week_id: str,
    request: RoadmapWeekUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoadmapWeekResponse:
    week = await roadmap_service.update_week(db, current_user, week_id, request)
    return RoadmapWeekResponse.model_validate(week)


@router.delete("/weeks/{week_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_week(
    week_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await roadmap_service.delete_week(db, current_user, week_id)


@router.patch("/weeks/reorder")
async def reorder_weeks(
    request: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    await roadmap_service.reorder_weeks(db, current_user, request.items)
    return {"message": "Reordered"}


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roadmap(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await roadmap_service.delete(db, current_user)


@router.post("/weeks/{week_id}/tasks", response_model=RoadmapTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    week_id: str,
    request: RoadmapTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoadmapTaskResponse:
    data = request.model_dump()
    task = await roadmap_service.create_task(db, current_user, week_id, data)
    return RoadmapTaskResponse.model_validate(task)


@router.put("/tasks/{task_id}", response_model=RoadmapTaskResponse)
async def update_task(
    task_id: str,
    request: RoadmapTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoadmapTaskResponse:
    task = await roadmap_service.update_task(db, current_user, task_id, request)
    return RoadmapTaskResponse.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await roadmap_service.delete_task(db, current_user, task_id)
