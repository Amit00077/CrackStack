from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import user_repository
from app.schemas.user import UserUpdate


class UserService:
    async def get_profile(self, db: AsyncSession, user: User) -> User:
        return user

    async def update_profile(
        self, db: AsyncSession, user: User, update: UserUpdate
    ) -> User:
        return await user_repository.update(
            db, user, **update.model_dump(exclude_unset=True)
        )


    async def anonymize_account(self, db: AsyncSession, user: User) -> None:
        user.email = f"deleted-{user.id}@anonymous.com"
        user.full_name = "Deleted User"
        user.hashed_password = None
        user.is_active = False
        await db.flush()

    async def export_user_data(self, db: AsyncSession, user: User) -> dict:
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }


user_service = UserService()
