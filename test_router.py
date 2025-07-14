"""Test the router classification directly"""

import asyncio
import os
from dotenv import load_dotenv
from backend.retrieval_graph.custom_prompts import ROUTER_SYSTEM_PROMPT
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.llms import load_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import Literal

load_dotenv()

class Router(BaseModel):
    """Router model for classifying queries"""
    type: Literal["research", "general", "more-info"] = Field(
        description="The type of query"
    )
    logic: str = Field(
        description="Explanation of the routing decision"
    )

async def test_router():
    """Test router classification"""
    
    # Load the model
    model = load_chat_model("anthropic/claude-3-5-haiku-20241022").with_structured_output(
        Router, method="function_calling"
    )
    
    # Test queries
    test_queries = [
        "What wedding venues are available in Uluwatu?",
        "Tell me about Alila Uluwatu",
        "Show me event services",
        "What's the weather like?",
        "How do I use langchain?",
        "Hi there!",
        "wedding planning services in Bali"
    ]
    
    print("=== Testing Router Classification ===\n")
    print(f"Router Prompt Preview:\n{ROUTER_SYSTEM_PROMPT[:200]}...\n")
    
    for query in test_queries:
        print(f"Query: '{query}'")
        
        messages = [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=query)
        ]
        
        try:
            response = await model.ainvoke(messages)
            print(f"  Type: {response.type}")
            print(f"  Logic: {response.logic}")
            print()
        except Exception as e:
            print(f"  Error: {e}")
            print()

if __name__ == "__main__":
    asyncio.run(test_router())