"""Supabase client wrapper to handle import issues."""

import os
import logging

logger = logging.getLogger(__name__)

# Try different import patterns for Supabase
SUPABASE_AVAILABLE = False
create_client = None
Client = None

try:
    # Try the standard import
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
    logger.info("Successfully imported Supabase using standard import")
except ImportError:
    try:
        # Try alternative import pattern
        import supabase
        create_client = supabase.create_client
        Client = supabase.Client
        SUPABASE_AVAILABLE = True
        logger.info("Successfully imported Supabase using alternative pattern")
    except (ImportError, AttributeError):
        try:
            # Try another pattern
            from supabase.client import create_client, Client
            SUPABASE_AVAILABLE = True
            logger.info("Successfully imported Supabase from supabase.client")
        except ImportError:
            logger.warning("Supabase package not available. Permission features will be disabled.")

# If Supabase is not available, create mock objects
if not SUPABASE_AVAILABLE:
    class Client:
        """Mock Supabase client."""
        pass
    
    def create_client(url: str, key: str) -> Client:
        """Mock create_client function."""
        logger.warning("Using mock Supabase client - no actual functionality")
        return Client()


def get_supabase_client():
    """Get a Supabase client instance."""
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase not available, returning mock client")
        return None
        
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.warning("Supabase credentials not configured")
        return None
        
    try:
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None