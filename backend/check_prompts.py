"""
Check what prompts are in the database
"""

import os
from supabase import create_client, Client

# Load environment variables
env_paths = [
    os.path.join(os.path.dirname(__file__), '..', '.env'),
    os.path.join(os.path.dirname(__file__), '..', 'frontend', '.env.local')
]

for env_path in env_paths:
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Get Supabase credentials
supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')

# Create client
supabase: Client = create_client(supabase_url, supabase_key)

print("Checking prompts in database...\n")

# Get all prompts
result = supabase.table('prompts').select('*').execute()

if result.data:
    print(f"Found {len(result.data)} prompts:")
    for prompt in result.data:
        print(f"\n- {prompt['id']}")
        print(f"  Name: {prompt['name']}")
        print(f"  Team: {prompt['team']}")
        print(f"  Active: {prompt.get('is_active', 'Not set')}")
else:
    print("No prompts found in database")

# Check with is_active filter
active_result = supabase.table('prompts').select('*').eq('is_active', True).execute()
print(f"\n\nActive prompts: {len(active_result.data) if active_result.data else 0}")