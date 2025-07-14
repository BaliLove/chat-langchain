"""Simple test to verify all prompts are set up"""

from langsmith import Client

client = Client()

prompts_to_check = [
    "bali-love-router-prompt",
    "bali-love-generate-queries-prompt", 
    "bali-love-more-info-prompt",
    "bali-love-research-plan-prompt",
    "bali-love-general-prompt",
    "bali-love-response-prompt"
]

print("Checking prompts...")
all_good = True

for prompt_name in prompts_to_check:
    try:
        prompt = client.pull_prompt(prompt_name)
        print(f"[OK] {prompt_name}")
    except Exception as e:
        print(f"[MISSING] {prompt_name}: {str(e)[:50]}...")
        all_good = False

if all_good:
    print("\nAll prompts ready! You can now commit and deploy.")
else:
    print("\nSome prompts are missing. Please create them in LangSmith.")