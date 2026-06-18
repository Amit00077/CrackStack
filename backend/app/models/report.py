from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import List

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed_rate: Mapped[float] = mapped_column(Float, default=0.0)
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    streak_health: Mapped[int] = mapped_column(Integer, default=0)
    letter_grade: Mapped[str] = mapped_column(String(2), nullable=False, default="F")
    verdict: Mapped[str] = mapped_column(String(20), nullable=False, default="behind")
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    strengths: Mapped[List[str]] = mapped_column(JSONB, default=[])
    improvement_areas: Mapped[List[str]] = mapped_column(JSONB, default=[])
    recommendations: Mapped[List[str]] = mapped_column(JSONB, default=[])
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uq_user_week_start"),
    )