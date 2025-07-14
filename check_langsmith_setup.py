"""Check LangSmith setup and existing prompts"""

import os
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

print("=== LangSmith Configuration ===")
print(f"API Key: {'Set' if os.getenv('LANGSMITH_API_KEY') else 'Not set'}")
print(f"Project: {os.getenv('LANGSMITH_PROJECT', 'Not set')}")

try:
    client = Client()
    
    # Try to pull an existing prompt to verify connection
    print("\n=== Testing Connection ===")
    try:
        # Try the old LangChain prompt
        prompt = client.pull_prompt("langchain-ai/chat-langchain-router-prompt")
        print("Successfully pulled existing LangChain prompt")
        print("Connection to LangSmith is working!")
        
        # Check the structure
        print(f"\nPrompt structure:")
        print(f"- Type: {type(prompt)}")
        print(f"- Has messages: {'messages' in dir(prompt)}")
        
    except Exception as e:
        print(f"Could not pull LangChain prompt: {e}")
    
    # Try to list prompts (this might not work due to permissions)
    print("\n=== Checking for Your Prompts ===")
    print("Note: Your prompts might need a namespace prefix")
    print("Common formats:")
    print("- your-username/prompt-name")
    print("- your-org/prompt-name")
    print("- just prompt-name")
    
    # Get info about the current session
    try:
        # This might help identify the correct namespace
        print("\nTrying to identify your namespace...")
        # LangSmith client doesn't expose user info directly
        # but we can infer from the project name
        project = os.getenv('LANGSMITH_PROJECT', '')
        if project:
            print(f"Your project: {project}")
            # Project names often contain username/org info
            
    except Exception as e:
        print(f"Could not get session info: {e}")
    
except Exception as e:
    print(f"\nError initializing LangSmith client: {e}")
    print("\nMake sure LANGSMITH_API_KEY is set correctly in .env")