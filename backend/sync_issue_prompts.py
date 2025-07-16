"""Sync issue-specific prompts to LangSmith"""
import os
from langsmith import Client
from dotenv import load_dotenv
from retrieval_graph.issue_category_review_prompt import (
    ISSUE_CATEGORY_REVIEW_PROMPT,
    CATEGORY_OWNER_ACTION_PROMPT,
    CATEGORY_PROMPTS,
    PROMPT_METADATA
)

# Load environment variables
load_dotenv()

def sync_issue_prompts():
    """Sync all issue-related prompts to LangSmith"""
    client = Client()
    
    # Single interactive issue review prompt
    prompts_to_sync = [
        {
            "name": "bali-love-issue-review",
            "template": ISSUE_CATEGORY_REVIEW_PROMPT,
            "metadata": {
                "name": "Issue Category Review",
                "description": "Interactive weekly issue review assistant - guides through category selection and generates comprehensive reports",
                "version": 1,
                "team": "Operations",
                "tags": ["issues", "review", "weekly", "operations", "interactive"],
                "category": "Operations",
                "type": "prompt"
            }
        }
    ]
    
    # Sync each prompt
    for prompt_config in prompts_to_sync:
        try:
            # Check if prompt exists
            try:
                existing = client.pull_prompt(prompt_config["name"])
                print(f"Updating existing prompt: {prompt_config['name']}")
                # Update the prompt
                from langchain_core.prompts import ChatPromptTemplate
                prompt_obj = ChatPromptTemplate.from_template(prompt_config["template"])
                client.push_prompt(
                    prompt_config["name"],
                    object=prompt_obj,
                    is_public=False,
                    description=prompt_config["metadata"].get("description", ""),
                    tags=prompt_config["metadata"].get("tags", [])
                )
            except:
                print(f"Creating new prompt: {prompt_config['name']}")
                # Create new prompt
                from langchain_core.prompts import ChatPromptTemplate
                prompt_obj = ChatPromptTemplate.from_template(prompt_config["template"])
                client.push_prompt(
                    prompt_config["name"],
                    object=prompt_obj,
                    is_public=False,
                    description=prompt_config["metadata"].get("description", ""),
                    tags=prompt_config["metadata"].get("tags", [])
                )
            
            print(f"Successfully synced: {prompt_config['name']}")
            
        except Exception as e:
            print(f"Error syncing {prompt_config['name']}: {str(e)}")
    
    print("\nPrompt sync complete!")
    print(f"Total prompts synced: {len(prompts_to_sync)}")

if __name__ == "__main__":
    sync_issue_prompts()