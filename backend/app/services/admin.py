from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.audit import audit_log_repository
from app.repositories.user import user_repository


class AdminService:
    async def get_audit_logs(self, db: AsyncSession, user_id: str | None = None, skip: int = 0, limit: int = 50) -> list:
        if user_id:
            return await audit_log_repository.get_by_user(db, user_id, skip=skip, limit=limit)
        return await audit_log_repository.get_all(db, skip=skip, limit=limit)

    async def log_action(
        self,
        db: AsyncSession,
        admin_user_id: str,
        action: str,
        resource: str,
        resource_id: str | None = None,
        details: str | None = None,
        ip_address: str | None = None,
    ):
        admin = await user_repository.get(db, id=admin_user_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "USER_NOT_FOUND", "details": "Admin user not found"},
            )
        return await audit_log_repository.log(
            db,
            user_id=admin_user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )


admin_service = AdminService()
