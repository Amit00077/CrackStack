from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.chat import ChatSession, ChatMessage
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSession]):
    def __init__(self):
        super().__init__(ChatSession)

    async def get_user_sessions(self, db: AsyncSession, user_id: str, include_archived: bool = False) -> list[ChatSession]:
        query = select(ChatSession).filter_by(user_id=user_id)
        if not include_archived:
            query = query.filter_by(is_archived=False)
        query = query.order_by(ChatSession.updated_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_with_messages(self, db: AsyncSession, session_id: str, user_id: str) -> ChatSession | None:
        query = (
            select(ChatSession)
            .options(joinedload(ChatSession.messages))
            .filter_by(id=session_id, user_id=user_id)
        )
        result = await db.execute(query)
        return result.unique().scalar_one_or_none()

    async def archive(self, db: AsyncSession, session_id: str, user_id: str) -> ChatSession | None:
        query = select(ChatSession).filter_by(id=session_id, user_id=user_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        if not session:
            return None
        session.is_archived = True
        await db.flush()
        await db.refresh(session)
        return session


class ChatMessageRepository(BaseRepository[ChatMessage]):
    def __init__(self):
        super().__init__(ChatMessage)

    async def get_by_session(self, db: AsyncSession, session_id: str, limit: int = 50) -> list[ChatMessage]:
        query = (
            select(ChatMessage)
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.created_at)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_message(self, db: AsyncSession, session_id: str, role: str, content: str, extra_metadata: dict | None = None) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            extra_metadata=extra_metadata,
        )
        db.add(message)
        await db.flush()
        await db.refresh(message)
        return message


chat_session_repository = ChatSessionRepository()
chat_message_repository = ChatMessageRepository()
