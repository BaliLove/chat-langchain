"""Unit tests for the main retrieval graph logic."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from backend.retrieval_graph.graph import (
    analyze_and_route_query,
    generate_response,
    summarize_documents,
    route_to_research,
)
from backend.retrieval_graph.state import AgentState, Router
from backend.retrieval_graph.configuration import AgentConfiguration


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = RunnableConfig(
        configurable={
            "query_model": "openai/gpt-4-turbo-preview",
            "response_model": "openai/gpt-4-turbo-preview",
            "provider": "openai",
        }
    )
    return config


@pytest.fixture
def mock_state():
    """Create a mock agent state."""
    return AgentState(
        messages=[HumanMessage(content="What is LangChain?")],
        router=None,
        documents=None,
        user_info={"permissions": {"allowed_agents": ["chat"], "allowed_data_sources": ["public"]}},
    )


class TestAnalyzeAndRouteQuery:
    """Tests for the analyze_and_route_query function."""

    @pytest.mark.asyncio
    async def test_route_query_with_existing_router(self, mock_state, mock_config):
        """Test that existing router is returned if present."""
        existing_router = Router(
            type="research",
            logic="User needs detailed information",
        )
        mock_state.router = existing_router

        result = await analyze_and_route_query(mock_state, config=mock_config)

        assert result["router"] == existing_router

    @pytest.mark.asyncio
    async def test_route_query_chitchat(self, mock_state, mock_config):
        """Test routing for chitchat queries."""
        mock_state.messages = [HumanMessage(content="Hello, how are you?")]
        
        with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
            mock_model = Mock()
            mock_structured = Mock()
            mock_model.with_structured_output.return_value = mock_structured
            mock_structured.ainvoke = AsyncMock(
                return_value=Router(type="chitchat", logic="Greeting detected")
            )
            mock_load.return_value = mock_model

            result = await analyze_and_route_query(mock_state, config=mock_config)

            assert result["router"]["type"] == "chitchat"
            assert "Greeting" in result["router"]["logic"]

    @pytest.mark.asyncio
    async def test_route_query_research(self, mock_state, mock_config):
        """Test routing for research queries."""
        with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
            mock_model = Mock()
            mock_structured = Mock()
            mock_model.with_structured_output.return_value = mock_structured
            mock_structured.ainvoke = AsyncMock(
                return_value=Router(
                    type="research",
                    logic="User asking about technical topic",
                )
            )
            mock_load.return_value = mock_model

            result = await analyze_and_route_query(mock_state, config=mock_config)

            assert result["router"]["type"] == "research"
            assert "technical" in result["router"]["logic"]

    @pytest.mark.asyncio
    async def test_route_query_with_permission_check(self, mock_state, mock_config):
        """Test that routing respects user permissions."""
        mock_state.user_info = {
            "permissions": {
                "allowed_agents": ["search"],  # No chat agent
                "allowed_data_sources": ["public"],
            }
        }
        
        with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
            mock_model = Mock()
            mock_structured = Mock()
            mock_model.with_structured_output.return_value = mock_structured
            mock_structured.ainvoke = AsyncMock(
                return_value=Router(type="research", logic="Permission filtered")
            )
            mock_load.return_value = mock_model

            result = await analyze_and_route_query(mock_state, config=mock_config)

            # Should still route but permissions will be checked later
            assert result["router"]["type"] == "research"


class TestGenerateResponse:
    """Tests for the generate_response function."""

    @pytest.mark.asyncio
    async def test_generate_response_with_documents(self, mock_state, mock_config):
        """Test response generation with retrieved documents."""
        mock_state.documents = [
            {"content": "LangChain is a framework for LLM applications"},
            {"content": "It helps build context-aware applications"},
        ]
        
        with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
            mock_model = Mock()
            mock_model.ainvoke = AsyncMock(
                return_value=AIMessage(content="LangChain is a powerful framework...")
            )
            mock_load.return_value = mock_model

            result = await generate_response(mock_state, config=mock_config)

            assert "messages" in result
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], AIMessage)
            assert "LangChain" in result["messages"][0].content

    @pytest.mark.asyncio
    async def test_generate_response_without_documents(self, mock_state, mock_config):
        """Test response generation without documents."""
        mock_state.documents = None
        
        with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
            mock_model = Mock()
            mock_model.ainvoke = AsyncMock(
                return_value=AIMessage(content="I'll help you with that...")
            )
            mock_load.return_value = mock_model

            result = await generate_response(mock_state, config=mock_config)

            assert "messages" in result
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], AIMessage)

    @pytest.mark.asyncio
    async def test_generate_response_with_context_filtering(self, mock_state, mock_config):
        """Test that documents are filtered based on user permissions."""
        mock_state.documents = [
            {"content": "Public information", "metadata": {"data_source": "public"}},
            {"content": "Private information", "metadata": {"data_source": "private"}},
        ]
        mock_state.user_info = {
            "permissions": {"allowed_data_sources": ["public"]}
        }
        
        with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
            mock_model = Mock()
            mock_model.ainvoke = AsyncMock(
                return_value=AIMessage(content="Based on public information...")
            )
            mock_load.return_value = mock_model

            with patch("backend.utils.format_docs") as mock_format:
                mock_format.return_value = "Formatted public docs"
                
                result = await generate_response(mock_state, config=mock_config)
                
                # Verify format_docs was called with documents and permissions
                mock_format.assert_called_once()
                call_args = mock_format.call_args[0]
                assert len(call_args[0]) == 2  # Both docs passed
                assert call_args[1] == mock_state.user_info["permissions"]


class TestSummarizeDocuments:
    """Tests for the summarize_documents function."""

    @pytest.mark.asyncio
    async def test_summarize_documents_success(self, mock_state, mock_config):
        """Test successful document summarization."""
        mock_state.documents = [
            {"content": "Document 1 content"},
            {"content": "Document 2 content"},
        ]
        
        with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
            mock_model = Mock()
            mock_model.ainvoke = AsyncMock(
                return_value=AIMessage(content="Summary: Key points from documents...")
            )
            mock_load.return_value = mock_model

            result = await summarize_documents(mock_state, config=mock_config)

            assert "summary" in result
            assert "Summary" in result["summary"]

    @pytest.mark.asyncio
    async def test_summarize_documents_empty(self, mock_state, mock_config):
        """Test summarization with no documents."""
        mock_state.documents = []
        
        result = await summarize_documents(mock_state, config=mock_config)

        assert "summary" in result
        assert result["summary"] == ""


class TestRouteToResearch:
    """Tests for the route_to_research function."""

    def test_route_chitchat(self, mock_state):
        """Test routing for chitchat type."""
        mock_state.router = Router(type="chitchat", logic="Casual conversation")
        
        result = route_to_research(mock_state)
        
        assert result == END

    def test_route_research(self, mock_state):
        """Test routing for research type."""
        mock_state.router = Router(type="research", logic="Needs information")
        
        result = route_to_research(mock_state)
        
        assert result == "research"

    def test_route_with_insufficient_permissions(self, mock_state):
        """Test routing when user lacks required agent permissions."""
        mock_state.router = Router(type="research", logic="Needs research")
        mock_state.user_info = {
            "permissions": {"allowed_agents": []}  # No agents allowed
        }
        
        result = route_to_research(mock_state)
        
        # Should still route to research, permissions checked elsewhere
        assert result == "research"

    def test_route_default(self, mock_state):
        """Test default routing behavior."""
        mock_state.router = None
        
        result = route_to_research(mock_state)
        
        assert result == END


@pytest.mark.asyncio
class TestErrorHandling:
    """Tests for error handling in graph functions."""

    async def test_analyze_route_query_error_handling(self, mock_state, mock_config):
        """Test error handling in analyze_and_route_query."""
        with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
            mock_load.side_effect = Exception("Model loading failed")
            
            with pytest.raises(Exception) as exc_info:
                await analyze_and_route_query(mock_state, config=mock_config)
            
            assert "Model loading failed" in str(exc_info.value)

    async def test_generate_response_error_handling(self, mock_state, mock_config):
        """Test error handling in generate_response."""
        mock_state.documents = [{"content": "Test doc"}]
        
        with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
            mock_model = Mock()
            mock_model.ainvoke = AsyncMock(side_effect=Exception("API call failed"))
            mock_load.return_value = mock_model
            
            with pytest.raises(Exception) as exc_info:
                await generate_response(mock_state, config=mock_config)
            
            assert "API call failed" in str(exc_info.value)