from uuid import UUID
from typing import List, Optional, Tuple, Dict, Any
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
import logging

from app.models.agent import Agent, AgentLLMConfig, LLMProvider
from app.api.deps import SessionDep
from app.services.processing.vector_search_service import VectorSearchService
from app.services.processing.embedding_service import EmbeddingGenerationService
from app.core.interfaces.llm import BaseLLM
from app.providers.llm.openai_llm import OpenAILLM
from app.providers.llm.gemini_llm import GeminiLLM

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, session: Session):
        self.session = session
        self.vector_service = VectorSearchService(session)
        self.embedding_service = EmbeddingGenerationService(session)

    def _get_llm_provider(self, config: AgentLLMConfig) -> BaseLLM:
        """Factory to get the correct LLM provider based on config."""

        logger.info(f"Getting LLM provider for config: {config}")

        if config.provider == LLMProvider.OPENAI:
            return OpenAILLM(api_key=None)  # Uses env var
        elif config.provider == LLMProvider.AZURE_OPENAI:
            return OpenAILLM()
        elif config.provider == LLMProvider.GEMINI:
            return GeminiLLM()
        elif config.provider == LLMProvider.ANTHROPIC:
            raise NotImplementedError("Anthropic provider not yet implemented")

        return OpenAILLM()

    async def run_agent(
        self,
        agent_id: UUID,
        query: str,
        session_id: UUID,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Run the RAG agent for a given query.

        Returns:
            Tuple[str, List[Dict]]: (Response text, List of source citations)
        """
        # 1. Fetch Agent & Config
        statement = (
            select(Agent)
            .where(Agent.id == agent_id)
            .options(
                selectinload(Agent.llm_config),
                selectinload(Agent.retrieval_config),
                selectinload(Agent.document_links),
            )
        )
        result = await self.session.execute(statement)
        agent = result.scalars().first()

        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        if not agent.llm_config:
            # Create default config if missing? Or raise error?
            # Raising error is safer for now.
            print(f"Agent {agent_id} missing LLM config")  # Debug
            # In a real app we might fallback to defaults
            # raise ValueError(f"Agent {agent_id} missing LLM config")
            # Proceeding effectively with defaults if I construct it manually,
            # but let's assume valid agent creation ensures this.
            pass

        # 2. Retrieve Context
        # Flatten document IDs from agent links
        doc_ids = (
            [link.document_id for link in agent.document_links]
            if agent.document_links
            else None
        )

        # Generate embedding for query
        query_embedding = self.embedding_service.embed_query(query)

        # Search
        # Use defaults from retrieval config if available
        top_k = 5
        if agent.retrieval_config:
            top_k = agent.retrieval_config.top_k

        chunks_with_scores = await self.vector_service.similarity_search_with_scores(
            query_embedding=query_embedding,
            limit=top_k,
            document_ids=doc_ids,  # Filter by documents linked to this agent
            project_id=agent.project_id,  # And/Or project
        )

        # 3. Construct Context String
        context_parts = []
        citations = []

        for chunk, score in chunks_with_scores:
            # Basic context format
            context_parts.append(f"Content: {chunk.text}")

            # Prepare citation (metadata)
            citations.append(
                {
                    "chunk_id": chunk.id,  # Now int
                    "document_id": str(chunk.document_id),
                    "document_name": (
                        chunk.document.filename if chunk.document else "Unknown"
                    ),
                    "content": chunk.text,
                    "similarity_score": score,
                    "page_number": chunk.page_number,
                }
            )

        context_str = "\n\n---\n\n".join(context_parts)

        # 4. Construct Prompt
        system_prompt = "You are a helpful AI assistant."
        if agent.llm_config and agent.llm_config.system_prompt:
            system_prompt = agent.llm_config.system_prompt

        full_prompt = f"""
        Use the following context to answer the user's question. If the answer is not in the context, say you don't know.

        Context:
        {context_str}

        User Question: {query}
        """

        logger.info(f"Full prompt: {full_prompt}")
        print(f"Full prompt: {full_prompt}")

        # 5. Generate Response
        llm_config = agent.llm_config
        provider = self._get_llm_provider(llm_config)

        response_text = await provider.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=llm_config.temperature if llm_config else 0.7,
            max_tokens=llm_config.max_tokens if llm_config else 1000,
            model=llm_config.model_name if llm_config else "gpt-4-turbo-preview",
        )

        return response_text, citations
