# app/crud/agent.py

from typing import List, Optional
from sqlmodel import Session, select
from app.crud.base import CRUDBase
from app.models.agent import Agent, AgentLLMConfig, AgentRetrievalConfig, AgentDocument
from uuid import UUID


class CRUDAgent(CRUDBase[Agent]):
    """CRUD operations for Agent"""

    def create_with_configs(
        self,
        db: Session,
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
        db.flush()  # Get agent.id without committing

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

        db.commit()
        db.refresh(agent)
        return agent

    def get_with_configs(self, db: Session, agent_id: UUID) -> Optional[Agent]:
        """Get agent with all configs loaded"""
        statement = select(Agent).where(Agent.id == agent_id)
        agent = db.exec(statement).first()

        if agent:
            # Eagerly load relationships
            _ = agent.llm_config
            _ = agent.retrieval_config
            _ = agent.document_links

        return agent

    def get_by_project(
        self, db: Session, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Agent]:
        """Get all agents for a project"""
        statement = (
            select(Agent)
            .where(Agent.project_id == project_id)
            .where(Agent.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(db.exec(statement).all())

    def update_llm_config(
        self, db: Session, agent_id: UUID, config_data: dict
    ) -> Optional[AgentLLMConfig]:
        """Update LLM configuration"""
        statement = select(AgentLLMConfig).where(AgentLLMConfig.agent_id == agent_id)
        config = db.exec(statement).first()

        if config:
            for key, value in config_data.items():
                setattr(config, key, value)
            db.add(config)
            db.commit()
            db.refresh(config)

        return config

    def link_documents(
        self,
        db: Session,
        agent_id: UUID,
        document_ids: List[int],
        replace: bool = False,
    ) -> List[AgentDocument]:
        """Link documents to agent"""

        if replace:
            # Remove existing links
            statement = select(AgentDocument).where(AgentDocument.agent_id == agent_id)
            existing = db.exec(statement).all()
            for link in existing:
                db.delete(link)

        # Create new links
        links = []
        for doc_id in document_ids:
            link = AgentDocument(agent_id=agent_id, document_id=doc_id)
            db.add(link)
            links.append(link)

        db.commit()
        return links


# Create singleton instance
agent_crud = CRUDAgent(Agent)
