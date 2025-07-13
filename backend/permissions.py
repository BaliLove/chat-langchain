"""Permission handling for the backend retrieval graph.

This module provides permission checking and filtering based on user roles
and allowed data sources.
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Try to import Supabase, but make it optional
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    logger.warning("Supabase package not installed. Permission features will be disabled.")
    SUPABASE_AVAILABLE = False
    Client = None
    create_client = None


@dataclass
class UserPermissions:
    """User permission data structure."""
    user_id: Optional[str]
    email: str
    role: str = "member"
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    allowed_agents: List[str] = None
    allowed_data_sources: List[str] = None
    permissions: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.allowed_agents is None:
            self.allowed_agents = ["chat"]
        if self.allowed_data_sources is None:
            self.allowed_data_sources = ["public", "company_wide"]
        if self.permissions is None:
            self.permissions = {}
    
    def has_agent(self, agent_name: str) -> bool:
        """Check if user has access to a specific agent."""
        return agent_name in self.allowed_agents
    
    def has_data_source(self, source_name: str) -> bool:
        """Check if user has access to a specific data source."""
        return source_name in self.allowed_data_sources
    
    def can_view_team_threads(self) -> bool:
        """Check if user can view team threads."""
        return self.permissions.get("can_view_team_threads", False)
    
    def can_export_data(self) -> bool:
        """Check if user can export data."""
        return self.permissions.get("can_export_data", False)
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"
    
    @property
    def is_manager(self) -> bool:
        """Check if user has manager role."""
        return self.role in ["admin", "manager"]


class PermissionManager:
    """Manages user permissions and access control."""
    
    def __init__(self):
        """Initialize the permission manager with Supabase client."""
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase not available. Permission checks will use defaults.")
            self.supabase = None
            return
            
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
        else:
            logger.warning("Supabase credentials not found. Permission checks will use defaults.")
            self.supabase = None
    
    async def get_user_permissions(self, user_email: str) -> UserPermissions:
        """Fetch user permissions from database.
        
        Args:
            user_email: The user's email address
            
        Returns:
            UserPermissions object with user's access rights
        """
        if not self.supabase:
            # Return default permissions if no database connection
            return UserPermissions(
                user_id=None,
                email=user_email,
                role="member",
                allowed_agents=["chat"],
                allowed_data_sources=["public"]
            )
        
        try:
            # Fetch from user_permissions view
            result = self.supabase.from_("user_permissions").select("*").eq("email", user_email).single().execute()
            
            if result.data:
                data = result.data
                return UserPermissions(
                    user_id=data.get("user_id"),
                    email=data.get("email", user_email),
                    role=data.get("role", "member"),
                    team_id=data.get("team_id"),
                    team_name=data.get("team_name"),
                    allowed_agents=data.get("allowed_agents", ["chat"]),
                    allowed_data_sources=data.get("allowed_data_sources", ["public", "company_wide"]),
                    permissions=data.get("permissions", {})
                )
            else:
                # User not found, return minimal permissions
                logger.info(f"No permissions found for user {user_email}, using defaults")
                return UserPermissions(
                    user_id=None,
                    email=user_email,
                    role="member",
                    allowed_agents=["chat"],
                    allowed_data_sources=["public"]
                )
                
        except Exception as e:
            logger.error(f"Error fetching permissions for {user_email}: {e}")
            # Return safe defaults on error
            return UserPermissions(
                user_id=None,
                email=user_email,
                role="member",
                allowed_agents=["chat"],
                allowed_data_sources=["public"]
            )
    
    def filter_documents_by_permissions(
        self, 
        documents: List[Dict[str, Any]], 
        permissions: UserPermissions
    ) -> List[Dict[str, Any]]:
        """Filter documents based on user's data source permissions.
        
        Args:
            documents: List of documents to filter
            permissions: User's permissions
            
        Returns:
            Filtered list of documents user has access to
        """
        if permissions.is_admin:
            # Admins can see all documents
            return documents
        
        filtered_docs = []
        for doc in documents:
            # Check document metadata for data source
            metadata = doc.get("metadata", {})
            doc_source = metadata.get("data_source", "public")
            
            # Check if user has access to this data source
            if permissions.has_data_source(doc_source):
                filtered_docs.append(doc)
            elif doc_source == "public":
                # Always allow public documents
                filtered_docs.append(doc)
        
        return filtered_docs
    
    def check_agent_access(self, agent_name: str, permissions: UserPermissions) -> bool:
        """Check if user has access to a specific agent.
        
        Args:
            agent_name: Name of the agent to check
            permissions: User's permissions
            
        Returns:
            True if user has access, False otherwise
        """
        return permissions.has_agent(agent_name)
    
    def get_metadata_filters(self, permissions: UserPermissions) -> Dict[str, List[str]]:
        """Get metadata filters based on user permissions.
        
        Args:
            permissions: User's permissions
            
        Returns:
            Dictionary of metadata filters to apply to searches
        """
        filters = {}
        
        # Add data source filters
        if not permissions.is_admin:
            filters["data_source"] = permissions.allowed_data_sources
        
        # Add team-specific filters if applicable
        if permissions.team_id and permissions.has_data_source("team_specific"):
            filters["team_id"] = [permissions.team_id]
        
        return filters


# Global permission manager instance
permission_manager = PermissionManager()


def require_permission(permission_check: str):
    """Decorator to check permissions before executing a function.
    
    Args:
        permission_check: Name of the permission to check (e.g., "can_export_data")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(state, *args, **kwargs):
            # Extract user email from state
            user_email = state.get("user_email")
            if not user_email:
                raise PermissionError("User email not found in state")
            
            # Get user permissions
            permissions = await permission_manager.get_user_permissions(user_email)
            
            # Check specific permission
            if hasattr(permissions, permission_check):
                if not getattr(permissions, permission_check)():
                    raise PermissionError(f"User lacks required permission: {permission_check}")
            
            # Add permissions to state for use in function
            state["user_permissions"] = permissions
            
            return await func(state, *args, **kwargs)
        return wrapper
    return decorator