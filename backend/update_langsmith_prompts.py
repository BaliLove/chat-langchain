#!/usr/bin/env python3
"""
Update LangSmith prompts with the enhanced Bali Love specific prompts.

This script pushes the updated prompts to LangSmith with proper versioning.
"""

import os
import sys
import logging
from datetime import datetime
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import updated prompts
from retrieval_graph.custom_prompts_updated import (
    ROUTER_SYSTEM_PROMPT,
    GENERATE_QUERIES_SYSTEM_PROMPT,
    MORE_INFO_SYSTEM_PROMPT,
    RESEARCH_PLAN_SYSTEM_PROMPT,
    GENERAL_SYSTEM_PROMPT,
    RESPONSE_SYSTEM_PROMPT,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptUpdater:
    """Updates prompts in LangSmith."""
    
    def __init__(self):
        """Initialize the prompt updater."""
        self.client = Client()
        
        # Define prompt mappings with descriptions
        self.prompt_configs = {
            "bali-love-router-prompt": {
                "template": ROUTER_SYSTEM_PROMPT,
                "description": "Enhanced router for Bali Love queries - handles event codes, messages, vendors",
                "version": "2.0"
            },
            "bali-love-generate-queries-prompt": {
                "template": GENERATE_QUERIES_SYSTEM_PROMPT,
                "description": "Query generator optimized for Bali Love data types",
                "version": "2.0"
            },
            "bali-love-more-info-prompt": {
                "template": MORE_INFO_SYSTEM_PROMPT,
                "description": "Clarification prompter with Bali Love context",
                "version": "2.0"
            },
            "bali-love-research-plan-prompt": {
                "template": RESEARCH_PLAN_SYSTEM_PROMPT,
                "description": "Research planner for Bali Love data searches",
                "version": "2.0"
            },
            "bali-love-general-prompt": {
                "template": GENERAL_SYSTEM_PROMPT,
                "description": "General response for Bali Love team context",
                "version": "2.0"
            },
            "bali-love-response-prompt": {
                "template": RESPONSE_SYSTEM_PROMPT,
                "description": "Response formatter optimized for Bali Love data presentation",
                "version": "2.0"
            }
        }
    
    def create_chat_prompt(self, system_content: str) -> ChatPromptTemplate:
        """Create a chat prompt template from system content."""
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_content)
        ])
    
    def push_prompt(self, name: str, config: dict) -> bool:
        """Push a single prompt to LangSmith."""
        try:
            prompt_template = self.create_chat_prompt(config["template"])
            
            # Push to LangSmith with correct API
            self.client.push_prompt(
                name,
                object=prompt_template,
                tags=[
                    "bali-love",
                    f"version-{config['version']}",
                    f"updated-{datetime.now().strftime('%Y-%m-%d')}",
                    "enhanced-routing",
                    "inbox-support",
                    config["description"]
                ]
            )
            
            logger.info(f"✅ Successfully pushed: {name} (v{config['version']})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to push {name}: {str(e)}")
            return False
    
    def push_all_prompts(self):
        """Push all updated prompts to LangSmith."""
        logger.info("Starting to push updated prompts to LangSmith...")
        logger.info("=" * 60)
        
        success_count = 0
        
        for name, config in self.prompt_configs.items():
            if self.push_prompt(name, config):
                success_count += 1
                logger.info(f"  Description: {config['description']}")
            logger.info("-" * 60)
        
        logger.info(f"\nSummary: {success_count}/{len(self.prompt_configs)} prompts updated successfully")
        
        if success_count == len(self.prompt_configs):
            logger.info("\n✅ All prompts updated successfully!")
            logger.info("\nKey improvements:")
            logger.info("- Router now recognizes event codes and message queries")
            logger.info("- Query generator optimized for Bali Love data types")
            logger.info("- Research planner handles wedding-specific searches")
            logger.info("- Response formatter presents data clearly for the team")
        else:
            logger.warning("\n⚠️ Some prompts failed to update. Check the errors above.")
    
    def verify_prompts(self):
        """Verify that prompts were updated correctly."""
        logger.info("\nVerifying prompts in LangSmith...")
        logger.info("=" * 60)
        
        for name in self.prompt_configs.keys():
            try:
                prompt = self.client.pull_prompt(name)
                logger.info(f"✅ {name} - Found in LangSmith")
                
                # Check if it has our tags
                if hasattr(prompt, 'metadata') and 'tags' in prompt.metadata:
                    tags = prompt.metadata['tags']
                    if 'enhanced-routing' in tags:
                        logger.info("  - Has enhanced routing tag ✓")
                    if 'inbox-support' in tags:
                        logger.info("  - Has inbox support tag ✓")
                        
            except Exception as e:
                logger.error(f"❌ {name} - Not found or error: {str(e)}")


def main():
    """Main function to update prompts."""
    updater = PromptUpdater()
    
    logger.info("Bali Love Prompt Updater")
    logger.info("========================")
    logger.info("This will update all prompts with enhanced Bali Love specific versions.")
    logger.info("Changes include:")
    logger.info("- Better event code recognition")
    logger.info("- Inbox message query support")
    logger.info("- Vendor/venue search optimization")
    logger.info("- Clearer response formatting")
    
    # Push all prompts
    updater.push_all_prompts()
    
    # Verify they were updated
    updater.verify_prompts()
    
    logger.info("\n✅ Update complete!")
    logger.info("\nTo use the new prompts:")
    logger.info("1. Set USE_LANGSMITH_PROMPTS=true in your environment")
    logger.info("2. Restart the application")
    logger.info("3. Test with queries like:")
    logger.info('   - "For KM150726VV, are there any messages that aren\'t replied?"')
    logger.info('   - "Show me all venues in Ubud"')
    logger.info('   - "What are the open issues for event SARLEAD?"')


if __name__ == "__main__":
    main()