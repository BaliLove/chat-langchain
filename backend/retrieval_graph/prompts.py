"""Default prompts."""

import logging
import os

logger = logging.getLogger(__name__)

# Check if we should use LangSmith prompts or custom prompts
USE_LANGSMITH_PROMPTS = os.getenv("USE_LANGSMITH_PROMPTS", "false").lower() == "true"

if USE_LANGSMITH_PROMPTS:
    try:
        from langsmith import Client
        client = Client()
        # fetch from langsmith
        ROUTER_SYSTEM_PROMPT = (
            client.pull_prompt("bali-love-router-prompt")
            .messages[0]
            .prompt.template
        )
        GENERATE_QUERIES_SYSTEM_PROMPT = (
            client.pull_prompt("bali-love-generate-queries-prompt")
            .messages[0]
            .prompt.template
        )
        MORE_INFO_SYSTEM_PROMPT = (
            client.pull_prompt("bali-love-more-info-prompt")
            .messages[0]
            .prompt.template
        )
        RESEARCH_PLAN_SYSTEM_PROMPT = (
            client.pull_prompt("bali-love-research-plan-prompt")
            .messages[0]
            .prompt.template
        )
        GENERAL_SYSTEM_PROMPT = (
            client.pull_prompt("bali-love-general-prompt")
            .messages[0]
            .prompt.template
        )
        RESPONSE_SYSTEM_PROMPT = (
            client.pull_prompt("bali-love-response-prompt")
            .messages[0]
            .prompt.template
        )
        logger.info("Using LangSmith prompts")
    except Exception as e:
        logger.warning(f"Failed to load LangSmith prompts: {e}. Using custom prompts.")
        USE_LANGSMITH_PROMPTS = False

if not USE_LANGSMITH_PROMPTS:
    # Use custom prompts
    from backend.retrieval_graph.custom_prompts import (
        ROUTER_SYSTEM_PROMPT,
        GENERATE_QUERIES_SYSTEM_PROMPT,
        MORE_INFO_SYSTEM_PROMPT,
        RESEARCH_PLAN_SYSTEM_PROMPT,
        GENERAL_SYSTEM_PROMPT,
        RESPONSE_SYSTEM_PROMPT
    )
    logger.info("Using custom prompts")
