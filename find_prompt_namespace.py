"""Try different namespace formats to find your prompts"""

from langsmith import Client

client = Client()

# Common namespace patterns to try
# Replace 'username' with your actual LangSmith username
possible_namespaces = [
    "",  # No namespace
    "bali-love",  # Organization name
    "tom",  # Common username
    "tomuser",  # Another possibility
    "default",  # Default namespace
]

prompt_names = [
    "bali-love-router-prompt",
    "router-prompt",  # Maybe without prefix
]

print("Trying to find your prompts with different namespaces...\n")

found_format = None

for namespace in possible_namespaces:
    for prompt_name in prompt_names:
        if namespace:
            full_name = f"{namespace}/{prompt_name}"
        else:
            full_name = prompt_name
            
        try:
            prompt = client.pull_prompt(full_name)
            print(f"[FOUND] {full_name}")
            found_format = namespace
            break
        except:
            # Silently skip
            pass
    
    if found_format is not None:
        break

if found_format is not None:
    print(f"\nYour prompts are using namespace: '{found_format}'")
    print(f"\nUpdate your prompts.py to use this format:")
    
    if found_format:
        print(f'client.pull_prompt("{found_format}/bali-love-router-prompt")')
    else:
        print(f'client.pull_prompt("bali-love-router-prompt")')
else:
    print("\nCould not find your prompts automatically.")
    print("\nPlease check in LangSmith UI:")
    print("1. Go to your prompts in LangSmith")
    print("2. Look at the URL or prompt details")
    print("3. Note the full prompt name including any prefix")
    print("4. Update prompts.py with the correct format")