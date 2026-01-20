# app/api/routes/chats.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import List, Optional, Any
from uuid import UUID

from app.api.deps import SessionDep, CurrentUser
from app.crud.chat import chat_session_crud, chat_message_crud, chat_feedback_crud
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionDetail,
    ChatSessionUpdate,
    ChatFeedbackCreate,
    ChatFeedbackResponse,
    ChatRequest,
    ChatResponse,
)

router = APIRouter()

# ============================================================================
# Sessions
# ============================================================================


@router.post(
    "/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_session(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    session_in: ChatSessionCreate,
) -> Any:
    """Create new chat session"""
    # Verify project access (TODO: Implement granular permissions)

    session = await chat_session_crud.create_session(
        db=db,
        user_id=current_user.id,
        project_id=session_in.project_id,
        agent_id=session_in.agent_id,
        title=session_in.title,
    )
    return session


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_sessions(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    project_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """Get all chat sessions for the current user"""
    return await chat_session_crud.get_user_sessions(
        db=db, user_id=current_user.id, project_id=project_id, skip=skip, limit=limit
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_session(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    session_id: UUID,
) -> Any:
    """Get chat session by ID with messages"""
    session = await chat_session_crud.get(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this session"
        )

    # Get messages
    messages = await chat_message_crud.get_session_messages(db, session_id)

    # Combine results
    # Ideally should be done in CRUD/Model but for now explicit composition
    session_detail = ChatSessionDetail.model_validate(session)
    session_detail.messages = messages

    return session_detail


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    session_id: UUID,
    session_in: ChatSessionUpdate,
) -> Any:
    """Update chat session"""
    session = await chat_session_crud.get(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this session"
        )

    session = await chat_session_crud.update(db, db_obj=session, obj_in=session_in)
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    session_id: UUID,
) -> None:
    """Delete chat session"""
    session = await chat_session_crud.get(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this session"
        )

    await chat_session_crud.remove(db, id=session_id)
    return None


# ============================================================================
# Messages
# ============================================================================


@router.post("/messages", response_model=ChatResponse)
async def send_message(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    chat_request: ChatRequest,
) -> Any:
    """
    Send a message to an agent and get a response.
    NOTE: content generation logic missing here, just placeholder for structure.
    """
    # 1. Get or Create Session
    if chat_request.session_id:
        session = await chat_session_crud.get(db, chat_request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        raise HTTPException(status_code=400, detail="session_id is required")

    # 2. Save User Message
    user_msg = await chat_message_crud.create_message(
        db, session_id=session.id, role="user", content=chat_request.message
    )

    # 3. Trigger Agent (Mock for now)
    # TODO: Integrate with actual Agent Runner / LLM Service
    agent_response_content = (
        f"Echo: {chat_request.message} (Agent {chat_request.agent_id})"
    )

    agent_msg = await chat_message_crud.create_message(
        db,
        session_id=session.id,
        role="assistant",
        content=agent_response_content,
        model_name="mock-model",
        tokens_used=10,
        latency_ms=100,
    )

    return ChatResponse(
        session_id=session.id,
        message_id=agent_msg.id,
        content=agent_response_content,
        sources=[],
        model_name="mock-model",
        tokens_used=10,
        latency_ms=100,
    )


@router.post("/messages/{message_id}/feedback", response_model=ChatFeedbackResponse)
async def submit_feedback(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    message_id: UUID,
    feedback: ChatFeedbackCreate,
) -> Any:
    """Submit feedback for a message"""
    # Verify message ownership
    message = await chat_message_crud.get(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    session = await chat_session_crud.get(db, message.session_id)
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return await chat_feedback_crud.create_or_update_feedback(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
        feedback_data=feedback.model_dump(exclude={"message_id"}),
    )
