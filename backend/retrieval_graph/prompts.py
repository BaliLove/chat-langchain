"""Default prompts."""

import logging
import os

logger = logging.getLogger(__name__)

# ALWAYS use LangSmith prompts - no fallbacks
from langsmith import Client

try:
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
    logger.info("Successfully loaded LangSmith prompts")
except Exception as e:
    logger.error(f"CRITICAL: Failed to load LangSmith prompts: {e}")
    # Raise the exception to prevent the app from starting without LangSmith prompts
    raise RuntimeError(f"Cannot start application without LangSmith prompts: {e}")
