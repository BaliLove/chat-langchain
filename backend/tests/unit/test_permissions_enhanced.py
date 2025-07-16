"""Enhanced unit tests for permission-based filtering and access control."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from langchain_core.documents import Document

from backend.utils import format_docs


@pytest.fixture
def sample_documents():
    """Create sample documents with various metadata."""
    return [
        Document(
            page_content="Public event information about wedding KM150726VV",
            metadata={
                "data_source": "events",
                "is_private": False,
                "event_code": "KM150726VV",
                "title": "Smith Wedding Event"
            }
        ),
        Document(
            page_content="Private vendor contract details",
            metadata={
                "data_source": "vendors",
                "is_private": True,
                "vendor_id": "vendor-123"
            }
        ),
        Document(
            page_content="Internal team notes about issues",
            metadata={
                "data_source": "issues",
                "is_private": True,
                "issue_id": "issue-456"
            }
        ),
        Document(
            page_content="Public inbox message from client",
            metadata={
                "data_source": "inbox_messages",
                "is_private": False,
                "event_code": "KM150726VV",
                "sender_email": "client@example.com"
            }
        ),
        Document(
            page_content="Training material for new staff",
            metadata={
                "data_source": "training",
                "is_private": False,
                "category": "onboarding"
            }
        )
    ]


@pytest.fixture
def member_permissions():
    """Standard member permissions."""
    return {
        "allowed_agents": ["chat", "search"],
        "allowed_data_sources": ["events", "inbox_messages", "training"],
        "role": "member"
    }


@pytest.fixture
def manager_permissions():
    """Manager permissions with more access."""
    return {
        "allowed_agents": ["chat", "search", "message-finder", "event-analyzer"],
        "allowed_data_sources": ["events", "inbox_messages", "training", "vendors", "issues"],
        "role": "manager"
    }


@pytest.fixture
def admin_permissions():
    """Admin permissions with full access."""
    return {
        "allowed_agents": ["*"],
        "allowed_data_sources": ["*"],
        "role": "admin"
    }


class TestPermissionFiltering:
    """Test document filtering based on permissions."""
    
    def test_member_document_filtering(self, sample_documents, member_permissions):
        """Test that members only see allowed data sources."""
        formatted = format_docs(sample_documents, member_permissions)
        
        # Members should see events, inbox_messages, and training
        assert "Public event information" in formatted
        assert "Public inbox message" in formatted
        assert "Training material" in formatted
        
        # Should NOT see vendors or issues
        assert "vendor contract" not in formatted
        assert "Internal team notes" not in formatted
    
    def test_manager_document_filtering(self, sample_documents, manager_permissions):
        """Test that managers see more data sources."""
        formatted = format_docs(sample_documents, manager_permissions)
        
        # Managers should see all data sources
        assert "Public event information" in formatted
        assert "Public inbox message" in formatted
        assert "Training material" in formatted
        assert "vendor contract" in formatted
        assert "Internal team notes" in formatted
    
    def test_admin_sees_everything(self, sample_documents, admin_permissions):
        """Test that admins bypass all filters."""
        formatted = format_docs(sample_documents, admin_permissions)
        
        # Admin should see all documents
        for doc in sample_documents:
            assert doc.page_content in formatted
    
    def test_private_flag_filtering(self, member_permissions):
        """Test that private documents are filtered based on role."""
        docs = [
            Document(
                page_content="Public event",
                metadata={"data_source": "events", "is_private": False}
            ),
            Document(
                page_content="Private event notes",
                metadata={"data_source": "events", "is_private": True}
            )
        ]
        
        formatted = format_docs(docs, member_permissions)
        
        # Member should only see public documents
        assert "Public event" in formatted
        assert "Private event notes" not in formatted
    
    def test_empty_permissions(self, sample_documents):
        """Test behavior with no permissions."""
        empty_permissions = {
            "allowed_agents": [],
            "allowed_data_sources": [],
            "role": "none"
        }
        
        formatted = format_docs(sample_documents, empty_permissions)
        
        # Should not see any documents
        for doc in sample_documents:
            assert doc.page_content not in formatted
    
    def test_missing_metadata(self, member_permissions):
        """Test handling of documents with missing metadata."""
        docs = [
            Document(
                page_content="Document without data_source",
                metadata={"title": "Test"}
            ),
            Document(
                page_content="Document with data_source",
                metadata={"data_source": "events"}
            )
        ]
        
        formatted = format_docs(docs, member_permissions)
        
        # Should handle missing metadata gracefully
        assert "Document without data_source" not in formatted
        assert "Document with data_source" in formatted
    
    def test_event_code_preservation(self, member_permissions):
        """Test that event codes are preserved in formatting."""
        docs = [
            Document(
                page_content="Message about wedding",
                metadata={
                    "data_source": "inbox_messages",
                    "event_code": "KM150726VV",
                    "event_name": "Smith Wedding"
                }
            )
        ]
        
        formatted = format_docs(docs, member_permissions)
        
        # Event code should be included in formatted output
        assert "KM150726VV" in formatted
        assert "Smith Wedding" in formatted


class TestAgentPermissions:
    """Test agent access control."""
    
    def test_member_agent_access(self, member_permissions):
        """Test member agent restrictions."""
        assert "chat" in member_permissions["allowed_agents"]
        assert "search" in member_permissions["allowed_agents"]
        assert "message-finder" not in member_permissions["allowed_agents"]
        assert "issue-tracker" not in member_permissions["allowed_agents"]
    
    def test_manager_agent_access(self, manager_permissions):
        """Test manager agent access."""
        allowed = manager_permissions["allowed_agents"]
        assert "chat" in allowed
        assert "search" in allowed
        assert "message-finder" in allowed
        assert "event-analyzer" in allowed
    
    def test_admin_wildcard_access(self, admin_permissions):
        """Test admin wildcard permissions."""
        assert admin_permissions["allowed_agents"] == ["*"]
        assert admin_permissions["allowed_data_sources"] == ["*"]
    
    def test_agent_permission_check_function(self):
        """Test helper function for checking agent access."""
        def has_agent_access(permissions, agent_name):
            allowed = permissions.get("allowed_agents", [])
            return "*" in allowed or agent_name in allowed
        
        member_perms = {"allowed_agents": ["chat", "search"]}
        admin_perms = {"allowed_agents": ["*"]}
        
        assert has_agent_access(member_perms, "chat") is True
        assert has_agent_access(member_perms, "research") is False
        assert has_agent_access(admin_perms, "anything") is True


class TestBaliLoveSpecificPermissions:
    """Test Bali Love specific permission scenarios."""
    
    def test_event_access_by_team(self):
        """Test that team members can access their assigned events."""
        team_permissions = {
            "allowed_agents": ["chat", "message-finder"],
            "allowed_data_sources": ["events", "inbox_messages"],
            "allowed_events": ["KM150726VV", "BL230415JD"],  # Specific events
            "role": "member"
        }
        
        docs = [
            Document(
                page_content="Message for allowed event",
                metadata={
                    "data_source": "inbox_messages",
                    "event_code": "KM150726VV"
                }
            ),
            Document(
                page_content="Message for different event",
                metadata={
                    "data_source": "inbox_messages",
                    "event_code": "XX999999ZZ"
                }
            )
        ]
        
        # This would need custom filtering logic for event-specific access
        # Demonstrating the test structure
        formatted = format_docs(docs, team_permissions)
        assert "Message for allowed event" in formatted
    
    def test_vendor_privacy_filtering(self):
        """Test vendor information privacy."""
        vendor_docs = [
            Document(
                page_content="Public vendor profile",
                metadata={
                    "data_source": "vendors",
                    "is_private": False,
                    "vendor_type": "florist"
                }
            ),
            Document(
                page_content="Private vendor pricing",
                metadata={
                    "data_source": "vendors",
                    "is_private": True,
                    "contains_pricing": True
                }
            )
        ]
        
        member_perms = {
            "allowed_agents": ["search"],
            "allowed_data_sources": ["vendors"],
            "role": "member"
        }
        
        formatted = format_docs(vendor_docs, member_perms)
        
        # Members should only see public vendor info
        assert "Public vendor profile" in formatted
        assert "Private vendor pricing" not in formatted
    
    def test_message_reply_status_visibility(self):
        """Test filtering based on message reply status."""
        messages = [
            Document(
                page_content="Urgent: Unanswered client question",
                metadata={
                    "data_source": "inbox_messages",
                    "is_replied": False,
                    "priority": "high",
                    "event_code": "KM150726VV"
                }
            ),
            Document(
                page_content="Resolved: Previous inquiry",
                metadata={
                    "data_source": "inbox_messages",
                    "is_replied": True,
                    "event_code": "KM150726VV"
                }
            )
        ]
        
        manager_perms = {
            "allowed_agents": ["message-finder"],
            "allowed_data_sources": ["inbox_messages"],
            "role": "manager",
            "show_unanswered_only": True  # Special filter
        }
        
        # This demonstrates how we might filter by reply status
        unanswered = [doc for doc in messages if not doc.metadata.get("is_replied", True)]
        assert len(unanswered) == 1
        assert "Urgent" in unanswered[0].page_content


class TestPermissionEdgeCases:
    """Test edge cases and error handling."""
    
    def test_malformed_permissions(self, sample_documents):
        """Test handling of malformed permission objects."""
        malformed_perms = {
            "allowed_agents": "chat",  # Should be list
            "allowed_data_sources": None,  # Should be list
            "role": ""
        }
        
        # Should handle gracefully without crashing
        formatted = format_docs(sample_documents, malformed_perms)
        assert formatted is not None
    
    def test_case_sensitivity(self):
        """Test that permission checks are case-insensitive."""
        docs = [
            Document(
                page_content="Event data",
                metadata={"data_source": "Events"}  # Capitalized
            )
        ]
        
        permissions = {
            "allowed_data_sources": ["events"],  # Lowercase
            "role": "member"
        }
        
        formatted = format_docs(docs, permissions)
        # Should match regardless of case
        assert "Event data" in formatted
    
    def test_special_characters_in_metadata(self):
        """Test handling of special characters in metadata."""
        docs = [
            Document(
                page_content="Special event",
                metadata={
                    "data_source": "events",
                    "title": "John & Jane's Wedding © 2024",
                    "event_code": "KM-150726-VV"
                }
            )
        ]
        
        permissions = {"allowed_data_sources": ["events"], "role": "member"}
        
        formatted = format_docs(docs, permissions)
        # Should handle special characters
        assert "Special event" in formatted
        assert formatted is not None