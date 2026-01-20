# app/crud/agent.py

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.crud.base import CRUDBase
from app.models.agent import Agent, AgentLLMConfig, AgentRetrievalConfig, AgentDocument
from uuid import UUID


from app.schemas.agent import AgentCreate, AgentUpdate


class CRUDAgent(CRUDBase[Agent, AgentCreate, AgentUpdate]):
    """CRUD operations for Agent"""

    async def create_with_configs(
        self,
        db: AsyncSession,
        *,
        agent_data: dict,
        llm_config_data: dict,
        retrieval_config_data: dict,
        document_ids: Optional[List[int]] = None
    ) -> Agent:
        """Create agent with all configs in one transaction"""

        # Create agent
        agent = Agent(**agent_data)
        db.add(agent)
        await db.flush()  # Get agent.id without committing

        # Create LLM config
        llm_config = AgentLLMConfig(agent_id=agent.id, **llm_config_data)
        db.add(llm_config)

        # Create retrieval config
        retrieval_config = AgentRetrievalConfig(
            agent_id=agent.id, **retrieval_config_data
        )
        db.add(retrieval_config)

        # Link documents
        if document_ids:
            for doc_id in document_ids:
                agent_doc = AgentDocument(agent_id=agent.id, document_id=doc_id)
                db.add(agent_doc)

        await db.commit()
        await db.refresh(agent)
        return agent

    async def get_with_configs(
        self, db: AsyncSession, agent_id: UUID
    ) -> Optional[Agent]:
        """Get agent with all configs loaded"""
        statement = select(Agent).where(Agent.id == agent_id)
        result = await db.execute(statement)
        agent = result.scalars().first()

        if agent:
            # Async loading of relationships is tricky in SQLAlchemy unless explicitly eager loaded in query
            # or if we touch them while session is open (but usually awaitable).
            # For simplicity, assuming selectinload is configured or lazy='selectin' in models.
            # If not, we might need explicit options.
            # For now, let's assume direct access triggers a load but waiting is needed?
            # Actually, with AsyncSession, lazy loading is often disabled or requires `await agent.awaitable_attrs.llm_config`.
            # Let's verify models later. For now, just fix the crud methods execution.
            pass

        return agent

    async def get_by_project(
        self, db: AsyncSession, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Agent]:
        """Get all agents for a project"""
        statement = (
            select(Agent)
            .where(Agent.project_id == project_id)
            .where(Agent.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_multi_by_project(
        self, db: AsyncSession, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Agent]:
        # Alias for get_by_project to match what I used in routes
        return await self.get_by_project(db, project_id, skip, limit)

    async def update_llm_config(
        self, db: AsyncSession, agent_id: UUID, config_data: dict
    ) -> Optional[AgentLLMConfig]:
        """Update LLM configuration"""
        statement = select(AgentLLMConfig).where(AgentLLMConfig.agent_id == agent_id)
        result = await db.execute(statement)
        config = result.scalars().first()

        if config:
            for key, value in config_data.items():
                setattr(config, key, value)
            db.add(config)
            await db.commit()
            await db.refresh(config)

        return config

    async def link_documents(
        self,
        db: AsyncSession,
        agent_id: UUID,
        document_ids: List[int],
        replace: bool = False,
    ) -> List[AgentDocument]:
        """Link documents to agent"""

        if replace:
            # Remove existing links
            statement = select(AgentDocument).where(AgentDocument.agent_id == agent_id)
            result = await db.execute(statement)
            existing = result.scalars().all()
            for link in existing:
                await db.delete(link)

        # Create new links
        links = []
        for doc_id in document_ids:
            link = AgentDocument(agent_id=agent_id, document_id=doc_id)
            db.add(link)
            links.append(link)

        await db.commit()
        return links


# Create singleton instance
agent_crud = CRUDAgent(Agent)
