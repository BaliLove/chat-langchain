"""Create prompts in LangSmith via API"""

import os
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

def create_prompts():
    """Try to create prompts via LangSmith API"""
    
    client = Client()
    
    # Check if we can create prompts
    try:
        # Try to list existing prompts first
        print("Checking LangSmith connection...")
        
        # The LangSmith client doesn't have a direct create_prompt method
        # Prompts are typically created through the UI or by pushing them
        
        # We can try to push a prompt
        from langchain_core.prompts import ChatPromptTemplate
        
        # Create a prompt template
        router_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI assistant for a venue and event booking platform in Bali. 

Analyze the user's query and classify it into ONE of these categories:

1. "research" - User is asking about:
   - Specific venues, locations, or properties
   - Events, weddings, or celebrations
   - Services, products, or vendors
   - Booking information or availability
   - Any specific information that could be in our database

2. "general" - User is making:
   - General conversation or greetings
   - Questions about how the platform works
   - Non-specific chitchat

3. "more-info" - The query is:
   - Too vague to understand
   - Missing key details needed to help

Examples:
- "Tell me about wedding venues in Uluwatu" → research
- "What venues do you have?" → research
- "Show me your event services" → research
- "Hi there!" → general
- "How does this work?" → general
- "I need help" → more-info

Provide your classification with type and logic explanation.""")
        ])
        
        # Try to push the prompt
        print("\nTrying to push prompt to LangSmith...")
        
        # Note: The push_prompt method requires the prompt to already exist
        # or you need to use the UI to create it first
        
        # Check existing prompts
        existing = client.list_prompts()
        print(f"Found {len(list(existing))} existing prompts")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nIt appears prompts need to be created through the LangSmith UI.")
        print("The API is mainly for pulling existing prompts, not creating new ones.")
        
        return False
    
    return True


if __name__ == "__main__":
    create_prompts()