"""
Simple sync script to populate Supabase with LangSmith prompts
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from langsmith import Client
from supabase import create_client, Client as SupabaseClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptSyncService:
    def __init__(self):
        # Load environment variables from multiple locations
        env_paths = [
            os.path.join(os.path.dirname(__file__), '..', '.env'),  # Root .env
            os.path.join(os.path.dirname(__file__), '..', 'frontend', '.env.local')  # Frontend .env.local
        ]
        
        for env_path in env_paths:
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value
        
        # Get environment variables
        self.supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        # Try service role key first (needed for writes), fall back to anon key
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        self.langsmith_api_key = os.getenv('LANGSMITH_API_KEY')
        
        # Log which key we're using (without exposing the actual key)
        if os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
            print("Using service role key for Supabase (required for sync)")
        else:
            print("Warning: Using anon key - sync may fail due to RLS policies")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(f"Missing Supabase configuration. URL: {self.supabase_url}, Key: {'***' if self.supabase_key else None}")
            
        # Initialize clients
        self.supabase: SupabaseClient = create_client(self.supabase_url, self.supabase_key)
        self.langsmith_client = Client(api_key=self.langsmith_api_key)
        
    def sync_prompts(self) -> Dict[str, int]:
        """Main sync function - fetch from LangSmith and update Supabase"""
        try:
            logger.info("Starting prompt sync from LangSmith")
            
            # Update sync status
            self.update_sync_status('in_progress', 'Fetching prompts from LangSmith')
            
            # Fetch prompts from LangSmith
            prompts = self.fetch_langsmith_prompts()
            logger.info(f"Fetched {len(prompts)} prompts from LangSmith")
            
            # Update database
            updated_count = self.update_database(prompts)
            
            # Update sync status to success
            self.update_sync_status('success', f'Successfully synced {updated_count} prompts')
            
            return {
                'fetched': len(prompts),
                'updated': updated_count,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            self.update_sync_status('error', str(e))
            raise
            
    def fetch_langsmith_prompts(self) -> List[Dict]:
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
            'bali-love-eos-issue-prompt',
            'bali-love-issue-review'
        ]
        
        for prompt_id in bali_prompt_ids:
            try:
                prompt_data = self.get_prompt_from_langsmith(prompt_id)
                if prompt_data:
                    prompts.append(prompt_data)
                    
            except Exception as e:
                logger.warning(f"Failed to fetch prompt {prompt_id}: {str(e)}")
                continue
                
        return prompts
        
    def get_prompt_from_langsmith(self, prompt_id: str) -> Optional[Dict]:
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
                },
                'bali-love-issue-review': {
                    'name': 'Issue Category Review',
                    'description': 'Interactive weekly issue review by category - generates comprehensive reports with actionable insights',
                    'team': 'Operations',
                    'category': 'Operations',
                    'context_tags': {
                        'All': ['Issues', 'Weekly Review'],
                        'Operations': ['Issue Management', 'Category Review'],
                        'Digital': ['Systems & Tools'],
                        'Client Experience': ['Customer Service']
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
            
            return {
                'id': prompt_id,
                'name': metadata['name'],
                'description': metadata['description'],
                'team': metadata['team'],
                'category': metadata['category'],
                'template': template,
                'version': 1,
                'usage_count': 0,
                'last_updated': datetime.now().isoformat(),
                'last_modified_by': 'system',
                'context_tags': json.dumps(metadata['context_tags'])
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch prompt {prompt_id} from LangSmith: {str(e)}")
            return None
        
    def update_database(self, prompts: List[Dict]) -> int:
        """Update Supabase database with prompt data"""
        updated_count = 0
        
        for prompt in prompts:
            try:
                # Check if prompt exists
                existing = self.supabase.table('prompts').select('id').eq('id', prompt['id']).execute()
                
                if existing.data:
                    # Update existing prompt
                    result = self.supabase.table('prompts').update(prompt).eq('id', prompt['id']).execute()
                else:
                    # Insert new prompt
                    result = self.supabase.table('prompts').insert(prompt).execute()
                
                if result.data:
                    updated_count += 1
                    logger.info(f"Updated prompt: {prompt['id']}")
                    
            except Exception as e:
                logger.error(f"Failed to update prompt {prompt['id']}: {str(e)}")
                continue
                
        return updated_count
        
    def update_sync_status(self, status: str, message: str = None):
        """Update sync status in database"""
        try:
            sync_data = {
                'last_sync_at': datetime.now().isoformat(),
                'sync_status': status,
                'error_message': message,
                'prompts_synced': 0
            }
            
            self.supabase.table('prompt_sync_status').insert(sync_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to update sync status: {str(e)}")

def main():
    """Main sync function"""
    try:
        sync_service = PromptSyncService()
        result = sync_service.sync_prompts()
        logger.info(f"Sync completed: {result}")
        
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()