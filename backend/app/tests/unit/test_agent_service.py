import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from app.services.agent_service import AgentService
from app.models.agent import Agent, AgentRetrievalConfig
from app.core.interfaces.llm import LLMResponse

@pytest.mark.asyncio
class TestAgentService:
    async def test_retrieve_context_vector_only(self):
        # Setup
        session = AsyncMock()
        vector_service = AsyncMock()
        embedding_service = MagicMock()
        
        service = AgentService(session, vector_service, embedding_service)
        
        agent = Agent(id=uuid4(), project_id=uuid4(), name="Test Agent")
        agent.retrieval_config = AgentRetrievalConfig(retrieval_mode="vector", top_k=5)
        agent.document_links = []
        
        embedding_service.embed_query.return_value = [0.1, 0.2]
        vector_service.similarity_search_with_scores.return_value = [
            (MagicMock(id=1, text="Context 1", document_id=uuid4(), page_number=1, document=None), 0.9)
        ]
        
        # Execute
        context_str, citations = await service._retrieve_context(agent, "test query")
        
        # Assert
        assert "Content: Context 1" in context_str
        assert len(citations) == 1
        assert citations[0]["content"] == "Context 1"
        vector_service.similarity_search_with_scores.assert_called_once()

    async def test_retrieve_context_hybrid(self):
        # Setup
        session = AsyncMock()
        vector_service = AsyncMock()
        embedding_service = MagicMock()
        
        service = AgentService(session, vector_service, embedding_service)
        
        agent = Agent(id=uuid4(), project_id=uuid4(), name="Test Agent")
        agent.retrieval_config = AgentRetrievalConfig(retrieval_mode="hybrid", top_k=5)
        agent.document_links = []
        
        embedding_service.embed_query.return_value = [0.1, 0.2]
        vector_service.hybrid_search.return_value = [
            (MagicMock(id=1, text="Hybrid Context", document_id=uuid4(), page_number=1, document=None), 0.85)
        ]
        
        # Execute
        context_str, citations = await service._retrieve_context(agent, "test query")
        
        # Assert
        assert "Hybrid Context" in context_str
        vector_service.hybrid_search.assert_called_once()

    @patch("app.services.agent_service.OpenAILLM")
    async def test_run_agent_success(self, mock_llm_class):
        # Setup
        session = AsyncMock()
        vector_service = AsyncMock()
        
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = LLMResponse(
            content="AI Response", 
            model_name="gpt-4o",
            total_tokens=100
        )
        mock_llm_class.return_value = mock_llm
        
        service = AgentService(session, vector_service)
        
        # Mock Agent fetch
        agent = Agent(id=uuid4(), project_id=uuid4(), name="Test Agent")
        agent.llm_config = MagicMock(provider="openai", temperature=0.7, max_tokens=1000, model_name="gpt-4o")
        
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = agent
        session.execute.return_value = mock_result
        
        # Mock context retrieval
        service._retrieve_context = AsyncMock(return_value=("Context", [{"chunk_id": 1}]))
        
        # Execute
        result = await service.run_agent(agent.id, "query", uuid4())
        
        # Assert
        assert result.content == "AI Response"
        assert result.model_name == "gpt-4o"
        assert len(result.citations) == 1
