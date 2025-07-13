import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_user():
    """Mock user data for testing."""
    return {
        "id": "test-user-123",
        "email": "test@bali.love",
        "team": "general",
        "role": "member"
    }

@pytest.fixture
def mock_admin_user():
    """Mock admin user data for testing."""
    return {
        "id": "admin-user-123",
        "email": "admin@bali.love",
        "team": "admin",
        "role": "admin"
    }

@pytest.fixture
def mock_permissions():
    """Mock permissions data for testing."""
    return {
        "team_name": "general",
        "role": "member",
        "allowed_agents": ["general", "research"],
        "allowed_data_sources": ["docs", "api", "tutorials"]
    }

@pytest.fixture
def mock_admin_permissions():
    """Mock admin permissions data for testing."""
    return {
        "team_name": "admin",
        "role": "admin",
        "allowed_agents": ["*"],
        "allowed_data_sources": ["*"]
    }

@pytest.fixture
def mock_message():
    """Mock chat message for testing."""
    return {
        "role": "user",
        "content": "What is LangChain?"
    }

@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    mock = Mock()
    mock.similarity_search = AsyncMock(return_value=[
        Mock(
            page_content="LangChain is a framework for developing applications powered by language models.",
            metadata={"source": "docs", "title": "Introduction"}
        ),
        Mock(
            page_content="LangChain provides tools for prompt management and chaining.",
            metadata={"source": "api", "title": "Core Concepts"}
        )
    ])
    return mock

@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(return_value="LangChain is a powerful framework for building LLM applications.")
    return mock

@pytest.fixture
def mock_graph_state():
    """Mock graph state for testing."""
    return {
        "messages": [{"role": "user", "content": "test question"}],
        "user_info": {
            "email": "test@bali.love",
            "permissions": {
                "allowed_agents": ["general"],
                "allowed_data_sources": ["docs"]
            }
        },
        "context": "",
        "route": None
    }

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock = Mock()
    
    # Auth mock
    mock.auth.get_user = AsyncMock(return_value=Mock(user=Mock(id="test-123")))
    
    # Table mock with chainable methods
    table_mock = Mock()
    table_mock.select = Mock(return_value=table_mock)
    table_mock.eq = Mock(return_value=table_mock)
    table_mock.single = AsyncMock(return_value={"data": {}, "error": None})
    table_mock.insert = AsyncMock(return_value={"data": {}, "error": None})
    table_mock.update = AsyncMock(return_value={"data": {}, "error": None})
    table_mock.delete = AsyncMock(return_value={"data": {}, "error": None})
    
    mock.from_ = Mock(return_value=table_mock)
    mock.table = Mock(return_value=table_mock)
    
    return mock

@pytest.fixture
def mock_bubble_response():
    """Mock Bubble API response for testing."""
    return {
        "response": {
            "results": [
                {
                    "_id": "user1",
                    "email": "user1@bali.love",
                    "authentication": {
                        "email": {
                            "email": "user1@bali.love"
                        }
                    },
                    "team": "general",
                    "role": "member"
                },
                {
                    "_id": "user2",
                    "email": "user2@bali.love",
                    "authentication": {
                        "email": {
                            "email": "user2@bali.love"
                        }
                    },
                    "team": "admin",
                    "role": "admin"
                }
            ],
            "count": 2,
            "remaining": 0
        }
    }