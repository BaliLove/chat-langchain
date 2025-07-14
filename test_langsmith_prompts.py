"""Test if LangSmith prompts are set up correctly"""

import os
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

def test_prompts():
    """Test if the new Bali prompts exist in LangSmith"""
    
    client = Client()
    
    # List of prompts we expect to exist
    expected_prompts = [
        "bali-love-router-prompt",
        "bali-love-generate-queries-prompt", 
        "bali-love-more-info-prompt",
        "bali-love-research-plan-prompt",
        "bali-love-general-prompt",
        "bali-love-response-prompt"
    ]
    
    print("=== Testing LangSmith Prompts ===\n")
    
    found_prompts = []
    missing_prompts = []
    
    for prompt_name in expected_prompts:
        try:
            print(f"Checking: {prompt_name}")
            prompt = client.pull_prompt(prompt_name)
            
            # Get the template content
            template = prompt.messages[0].prompt.template
            
            print(f"  ✓ Found! Length: {len(template)} chars")
            
            # Show preview
            preview = template[:100] + "..." if len(template) > 100 else template
            print(f"  Preview: {preview}\n")
            
            found_prompts.append(prompt_name)
            
        except Exception as e:
            print(f"  ✗ Not found: {e}\n")
            missing_prompts.append(prompt_name)
    
    print("\n=== Summary ===")
    print(f"Found: {len(found_prompts)}/{len(expected_prompts)} prompts")
    
    if missing_prompts:
        print(f"\nMissing prompts:")
        for prompt in missing_prompts:
            print(f"  - {prompt}")
        print(f"\nPlease create these in LangSmith UI")
    else:
        print("\n✓ All prompts are set up correctly!")
        print("\nYou can now:")
        print("1. Update backend/retrieval_graph/prompts.py with prompts_updated.py")
        print("2. Commit and push to deploy")
        print("3. Test venue queries in your chatbot")
    
    # Also check if we can pull the old prompts (for comparison)
    print("\n=== Old Prompts Check ===")
    old_prompt = "langchain-ai/chat-langchain-router-prompt"
    try:
        prompt = client.pull_prompt(old_prompt)
        print(f"Old prompt still accessible: {old_prompt}")
        print("Make sure to update the code to use new prompt names!")
    except:
        print("Old prompts not accessible (this is fine)")


if __name__ == "__main__":
    test_prompts()