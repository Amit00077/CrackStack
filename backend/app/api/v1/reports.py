from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.report import PaginatedReportsResponse, ReportGenerateResponse, WeeklyReportResponse
from app.services.report import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=ReportGenerateResponse)
async def generate_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportGenerateResponse:
    report = await report_service.generate(db, current_user)
    return ReportGenerateResponse(message="Report generated successfully", report_id=report.id)


@router.get("/latest", response_model=WeeklyReportResponse)
async def get_latest_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WeeklyReportResponse:
    report = await report_service.get_current(db, current_user)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Not Found", "code": "REPORT_NOT_FOUND", "details": "No current report found"},
        )
    return WeeklyReportResponse.model_validate(report)


@router.get("/current", response_model=WeeklyReportResponse)
async def get_current_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WeeklyReportResponse:
    report = await report_service.get_current(db, current_user)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Not Found", "code": "REPORT_NOT_FOUND", "details": "No current report found"},
        )
    return WeeklyReportResponse.model_validate(report)


@router.get("/history", response_model=PaginatedReportsResponse)
async def get_report_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedReportsResponse:
    reports, total = await report_service.get_history(db, current_user, page=page, limit=limit)
    return PaginatedReportsResponse(
        items=[WeeklyReportResponse.model_validate(r) for r in reports],
        total=total,
        page=page,
        limit=limit,
        pages=max(1, (total + limit - 1) // limit),
    )