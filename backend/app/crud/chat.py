# app/crud/chat.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select, func, and_
from app.crud.base import CRUDBase
from app.models.chat import (
    ChatSession,
    ChatMessage,
    ChatContext,
    ChatFeedback,
    MessageRole,
    ChatSessionStatus,
)
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatMessageCreate,
    ChatFeedbackCreate,
    ChatFeedbackUpdate,
)
from pydantic import BaseModel


class CRUDChatSession(CRUDBase[ChatSession, ChatSessionCreate, ChatSessionUpdate]):
    """CRUD operations for chat sessions"""

    async def create_session(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        project_id: UUID,
        agent_id: UUID,
        title: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            user_id=user_id,
            project_id=project_id,
            agent_id=agent_id,
            title=title or "New Chat",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_with_messages(
        self, db: AsyncSession, session_id: UUID
    ) -> Optional[ChatSession]:
        """Get session with messages eager loaded"""
        statement = (
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .options(selectinload(ChatSession.messages))
        )
        result = await db.execute(statement)
        return result.scalars().first()

    async def get_user_sessions(
        self,
        db: AsyncSession,
        user_id: UUID,
        project_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ChatSession]:
        """Get all sessions for a user"""
        statement = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .where(ChatSession.status == ChatSessionStatus.ACTIVE)
            .order_by(ChatSession.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )

        if project_id:
            statement = statement.where(ChatSession.project_id == project_id)

        result = await db.execute(statement)
        return list(result.scalars().all())

    async def update_last_message_time(
        self, db: AsyncSession, session_id: UUID
    ) -> Optional[ChatSession]:
        """Update session's last message timestamp"""
        session = await self.get(db, session_id)
        if session:
            session.last_message_at = datetime.now(UTC)
            session.updated_at = datetime.now(UTC)
            session.message_count += 1
            db.add(session)
            await db.commit()
            await db.refresh(session)
        return session


class CRUDChatMessage(CRUDBase[ChatMessage, ChatMessageCreate, BaseModel]):
    """CRUD operations for chat messages"""

    async def create_message(
        self,
        db: AsyncSession,
        *,
        session_id: UUID,
        role: MessageRole,
        content: str,
        model_name: Optional[str] = None,
        tokens_used: Optional[int] = None,
        latency_ms: Optional[int] = None,
        cost_usd: Optional[float] = None
    ) -> ChatMessage:
        """Create a new message"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            model_name=model_name,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )
        db.add(message)
        await db.flush()

        # Update session
        await chat_session_crud.update_last_message_time(db, session_id)

        await db.commit()
        await db.refresh(message)
        return message

    async def get_session_messages(
        self, db: AsyncSession, session_id: UUID, limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get all messages for a session"""
        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )

        if limit:
            statement = statement.limit(limit)

        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_message_with_context(
        self, db: AsyncSession, message_id: UUID
    ) -> Optional[ChatMessage]:
        """Get message with contexts loaded"""
        message = await self.get(db, message_id)
        if message:
            # Relationship loading strategy needed if lazy
            pass
        return message


class CRUDChatContext(CRUDBase[ChatContext, BaseModel, BaseModel]):
    """CRUD operations for chat contexts"""

    async def add_contexts(
        self, db: AsyncSession, *, message_id: UUID, contexts: List[dict]
    ) -> List[ChatContext]:
        """Add multiple contexts for a message"""
        db_contexts = []

        for ctx in contexts:
            context = ChatContext(
                message_id=message_id,
                chunk_id=ctx["chunk_id"],
                project_id=ctx["project_id"],
                document_id=ctx["document_id"],
                similarity_score=ctx["similarity_score"],
                rank=ctx["rank"],
                retrieval_method=ctx.get("retrieval_method", "hybrid"),
                was_used=ctx.get("was_used", True),
            )
            db.add(context)
            db_contexts.append(context)

        # Update message sources count (fetch message first)
        statement = select(ChatMessage).where(ChatMessage.id == message_id)
        result = await db.execute(statement)
        message = result.scalars().first()

        if message:
            message.sources_count = len(contexts)
            db.add(message)

        await db.commit()
        return db_contexts


class CRUDChatFeedback(CRUDBase[ChatFeedback, ChatFeedbackCreate, ChatFeedbackUpdate]):
    """CRUD operations for chat feedback"""

    async def create_or_update_feedback(
        self, db: AsyncSession, *, message_id: UUID, user_id: UUID, feedback_data: dict
    ) -> ChatFeedback:
        """Create or update feedback for a message"""
        # Check if feedback exists
        statement = select(ChatFeedback).where(ChatFeedback.message_id == message_id)
        result = await db.execute(statement)
        feedback = result.scalars().first()

        if feedback:
            # Update existing
            for key, value in feedback_data.items():
                setattr(feedback, key, value)
            feedback.updated_at = datetime.now(UTC)
        else:
            # Create new
            feedback = ChatFeedback(
                message_id=message_id, user_id=user_id, **feedback_data
            )

        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        return feedback

    async def get_feedback_stats(
        self,
        db: AsyncSession,
        agent_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> dict:
        """Get aggregated feedback statistics"""
        # Build query
        statement = select(ChatFeedback)

        if agent_id or project_id:
            statement = statement.join(ChatMessage).join(ChatSession)
            if agent_id:
                statement = statement.where(ChatSession.agent_id == agent_id)
            if project_id:
                statement = statement.where(ChatSession.project_id == project_id)

        result = await db.execute(statement)
        feedbacks = result.scalars().all()

        # Aggregate
        stats = {
            "total": len(feedbacks),
            "thumbs_up": sum(1 for f in feedbacks if f.feedback_type == "thumbs_up"),
            "thumbs_down": sum(
                1 for f in feedbacks if f.feedback_type == "thumbs_down"
            ),
            "avg_rating": 0.0,
        }

        ratings = [f.rating for f in feedbacks if f.rating is not None]
        if ratings:
            stats["avg_rating"] = sum(ratings) / len(ratings)

        return stats


# Create singleton instances
chat_session_crud = CRUDChatSession(ChatSession)
chat_message_crud = CRUDChatMessage(ChatMessage)
chat_context_crud = CRUDChatContext(ChatContext)
chat_feedback_crud = CRUDChatFeedback(ChatFeedback)
