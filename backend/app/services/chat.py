from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai import get_active_ai_client
from app.models.chat import ChatSession, ChatMessage
from app.repositories.chat import chat_session_repository, chat_message_repository
from app.repositories.goal import goal_repository
from app.repositories.progress import progress_repository
from app.repositories.report import weekly_report_repository
from app.repositories.user import user_repository

logger = logging.getLogger(__name__)


async def stream_response(messages: list, db: AsyncSession) -> AsyncGenerator[str, None]:
    client, model, max_tokens = await get_active_ai_client(db)
    if not client:
        yield "AI chat is not configured. Please configure an AI provider in the admin panel."
        return

    try:
        kwargs = dict(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
            stream=True,
        )
        stream = await client.chat.completions.create(**kwargs)
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content
    except Exception as exc:
        logger.error("AI streaming call failed: %s", exc)
        yield f"Sorry, I encountered an error: {exc}"


class ChatService:
    async def create_session(self, db: AsyncSession, user_id: str, title: str | None = None) -> ChatSession:
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "USER_NOT_FOUND", "details": "User not found"},
            )
        if not title:
            title = "New Chat"
        return await chat_session_repository.create(db, user_id=user_id, title=title)

    async def get_user_sessions(self, db: AsyncSession, user_id: str, include_archived: bool = False) -> list[ChatSession]:
        return await chat_session_repository.get_user_sessions(db, user_id, include_archived=include_archived)

    async def get_session_by_id(self, db: AsyncSession, session_id: str, user_id: str) -> ChatSession:
        session = await chat_session_repository.get_with_messages(db, session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "SESSION_NOT_FOUND", "details": "Chat session not found"},
            )
        return session

    async def delete_session_by_id(self, db: AsyncSession, session_id: str, user_id: str) -> None:
        session = await chat_session_repository.get(db, id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "SESSION_NOT_FOUND", "details": "Chat session not found"},
            )
        await chat_session_repository.delete(db, session)

    async def send_message(self, db: AsyncSession, user_id: str, session_id: str, content: str) -> AsyncGenerator[str, None]:
        session = await chat_session_repository.get(db, id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "SESSION_NOT_FOUND", "details": "Chat session not found"},
            )
        await chat_message_repository.create_message(db, session_id, "user", content)
        context = await self.build_context(db, user_id)
        system_prompt = self._build_system_prompt(context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]
        full_response = ""
        async for chunk in stream_response(messages, db):
            full_response += chunk
            yield chunk
        await chat_message_repository.create_message(
            db, session_id, "assistant", full_response.strip(),
            extra_metadata={"context": context},
        )
        if session.title == "New Chat":
            session.title = content[:50]
            await db.flush()

    async def build_context(self, db: AsyncSession, user_id: str) -> dict:
        goal = await goal_repository.get_active_by_user(db, user_id)
        streak = await progress_repository.get_streak(db, user_id)
        return {
            "goal": {
                "goal_text": goal.goal_text if goal else None,
                "target_role": goal.target_role if goal else None,
                "target_company": goal.target_company if goal else None,
                "weak_areas": goal.weak_areas if goal else [],
                "duration_months": goal.duration_months if goal else None,
            },
            "streak": {
                "current": streak.current_streak if streak else 0,
                "best": streak.best_streak if streak else 0,
            },
        }

    async def archive_session(self, db: AsyncSession, session_id: str, user_id: str) -> ChatSession:
        session = await chat_session_repository.archive(db, session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "code": "SESSION_NOT_FOUND", "details": "Chat session not found"},
            )
        return session

    def _build_system_prompt(self, context: dict) -> str:
        return json.dumps({
            "role": "assistant",
            "type": "study_coach",
            "context": context,
        })


    async def stream_response(self, db: AsyncSession, user, message: str, session_id: str | None = None):
        uid = user.id if hasattr(user, "id") else user
        if not session_id:
            session = await self.create_session(db, uid)
            session_id = session.id
        yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
        async for chunk in self.send_message(db, uid, session_id, message):
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    async def get_sessions(self, db: AsyncSession, user):
        uid = user.id if hasattr(user, "id") else user
        return await self.get_user_sessions(db, uid)

    async def get_session(self, db: AsyncSession, user, session_id: str):
        uid = user.id if hasattr(user, "id") else user
        return await self.get_session_by_id(db, session_id, uid)

    async def delete_session(self, db: AsyncSession, user, session_id: str):
        uid = user.id if hasattr(user, "id") else user
        return await self.delete_session_by_id(db, session_id, uid)


chat_service = ChatService()
