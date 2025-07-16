"""
Sync job to update prompt cache from LangSmith
This avoids expensive API calls on every page load
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import asyncpg
from langsmith import Client
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptData(BaseModel):
    id: str
    name: str
    description: str
    template: str
    team: str
    type: str = "prompt"
    category: str
    version: int = 1
    usage_count: int = 0
    last_updated: datetime
    last_modified_by: str
    context_tags: Dict[str, List[str]] = {}

class PromptSyncService:
    def __init__(self, db_url: str, langsmith_api_key: str):
        self.db_url = db_url
        self.langsmith_client = Client(api_key=langsmith_api_key)
        self.db_pool = None
        
    async def init_db_pool(self):
        """Initialize database connection pool"""
        self.db_pool = await asyncpg.create_pool(self.db_url)
        
    async def close_db_pool(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            
    async def sync_prompts(self) -> Dict[str, int]:
        """
        Main sync function - fetch from LangSmith and update Supabase
        Returns: Dict with sync statistics
        """
        try:
            logger.info("Starting prompt sync from LangSmith")
            
            # Update sync status to in_progress
            await self.update_sync_status('in_progress', 'Fetching prompts from LangSmith')
            
            # Fetch prompts from LangSmith
            langsmith_prompts = await self.fetch_langsmith_prompts()
            logger.info(f"Fetched {len(langsmith_prompts)} prompts from LangSmith")
            
            # Update database
            updated_count = await self.update_database(langsmith_prompts)
            
            # Update sync status to success
            await self.update_sync_status('success', f'Successfully synced {updated_count} prompts')
            
            return {
                'fetched': len(langsmith_prompts),
                'updated': updated_count,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            await self.update_sync_status('error', str(e))
            raise
            
    async def fetch_langsmith_prompts(self) -> List[PromptData]:
        """Fetch prompts from LangSmith API"""
        prompts = []
        
        # List of Bali Love prompt IDs
        bali_prompt_ids = [
            'bali-love-router-prompt',
            'bali-love-generate-queries-prompt',
            'bali-love-more-info-prompt',
            'bali-love-research-plan-prompt',
            'bali-love-general-prompt',
            'bali-love-response-prompt',
            'bali-love-eos-issue-prompt'
        ]
        
        for prompt_id in bali_prompt_ids:
            try:
                # Note: Will need to implement when LangSmith API limits reset
                # For now, use the mock data structure
                prompt_data = await self.get_prompt_from_langsmith(prompt_id)
                if prompt_data:
                    prompts.append(prompt_data)
                    
            except Exception as e:
                logger.warning(f"Failed to fetch prompt {prompt_id}: {str(e)}")
                continue
                
        return prompts
        
    async def get_prompt_from_langsmith(self, prompt_id: str) -> Optional[PromptData]:
        """Get single prompt from LangSmith"""
        try:
            # Fetch prompt from LangSmith
            prompt = self.langsmith_client.pull_prompt(prompt_id)
            
            # Extract template from the first message
            template = prompt.messages[0].prompt.template if prompt.messages else ""
            
            # Map prompt IDs to metadata
            prompt_metadata = {
                'bali-love-router-prompt': {
                    'name': 'Router System Prompt',
                    'description': 'Classifies user queries into research, general, or more-info categories',
                    'team': 'All',
                    'category': 'Core System',
                    'context_tags': {
                        'All': ['All'],
                        'Revenue': ['All'],
                        'Client Experience': ['All'],
                        'Digital': ['All']
                    }
                },
                'bali-love-generate-queries-prompt': {
                    'name': 'Generate Queries Prompt',
                    'description': 'Creates 3-5 specific search queries to find relevant information',
                    'team': 'Digital',
                    'category': 'Research',
                    'context_tags': {
                        'All': ['All'],
                        'Digital': ['Documentation', 'Systems'],
                        'Special Projects': ['Research']
                    }
                },
                'bali-love-more-info-prompt': {
                    'name': 'More Information Prompt',
                    'description': 'Requests clarification when queries are too vague or unclear',
                    'team': 'Client Experience',
                    'category': 'Conversation',
                    'context_tags': {
                        'All': ['Communication'],
                        'Client Experience': ['Weddings', 'Corporate Events', 'All']
                    }
                },
                'bali-love-research-plan-prompt': {
                    'name': 'Research Plan Prompt',
                    'description': 'Creates step-by-step research plans to answer questions comprehensively',
                    'team': 'Revenue',
                    'category': 'Research',
                    'context_tags': {
                        'All': ['Events', 'Venues & Vendors'],
                        'Revenue': ['Venues', 'Vendors', 'Packages'],
                        'Client Experience': ['Weddings', 'Corporate Events']
                    }
                },
                'bali-love-general-prompt': {
                    'name': 'General Conversation Prompt',
                    'description': 'Handles general queries and casual conversation',
                    'team': 'Client Experience',
                    'category': 'Conversation',
                    'context_tags': {
                        'All': ['Communication'],
                        'Client Experience': ['All'],
                        'People & Culture': ['Team Info']
                    }
                },
                'bali-love-response-prompt': {
                    'name': 'Response System Prompt',
                    'description': 'Generates comprehensive answers based on retrieved context',
                    'team': 'All',
                    'category': 'Core System',
                    'context_tags': {
                        'All': ['All'],
                        'Revenue': ['All'],
                        'Client Experience': ['All'],
                        'Finance': ['All'],
                        'People & Culture': ['All'],
                        'Digital': ['All'],
                        'Special Projects': ['All']
                    }
                },
                'bali-love-eos-issue-prompt': {
                    'name': 'EOS Issue Management',
                    'description': 'Helps team manage EOS issues - find duplicates, review stale items, track ownership',
                    'team': 'Digital',
                    'category': 'Operations',
                    'context_tags': {
                        'All': ['Tasks & Issues'],
                        'Digital': ['Issues', 'Tasks'],
                        'Finance': ['Reports'],
                        'Client Experience': ['All']
                    }
                }
            }
            
            metadata = prompt_metadata.get(prompt_id, {
                'name': prompt_id,
                'description': 'LangSmith prompt',
                'team': 'All',
                'category': 'General',
                'context_tags': {'All': ['All']}
            })
            
            return PromptData(
                id=prompt_id,
                name=metadata['name'],
                description=metadata['description'],
                team=metadata['team'],
                category=metadata['category'],
                template=template,
                version=1,  # LangSmith doesn't expose version in the API response
                usage_count=0,  # Will be tracked in our database
                last_updated=datetime.now(),
                last_modified_by='system',
                context_tags=metadata['context_tags']
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch prompt {prompt_id} from LangSmith: {str(e)}")
            return None
        
    async def update_database(self, prompts: List[PromptData]) -> int:
        """Update Supabase database with prompt data"""
        updated_count = 0
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for prompt in prompts:
                    try:
                        # Upsert prompt
                        await conn.execute('''
                            INSERT INTO prompts (
                                id, name, description, template, team, type, category, 
                                version, usage_count, last_updated, last_modified_by, context_tags
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                            ON CONFLICT (id) DO UPDATE SET
                                name = EXCLUDED.name,
                                description = EXCLUDED.description,
                                template = EXCLUDED.template,
                                team = EXCLUDED.team,
                                category = EXCLUDED.category,
                                version = EXCLUDED.version,
                                usage_count = EXCLUDED.usage_count,
                                last_updated = EXCLUDED.last_updated,
                                last_modified_by = EXCLUDED.last_modified_by,
                                context_tags = EXCLUDED.context_tags,
                                updated_at = NOW()
                        ''', prompt.id, prompt.name, prompt.description, prompt.template,
                             prompt.team, prompt.type, prompt.category, prompt.version,
                             prompt.usage_count, prompt.last_updated, prompt.last_modified_by,
                             json.dumps(prompt.context_tags))
                        
                        # Add version history if version changed
                        await conn.execute('''
                            INSERT INTO prompt_versions (prompt_id, version, template, modified_by)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (prompt_id, version) DO NOTHING
                        ''', prompt.id, prompt.version, prompt.template, prompt.last_modified_by)
                        
                        updated_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to update prompt {prompt.id}: {str(e)}")
                        continue
                        
        return updated_count
        
    async def update_sync_status(self, status: str, message: str = None):
        """Update sync status in database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO prompt_sync_status (sync_status, error_message, prompts_synced)
                VALUES ($1, $2, $3)
            ''', status, message, 0)
            
    async def cleanup_old_examples(self):
        """Clean up old examples to keep only recent ones"""
        async with self.db_pool.acquire() as conn:
            await conn.execute('SELECT cleanup_old_examples()')
            
async def main():
    """Main sync function"""
    import os
    
    # Get configuration from environment
    db_url = os.getenv('SUPABASE_DB_URL')
    langsmith_api_key = os.getenv('LANGSMITH_API_KEY')
    
    if not db_url or not langsmith_api_key:
        logger.error("Missing required environment variables")
        return
        
    sync_service = PromptSyncService(db_url, langsmith_api_key)
    
    try:
        await sync_service.init_db_pool()
        result = await sync_service.sync_prompts()
        logger.info(f"Sync completed: {result}")
        
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        raise
        
    finally:
        await sync_service.close_db_pool()

if __name__ == "__main__":
    asyncio.run(main())