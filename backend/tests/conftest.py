"""Shared test fixtures and configuration for backend tests."""

import os
import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, List, Any
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig

from backend.retrieval_graph.state import AgentState, Router


# Set test environment
os.environ["TESTING"] = "true"


@pytest.fixture
def mock_permissions():
    """Standard member permissions for testing."""
    return {
        "allowed_agents": ["chat", "search"],
        "allowed_data_sources": ["events", "inbox_messages", "training"],
        "role": "member"
    }


@pytest.fixture
def mock_manager_permissions():
    """Manager permissions for testing."""
    return {
        "allowed_agents": ["chat", "search", "message-finder", "event-analyzer"],
        "allowed_data_sources": ["events", "inbox_messages", "vendors", "issues", "training"],
        "role": "manager"
    }


@pytest.fixture
def mock_admin_permissions():
    """Admin permissions for testing."""
    return {
        "allowed_agents": ["*"],
        "allowed_data_sources": ["*"],
        "role": "admin"
    }


@pytest.fixture
def mock_user_info():
    """Mock user information with permissions."""
    return {
        "user_id": "test-user-123",
        "email": "test@bali.love",
        "team_id": "bali-love-team",
        "permissions": {
            "allowed_agents": ["chat", "search"],
            "allowed_data_sources": ["events", "inbox_messages", "training"],
            "role": "member"
        }
    }


@pytest.fixture
def mock_graph_state():
    """Mock graph state for testing."""
    return AgentState(
        messages=[HumanMessage(content="Test query")],
        router=None,
        documents=None,
        user_info={
            "permissions": {
                "allowed_agents": ["chat", "search"],
                "allowed_data_sources": ["events", "inbox_messages"],
                "role": "member"
            }
        }
    )


@pytest.fixture
def mock_runnable_config():
    """Mock runnable configuration."""
    return RunnableConfig(
        configurable={
            "query_model": "openai/gpt-4-turbo-preview",
            "response_model": "openai/gpt-4-turbo-preview",
            "provider": "openai",
        }
    )


@pytest.fixture
def sample_event_documents():
    """Sample event-related documents."""
    return [
        Document(
            page_content="Wedding event for John and Jane Smith",
            metadata={
                "data_source": "events",
                "event_code": "KM150726VV",
                "event_name": "Smith Wedding",
                "date": "2024-07-26",
                "venue": "Beach Club Bali",
                "is_private": False
            }
        ),
        Document(
            page_content="Event timeline and schedule details",
            metadata={
                "data_source": "events",
                "event_code": "KM150726VV",
                "document_type": "timeline",
                "is_private": False
            }
        )
    ]


@pytest.fixture
def sample_message_documents():
    """Sample inbox message documents."""
    return [
        Document(
            page_content="Question about catering options for the wedding",
            metadata={
                "data_source": "inbox_messages",
                "event_code": "KM150726VV",
                "sender_email": "client@example.com",
                "is_replied": False,
                "priority": "high",
                "date": "2024-01-15"
            }
        ),
        Document(
            page_content="Venue confirmation received",
            metadata={
                "data_source": "inbox_messages",
                "event_code": "KM150726VV",
                "sender_email": "venue@beachclub.com",
                "is_replied": True,
                "date": "2024-01-10"
            }
        )
    ]


@pytest.fixture
def sample_vendor_documents():
    """Sample vendor documents."""
    return [
        Document(
            page_content="Bali Beach Catering - Premium wedding catering services",
            metadata={
                "data_source": "vendors",
                "vendor_id": "vendor-catering-001",
                "vendor_type": "catering",
                "rating": 4.8,
                "is_private": False
            }
        ),
        Document(
            page_content="Private pricing information for catering packages",
            metadata={
                "data_source": "vendors",
                "vendor_id": "vendor-catering-001",
                "document_type": "pricing",
                "is_private": True
            }
        )
    ]


@pytest.fixture
def mock_llm_response():
    """Mock LLM response generator."""
    def _generate_response(content: str) -> AIMessage:
        return AIMessage(content=content)
    return _generate_response


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    class MockVectorStore:
        def __init__(self):
            self.documents = []
        
        async def asimilarity_search(self, query: str, k: int = 4, filter: Dict = None) -> List[Document]:
            # Return mock documents based on query
            if "event" in query.lower():
                return sample_event_documents()[:k]
            elif "message" in query.lower():
                return sample_message_documents()[:k]
            return []
        
        async def aadd_documents(self, documents: List[Document]) -> List[str]:
            self.documents.extend(documents)
            return [f"doc-{i}" for i in range(len(documents))]
    
    return MockVectorStore()


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    class MockSupabaseClient:
        def __init__(self):
            self.auth = Mock()
            self.auth.get_user = AsyncMock(return_value={
                "user": {"id": "test-user-123", "email": "test@bali.love"}
            })
        
        def from_(self, table: str):
            return self
        
        def select(self, columns: str = "*"):
            return self
        
        def eq(self, column: str, value: Any):
            return self
        
        async def execute(self):
            return {"data": [], "error": None}
    
    return MockSupabaseClient()


@pytest.fixture
def mock_pinecone_index():
    """Mock Pinecone index for testing."""
    class MockPineconeIndex:
        def __init__(self):
            self.vectors = {}
        
        def upsert(self, vectors: List[tuple]) -> Dict:
            for vec_id, values, metadata in vectors:
                self.vectors[vec_id] = {"values": values, "metadata": metadata}
            return {"upserted_count": len(vectors)}
        
        def query(self, vector: List[float], top_k: int = 10, filter: Dict = None) -> Dict:
            # Return mock results
            return {
                "matches": [
                    {
                        "id": "doc-1",
                        "score": 0.95,
                        "metadata": {
                            "content": "Test document",
                            "data_source": "events"
                        }
                    }
                ]
            }
    
    return MockPineconeIndex()


@pytest.fixture
def mock_bubble_client():
    """Mock Bubble.io client for testing."""
    class MockBubbleClient:
        def __init__(self):
            self.data = {
                "events": [
                    {
                        "_id": "event-001",
                        "code": "KM150726VV",
                        "name": "Smith Wedding",
                        "date": "2024-07-26"
                    }
                ],
                "inbox_messages": [
                    {
                        "_id": "msg-001",
                        "event": "event-001",
                        "content": "Test message",
                        "is_replied": False
                    }
                ]
            }
        
        async def fetch_data(self, data_type: str, limit: int = 100) -> List[Dict]:
            return self.data.get(data_type, [])[:limit]
    
    return MockBubbleClient()


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_api: mark test as requiring external API access"
    )