from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatSessionResponse, ChatSessionWithMessagesResponse
from app.services.chat import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message")
async def chat_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return StreamingResponse(
        chat_service.stream_response(db, current_user, request.message, request.session_id),
        media_type="text/event-stream",
    )


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatSessionResponse]:
    sessions = await chat_service.get_sessions(db, current_user)
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionWithMessagesResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionWithMessagesResponse:
    session = await chat_service.get_session(db, current_user, session_id)
    return ChatSessionWithMessagesResponse.model_validate(session)


@router.post("/sessions/{session_id}/archive")
async def archive_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionResponse:
    session = await chat_service.archive_session(db, session_id, current_user.id if hasattr(current_user, "id") else current_user)
    return ChatSessionResponse.model_validate(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await chat_service.delete_session(db, current_user, session_id)
