# app/api/routes/chats.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from typing import List, Optional, Any
from uuid import UUID
import json
import logging

from app.api import deps
from app.api.deps import SessionDep, CurrentUser
from app.crud.chat import chat_session_crud, chat_message_crud, chat_feedback_crud
from app.crud.agent import agent_crud
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
logger = logging.getLogger(__name__)

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
    # Verify project access
    await deps.check_project_access(db, session_in.project_id, current_user)

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
    if project_id:
        await deps.check_project_access(db, project_id, current_user)

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
    session = await chat_session_crud.get_with_messages(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this session"
        )

    return session


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
    Supports streaming via Server-Sent Events (SSE) if stream=True.
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

    from app.services.agent_service import AgentService
    agent_service = AgentService(db)

    # 3. Stream or Block
    if chat_request.stream:
        async def event_generator():
            accumulated_content = ""
            citations = []
            final_usage = {}
            
            try:
                async for event in agent_service.run_agent_stream(
                    agent_id=session.agent_id, query=chat_request.message, session_id=session.id
                ):
                    # Pass through event to client
                    yield f"data: {json.dumps(event)}\n\n"
                    
                    # Accumulate for DB save
                    if event["type"] == "content":
                        accumulated_content += event.get("data", "")
                    elif event["type"] == "citation":
                        citations = event.get("data", [])
                    elif event["type"] == "usage":
                        final_usage = event.get("data", {})
                
                # Save Assistant Message
                agent_msg = await chat_message_crud.create_message(
                    db,
                    session_id=session.id,
                    role="assistant",
                    content=accumulated_content,
                    model_name=final_usage.get("model_name"),
                    tokens_used=0, # Placeholder
                    latency_ms=final_usage.get("latency_ms", 0),
                )
                
                # Save Contexts
                if citations:
                    from app.crud.chat import chat_context_crud
                    await chat_context_crud.add_contexts(
                        db,
                        message_id=agent_msg.id,
                        contexts=[
                            {
                                "chunk_id": c["chunk_id"],
                                "project_id": session.project_id,
                                "document_id": UUID(c["document_id"]),
                                "similarity_score": c["similarity_score"],
                                "rank": i,
                                "retrieval_method": "hybrid",
                                "was_used": True,
                            }
                            for i, c in enumerate(citations)
                        ],
                    )
                
                # Send "done" event with message ID
                yield f"data: {json.dumps({'type': 'done', 'message_id': str(agent_msg.id)})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    else:
        # Blocking Mode
        try:
            run_result = await agent_service.run_agent(
                agent_id=session.agent_id, query=chat_request.message, session_id=session.id
            )

            agent_msg = await chat_message_crud.create_message(
                db,
                session_id=session.id,
                role="assistant",
                content=run_result.content,
                model_name=run_result.model_name,
                tokens_used=run_result.total_tokens,
                latency_ms=run_result.latency_ms,
            )

            # Save contexts/citations
            if run_result.citations:
                from app.crud.chat import chat_context_crud
                await chat_context_crud.add_contexts(
                    db,
                    message_id=agent_msg.id,
                    contexts=[
                        {
                            "chunk_id": c["chunk_id"],
                            "project_id": session.project_id,
                            "document_id": UUID(c["document_id"]),
                            "similarity_score": c["similarity_score"],
                            "rank": i,
                            "retrieval_method": "hybrid",
                            "was_used": True,
                        }
                        for i, c in enumerate(run_result.citations)
                    ],
                )

            return ChatResponse(
                session_id=session.id,
                message_id=agent_msg.id,
                content=run_result.content,
                sources=run_result.citations,
                model_name=run_result.model_name,
                tokens_used=run_result.total_tokens or 0,
                latency_ms=run_result.latency_ms,
            )
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


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


@router.get("/feedback/stats", response_model=dict)
async def get_feedback_stats(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    agent_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
) -> Any:
    """Get feedback statistics"""
    if project_id:
        await deps.check_project_access(db, project_id, current_user)
    
    if agent_id:
        agent = await agent_crud.get(db, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        await deps.check_project_access(db, agent.project_id, current_user)

    return await chat_feedback_crud.get_feedback_stats(
        db=db, agent_id=agent_id, project_id=project_id
    )
