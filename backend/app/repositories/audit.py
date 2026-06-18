from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self):
        super().__init__(AuditLog)

    async def log(
        self,
        db: AsyncSession,
        user_id: str | None,
        action: str,
        resource: str,
        resource_id: str | None = None,
        details: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        return await self.create(
            db,
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )

    async def get_by_user(self, db: AsyncSession, user_id: str, skip: int = 0, limit: int = 50) -> list[AuditLog]:
        query = (
            select(AuditLog)
            .filter_by(user_id=user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 50) -> list[AuditLog]:
        query = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


audit_log_repository = AuditLogRepository()
