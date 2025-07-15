#!/usr/bin/env python3
"""
Deploy Prompts to LangSmith

This script deploys prompts to LangSmith with versioning and tagging.
Use this as part of your CI/CD pipeline.

Usage:
    python scripts/deploy_prompts.py [--env production|staging|dev] [--tag custom-tag]
"""

import os
import sys
import argparse
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from manage_prompts import PromptManager

def deploy_prompts(environment: str = "production", custom_tag: str = None):
    """Deploy prompts to LangSmith with appropriate tags."""
    
    print(f"🚀 Deploying prompts to LangSmith ({environment})...")
    
    # Initialize manager
    manager = PromptManager()
    
    # Create environment-specific tags
    tags = [
        "bali-love",
        environment,
        f"deployed-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        f"git-{get_git_commit()[:8]}" if get_git_commit() else "no-git"
    ]
    
    if custom_tag:
        tags.append(custom_tag)
    
    # Deploy each prompt with tags
    success_count = 0
    for name, prompt_text in manager.prompt_mapping.items():
        if manager.push_prompt(name, prompt_text, tags):
            success_count += 1
        else:
            print(f"❌ Failed to deploy {name}")
    
    if success_count == len(manager.prompt_mapping):
        print(f"✅ Successfully deployed all {success_count} prompts to {environment}")
        return True
    else:
        print(f"⚠️ Deployed {success_count}/{len(manager.prompt_mapping)} prompts")
        return False

def get_git_commit():
    """Get current git commit hash."""
    try:
        import subprocess
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    except:
        return None

def main():
    parser = argparse.ArgumentParser(description='Deploy prompts to LangSmith')
    parser.add_argument('--env', choices=['production', 'staging', 'dev'], 
                       default='production', help='Environment to deploy to')
    parser.add_argument('--tag', help='Custom tag to add to prompts')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be deployed without actually deploying')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN - Would deploy the following prompts:")
        manager = PromptManager()
        for name in manager.prompt_mapping.keys():
            print(f"  • {name}")
        return
    
    # Check environment variables
    if not os.getenv('LANGSMITH_API_KEY'):
        print("❌ LANGSMITH_API_KEY environment variable not set")
        sys.exit(1)
    
    # Deploy prompts
    success = deploy_prompts(args.env, args.tag)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()