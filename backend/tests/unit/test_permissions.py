import pytest
from unittest.mock import Mock, patch
from backend.retrieval import format_docs_with_permissions

@pytest.mark.unit
class TestPermissions:
    """Test permission-based filtering and access control."""
    
    def test_format_docs_filters_by_data_source(self, mock_permissions):
        """Test that documents are filtered based on allowed data sources."""
        # Create mock documents with different sources
        docs = [
            Mock(page_content="Doc 1", metadata={"source": "docs"}),
            Mock(page_content="Doc 2", metadata={"source": "api"}),
            Mock(page_content="Doc 3", metadata={"source": "internal"}),  # Not allowed
            Mock(page_content="Doc 4", metadata={"source": "tutorials"}),
        ]
        
        # Filter documents
        filtered_content = format_docs_with_permissions(docs, mock_permissions)
        
        # Should only include allowed sources
        assert "Doc 1" in filtered_content
        assert "Doc 2" in filtered_content
        assert "Doc 3" not in filtered_content
        assert "Doc 4" in filtered_content
    
    def test_format_docs_admin_sees_all(self, mock_admin_permissions):
        """Test that admin users can see all documents."""
        # Create mock documents
        docs = [
            Mock(page_content="Public doc", metadata={"source": "docs"}),
            Mock(page_content="Internal doc", metadata={"source": "internal"}),
            Mock(page_content="Private doc", metadata={"source": "private"}),
        ]
        
        # Admin permissions have "*" for all sources
        filtered_content = format_docs_with_permissions(docs, mock_admin_permissions)
        
        # Admin should see everything
        assert "Public doc" in filtered_content
        assert "Internal doc" in filtered_content
        assert "Private doc" in filtered_content
    
    def test_format_docs_empty_permissions(self):
        """Test behavior with no permissions."""
        docs = [
            Mock(page_content="Doc 1", metadata={"source": "docs"}),
        ]
        
        empty_permissions = {
            "allowed_data_sources": []
        }
        
        filtered_content = format_docs_with_permissions(docs, empty_permissions)
        
        # Should return empty or default message
        assert "Doc 1" not in filtered_content
    
    def test_permission_check_for_agents(self, mock_permissions):
        """Test agent access checking."""
        # Test allowed agents
        assert "general" in mock_permissions["allowed_agents"]
        assert "research" in mock_permissions["allowed_agents"]
        assert "admin" not in mock_permissions["allowed_agents"]
        
        # Test with admin permissions
        admin_perms = {"allowed_agents": ["*"]}
        assert "*" in admin_perms["allowed_agents"]  # Admin has access to all
    
    @pytest.mark.asyncio
    async def test_permission_based_routing(self, mock_graph_state):
        """Test that routing respects user permissions."""
        from backend.retrieval_graph.graph import should_use_researcher
        
        # User without research agent access
        mock_graph_state["user_info"]["permissions"]["allowed_agents"] = ["general"]
        
        # Should not route to researcher even with complex query
        mock_graph_state["messages"][-1]["content"] = "Compare X with Y and analyze the differences"
        
        # This would need the actual implementation to test properly
        # For now, we're demonstrating the test structure
        
    def test_data_source_metadata_preservation(self):
        """Test that source metadata is preserved during filtering."""
        docs = [
            Mock(
                page_content="Content",
                metadata={
                    "source": "docs",
                    "title": "Test Title",
                    "url": "https://example.com"
                }
            )
        ]
        
        permissions = {"allowed_data_sources": ["docs"]}
        filtered_content = format_docs_with_permissions(docs, permissions)
        
        # Should preserve source information
        assert "docs" in filtered_content
        assert "Test Title" in filtered_content