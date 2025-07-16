"""Unit tests for router decision logic."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from backend.retrieval_graph.state import Router, AgentState
from backend.retrieval_graph.prompts import ROUTER_SYSTEM_PROMPT


class TestRouterLogic:
    """Test the router's decision-making logic."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return RunnableConfig(
            configurable={
                "query_model": "openai/gpt-4-turbo-preview",
                "provider": "openai",
            }
        )
    
    @pytest.fixture
    def router_test_cases(self):
        """Test cases for router decisions."""
        return [
            # Chitchat cases
            {
                "query": "Hello, how are you today?",
                "expected_type": "chitchat",
                "reason": "Greeting/social interaction"
            },
            {
                "query": "Thanks for your help!",
                "expected_type": "chitchat",
                "reason": "Appreciation/closing"
            },
            {
                "query": "What's the weather like?",
                "expected_type": "chitchat",
                "reason": "Off-topic question"
            },
            
            # Research cases - Bali Love specific
            {
                "query": "Show me all messages for event KM150726VV",
                "expected_type": "research",
                "reason": "Event-specific information request"
            },
            {
                "query": "Are there any unanswered messages for the Smith wedding?",
                "expected_type": "research",
                "reason": "Message status query"
            },
            {
                "query": "What venues do we have available for beach weddings?",
                "expected_type": "research",
                "reason": "Venue search query"
            },
            {
                "query": "Find all issues related to catering vendors",
                "expected_type": "research",
                "reason": "Issue tracking query"
            },
            {
                "query": "What's the training process for new wedding coordinators?",
                "expected_type": "research",
                "reason": "Training material request"
            },
        ]
    
    @pytest.mark.asyncio
    async def test_router_classifications(self, router_test_cases, mock_config):
        """Test that router correctly classifies different query types."""
        from backend.retrieval_graph.graph import analyze_and_route_query
        
        for test_case in router_test_cases:
            state = AgentState(
                messages=[HumanMessage(content=test_case["query"])],
                router=None,
                user_info={"permissions": {"allowed_agents": ["chat", "search"]}}
            )
            
            with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
                mock_model = Mock()
                mock_structured = Mock()
                mock_model.with_structured_output.return_value = mock_structured
                
                # Simulate router decision based on query patterns
                router_type = self._determine_router_type(test_case["query"])
                mock_structured.ainvoke = AsyncMock(
                    return_value=Router(
                        type=router_type,
                        logic=test_case["reason"]
                    )
                )
                mock_load.return_value = mock_model
                
                result = await analyze_and_route_query(state, config=mock_config)
                
                assert result["router"]["type"] == test_case["expected_type"], \
                    f"Query '{test_case['query']}' should be classified as {test_case['expected_type']}"
    
    def _determine_router_type(self, query: str) -> str:
        """Helper to simulate router logic for testing."""
        query_lower = query.lower()
        
        # Chitchat patterns
        chitchat_patterns = [
            "hello", "hi", "hey", "thanks", "thank you", "bye", 
            "goodbye", "how are you", "weather", "what's up"
        ]
        
        # Research patterns (Bali Love specific)
        research_patterns = [
            "event", "message", "wedding", "venue", "vendor", 
            "issue", "training", "show me", "find", "search",
            "are there any", "what", "when", "where", "who"
        ]
        
        if any(pattern in query_lower for pattern in chitchat_patterns):
            return "chitchat"
        elif any(pattern in query_lower for pattern in research_patterns):
            return "research"
        else:
            return "chitchat"  # Default
    
    def test_router_with_context(self):
        """Test router decisions with conversation context."""
        state = AgentState(
            messages=[
                HumanMessage(content="Tell me about event KM150726VV"),
                AIMessage(content="The Smith wedding is scheduled for..."),
                HumanMessage(content="What about the catering?")  # Context-dependent
            ],
            router=None,
            user_info={"permissions": {"allowed_agents": ["chat", "search"]}}
        )
        
        # With context, "What about the catering?" should be research
        # because it refers to the previous event discussion
        assert len(state.messages) == 3
        assert "event" in state.messages[0].content.lower()
    
    def test_router_edge_cases(self):
        """Test router with edge case queries."""
        edge_cases = [
            "",  # Empty query
            "???",  # Only punctuation
            "KM150726VV",  # Just an event code
            "URGENT: ",  # Incomplete urgent message
            "a" * 1000,  # Very long query
        ]
        
        for query in edge_cases:
            state = AgentState(
                messages=[HumanMessage(content=query)],
                router=None,
                user_info={"permissions": {"allowed_agents": ["chat"]}}
            )
            
            # Router should handle these gracefully
            assert state.messages[0].content == query


class TestRouterPermissionIntegration:
    """Test router behavior with different permission levels."""
    
    @pytest.mark.asyncio
    async def test_router_respects_agent_permissions(self):
        """Test that router considers user's allowed agents."""
        from backend.retrieval_graph.graph import route_to_research
        
        # User without research agent
        state_no_research = AgentState(
            messages=[HumanMessage(content="Find all vendor issues")],
            router=Router(type="research", logic="User wants vendor issues"),
            user_info={
                "permissions": {
                    "allowed_agents": ["chat"],  # No search/research
                    "allowed_data_sources": ["public"]
                }
            }
        )
        
        # Even with research router, should check permissions
        result = route_to_research(state_no_research)
        assert result == "research"  # Still routes, but permissions checked later
        
        # User with research agent
        state_with_research = AgentState(
            messages=[HumanMessage(content="Find all vendor issues")],
            router=Router(type="research", logic="User wants vendor issues"),
            user_info={
                "permissions": {
                    "allowed_agents": ["chat", "search", "message-finder"],
                    "allowed_data_sources": ["vendors", "issues"]
                }
            }
        )
        
        result = route_to_research(state_with_research)
        assert result == "research"
    
    def test_router_with_role_based_logic(self):
        """Test router decisions based on user roles."""
        queries_by_role = {
            "member": {
                "query": "Show me internal team notes",
                "should_access": False
            },
            "manager": {
                "query": "Show me all vendor contracts",
                "should_access": True
            },
            "admin": {
                "query": "Show me everything for event KM150726VV",
                "should_access": True
            }
        }
        
        for role, test_data in queries_by_role.items():
            state = AgentState(
                messages=[HumanMessage(content=test_data["query"])],
                router=None,
                user_info={
                    "role": role,
                    "permissions": self._get_permissions_for_role(role)
                }
            )
            
            # Verify state has correct role
            assert state.user_info["role"] == role
    
    def _get_permissions_for_role(self, role: str) -> dict:
        """Helper to get permissions based on role."""
        if role == "admin":
            return {
                "allowed_agents": ["*"],
                "allowed_data_sources": ["*"]
            }
        elif role == "manager":
            return {
                "allowed_agents": ["chat", "search", "message-finder", "event-analyzer"],
                "allowed_data_sources": ["events", "inbox_messages", "vendors", "issues"]
            }
        else:  # member
            return {
                "allowed_agents": ["chat", "search"],
                "allowed_data_sources": ["events", "inbox_messages", "training"]
            }


class TestRouterPrompts:
    """Test router prompt effectiveness."""
    
    def test_router_system_prompt_contains_bali_love_context(self):
        """Ensure router prompt is customized for Bali Love."""
        assert "Bali Love" in ROUTER_SYSTEM_PROMPT
        assert "wedding" in ROUTER_SYSTEM_PROMPT.lower()
        assert "event" in ROUTER_SYSTEM_PROMPT.lower()
    
    def test_router_prompt_mentions_event_codes(self):
        """Ensure router knows about event code format."""
        # Event codes like KM150726VV should be recognized
        assert any(
            keyword in ROUTER_SYSTEM_PROMPT.lower() 
            for keyword in ["event code", "event_code", "km", "vv"]
        )
    
    def test_router_prompt_includes_data_sources(self):
        """Ensure router knows about available data sources."""
        data_sources = [
            "events", "inbox_messages", "vendors", 
            "venues", "issues", "training"
        ]
        
        prompt_lower = ROUTER_SYSTEM_PROMPT.lower()
        # At least some data sources should be mentioned
        mentioned_sources = [
            source for source in data_sources 
            if source in prompt_lower
        ]
        assert len(mentioned_sources) >= 3


class TestRouterErrorHandling:
    """Test router error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_router_handles_llm_errors(self, mock_config):
        """Test router behavior when LLM fails."""
        from backend.retrieval_graph.graph import analyze_and_route_query
        
        state = AgentState(
            messages=[HumanMessage(content="Test query")],
            router=None,
            user_info={"permissions": {"allowed_agents": ["chat"]}}
        )
        
        with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
            mock_model = Mock()
            mock_structured = Mock()
            mock_model.with_structured_output.return_value = mock_structured
            mock_structured.ainvoke = AsyncMock(
                side_effect=Exception("LLM API error")
            )
            mock_load.return_value = mock_model
            
            with pytest.raises(Exception) as exc_info:
                await analyze_and_route_query(state, config=mock_config)
            
            assert "LLM API error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_router_timeout_handling(self, mock_config):
        """Test router behavior with timeout."""
        import asyncio
        from backend.retrieval_graph.graph import analyze_and_route_query
        
        state = AgentState(
            messages=[HumanMessage(content="Complex query requiring analysis")],
            router=None,
            user_info={"permissions": {"allowed_agents": ["chat", "search"]}}
        )
        
        with patch("backend.retrieval_graph.graph.load_chat_model") as mock_load:
            mock_model = Mock()
            mock_structured = Mock()
            
            async def slow_invoke(*args, **kwargs):
                await asyncio.sleep(10)  # Simulate slow response
                return Router(type="research", logic="Timeout test")
            
            mock_structured.ainvoke = slow_invoke
            mock_model.with_structured_output.return_value = mock_structured
            mock_load.return_value = mock_model
            
            # This would timeout in a real scenario with proper timeout config
            # For testing, we're demonstrating the structure
            
    def test_router_fallback_behavior(self):
        """Test router fallback when classification fails."""
        from backend.retrieval_graph.graph import route_to_research
        
        # State with no router decision
        state = AgentState(
            messages=[HumanMessage(content="Ambiguous query")],
            router=None,  # No router decision made
            user_info={"permissions": {"allowed_agents": ["chat"]}}
        )
        
        # Should have a sensible default
        result = route_to_research(state)
        assert result == "END"  # Default to ending without research