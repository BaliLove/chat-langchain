#!/usr/bin/env python3
"""
LangSmith Prompt Management System

This script allows you to manage prompts in LangSmith programmatically.
You can push, pull, list, and version control your prompts.

Usage:
    python manage_prompts.py push          # Push all prompts to LangSmith
    python manage_prompts.py pull          # Pull all prompts from LangSmith
    python manage_prompts.py list          # List all prompts in LangSmith
    python manage_prompts.py push-single <name>  # Push single prompt
    python manage_prompts.py pull-single <name>  # Pull single prompt
    python manage_prompts.py compare       # Compare local vs LangSmith prompts
"""

import os
import sys
import logging
from typing import Dict, List, Optional
from datetime import datetime
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import custom prompts as fallback
from retrieval_graph.custom_prompts import (
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

class PromptManager:
    """Manages prompts between local files and LangSmith."""
    
    def __init__(self):
        """Initialize the prompt manager."""
        self.client = Client()
        
        # Import EOS issue prompt
        try:
            from retrieval_graph.eos_issue_prompt import EOS_ISSUE_MANAGEMENT_PROMPT
            eos_prompt_available = True
        except ImportError:
            eos_prompt_available = False
            EOS_ISSUE_MANAGEMENT_PROMPT = ""
        
        # Define prompt mapping: LangSmith name -> local variable
        self.prompt_mapping = {
            "bali-love-router-prompt": ROUTER_SYSTEM_PROMPT,
            "bali-love-generate-queries-prompt": GENERATE_QUERIES_SYSTEM_PROMPT,
            "bali-love-more-info-prompt": MORE_INFO_SYSTEM_PROMPT,
            "bali-love-research-plan-prompt": RESEARCH_PLAN_SYSTEM_PROMPT,
            "bali-love-general-prompt": GENERAL_SYSTEM_PROMPT,
            "bali-love-response-prompt": RESPONSE_SYSTEM_PROMPT,
        }
        
        # Add EOS prompt if available
        if eos_prompt_available:
            self.prompt_mapping["bali-love-eos-issue-prompt"] = EOS_ISSUE_MANAGEMENT_PROMPT
        
        # Descriptions for each prompt
        self.prompt_descriptions = {
            "bali-love-router-prompt": "Routes user queries to research, general, or more-info categories",
            "bali-love-generate-queries-prompt": "Generates 3-5 search queries from user questions",
            "bali-love-more-info-prompt": "Asks for clarification when queries are too vague",
            "bali-love-research-plan-prompt": "Creates step-by-step research plans",
            "bali-love-general-prompt": "Handles general conversation and questions",
            "bali-love-response-prompt": "Generates final responses with retrieved context",
            "bali-love-eos-issue-prompt": "Helps team manage EOS issues - find duplicates, review stale items, track ownership",
        }
    
    def create_chat_prompt(self, system_prompt: str) -> ChatPromptTemplate:
        """Create a ChatPromptTemplate from a system prompt string."""
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template("{input}")
        ])
    
    def push_prompt(self, name: str, prompt_text: str, tags: Optional[List[str]] = None) -> bool:
        """Push a single prompt to LangSmith."""
        try:
            # Create ChatPromptTemplate
            prompt_template = self.create_chat_prompt(prompt_text)
            
            # Add default tags
            if tags is None:
                tags = ["bali-love", "production", f"updated-{datetime.now().strftime('%Y%m%d')}"]
            
            # Push to LangSmith
            self.client.push_prompt(
                name,
                object=prompt_template,
                tags=tags
            )
            
            logger.info(f"✅ Successfully pushed prompt: {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to push prompt {name}: {e}")
            return False
    
    def pull_prompt(self, name: str) -> Optional[str]:
        """Pull a single prompt from LangSmith."""
        try:
            prompt = self.client.pull_prompt(name)
            # Extract the system message template
            system_message = prompt.messages[0].prompt.template
            logger.info(f"✅ Successfully pulled prompt: {name}")
            return system_message
            
        except Exception as e:
            logger.error(f"❌ Failed to pull prompt {name}: {e}")
            return None
    
    def list_prompts(self) -> List[str]:
        """List all prompts in LangSmith."""
        try:
            # Get all prompts (this might need adjustment based on LangSmith API)
            prompts = []
            for prompt_name in self.prompt_mapping.keys():
                try:
                    self.client.pull_prompt(prompt_name)
                    prompts.append(prompt_name)
                except:
                    logger.warning(f"Prompt {prompt_name} not found in LangSmith")
            
            return prompts
            
        except Exception as e:
            logger.error(f"❌ Failed to list prompts: {e}")
            return []
    
    def push_all_prompts(self) -> bool:
        """Push all local prompts to LangSmith."""
        logger.info("🚀 Pushing all prompts to LangSmith...")
        
        success_count = 0
        for name, prompt_text in self.prompt_mapping.items():
            if self.push_prompt(name, prompt_text):
                success_count += 1
        
        logger.info(f"✅ Successfully pushed {success_count}/{len(self.prompt_mapping)} prompts")
        return success_count == len(self.prompt_mapping)
    
    def pull_all_prompts(self) -> Dict[str, str]:
        """Pull all prompts from LangSmith."""
        logger.info("⬇️ Pulling all prompts from LangSmith...")
        
        pulled_prompts = {}
        for name in self.prompt_mapping.keys():
            prompt_text = self.pull_prompt(name)
            if prompt_text:
                pulled_prompts[name] = prompt_text
        
        logger.info(f"✅ Successfully pulled {len(pulled_prompts)} prompts")
        return pulled_prompts
    
    def compare_prompts(self) -> Dict[str, Dict[str, str]]:
        """Compare local prompts with LangSmith prompts."""
        logger.info("🔍 Comparing local and LangSmith prompts...")
        
        comparison = {}
        
        for name, local_prompt in self.prompt_mapping.items():
            remote_prompt = self.pull_prompt(name)
            
            comparison[name] = {
                "local": local_prompt,
                "remote": remote_prompt or "NOT FOUND",
                "matches": local_prompt == remote_prompt if remote_prompt else False
            }
            
            if remote_prompt:
                if local_prompt == remote_prompt:
                    logger.info(f"✅ {name}: Local and remote match")
                else:
                    logger.warning(f"⚠️ {name}: Local and remote differ")
            else:
                logger.error(f"❌ {name}: Not found in LangSmith")
        
        return comparison
    
    def update_local_prompts_file(self, pulled_prompts: Dict[str, str]) -> bool:
        """Update the local custom_prompts.py file with pulled prompts."""
        try:
            # Read current file
            custom_prompts_path = os.path.join(
                os.path.dirname(__file__), 
                "retrieval_graph", 
                "custom_prompts.py"
            )
            
            with open(custom_prompts_path, 'r') as f:
                content = f.read()
            
            # Create mapping from LangSmith names to variable names
            variable_mapping = {
                "bali-love-router-prompt": "ROUTER_SYSTEM_PROMPT",
                "bali-love-generate-queries-prompt": "GENERATE_QUERIES_SYSTEM_PROMPT",
                "bali-love-more-info-prompt": "MORE_INFO_SYSTEM_PROMPT",
                "bali-love-research-plan-prompt": "RESEARCH_PLAN_SYSTEM_PROMPT",
                "bali-love-general-prompt": "GENERAL_SYSTEM_PROMPT",
                "bali-love-response-prompt": "RESPONSE_SYSTEM_PROMPT",
            }
            
            # Update each prompt variable
            for langsmith_name, prompt_text in pulled_prompts.items():
                if langsmith_name in variable_mapping:
                    var_name = variable_mapping[langsmith_name]
                    # Find and replace the variable assignment
                    import re
                    pattern = f'{var_name} = """[^"]*"""'
                    replacement = f'{var_name} = """{prompt_text}"""'
                    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            # Write back to file
            with open(custom_prompts_path, 'w') as f:
                f.write(content)
            
            logger.info("✅ Successfully updated local custom_prompts.py")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update local prompts file: {e}")
            return False

def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    manager = PromptManager()
    command = sys.argv[1].lower()
    
    if command == "push":
        success = manager.push_all_prompts()
        sys.exit(0 if success else 1)
    
    elif command == "pull":
        pulled_prompts = manager.pull_all_prompts()
        if pulled_prompts:
            print("\n📋 Pulled Prompts:")
            for name, prompt in pulled_prompts.items():
                print(f"\n🔹 {name}:")
                print(f"   {prompt[:100]}..." if len(prompt) > 100 else f"   {prompt}")
        sys.exit(0 if pulled_prompts else 1)
    
    elif command == "list":
        prompts = manager.list_prompts()
        print(f"\n📋 Found {len(prompts)} prompts in LangSmith:")
        for prompt in prompts:
            description = manager.prompt_descriptions.get(prompt, "No description")
            print(f"  🔹 {prompt}: {description}")
        sys.exit(0)
    
    elif command == "push-single":
        if len(sys.argv) < 3:
            print("Usage: python manage_prompts.py push-single <prompt-name>")
            sys.exit(1)
        
        name = sys.argv[2]
        if name not in manager.prompt_mapping:
            print(f"❌ Unknown prompt: {name}")
            print(f"Available prompts: {list(manager.prompt_mapping.keys())}")
            sys.exit(1)
        
        success = manager.push_prompt(name, manager.prompt_mapping[name])
        sys.exit(0 if success else 1)
    
    elif command == "pull-single":
        if len(sys.argv) < 3:
            print("Usage: python manage_prompts.py pull-single <prompt-name>")
            sys.exit(1)
        
        name = sys.argv[2]
        prompt = manager.pull_prompt(name)
        if prompt:
            print(f"\n🔹 {name}:")
            print(prompt)
        sys.exit(0 if prompt else 1)
    
    elif command == "compare":
        comparison = manager.compare_prompts()
        print("\n[INFO] Prompt Comparison Results:")
        for name, result in comparison.items():
            status = "MATCH" if result["matches"] else "DIFFER"
            print(f"  {status} {name}")
        sys.exit(0)
    
    elif command == "sync-local":
        pulled_prompts = manager.pull_all_prompts()
        if pulled_prompts:
            success = manager.update_local_prompts_file(pulled_prompts)
            sys.exit(0 if success else 1)
        sys.exit(1)
    
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()