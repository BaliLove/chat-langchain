"""
Setup Supabase tables for prompt caching
"""

import os
from supabase import create_client, Client

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', '.env.local')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Get Supabase credentials
supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
supabase_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("Error: Missing Supabase configuration")
    exit(1)

# Create client
supabase: Client = create_client(supabase_url, supabase_key)

print(f"Connected to Supabase at {supabase_url}")
print("\nTo create the tables, please:")
print("1. Go to your Supabase dashboard: https://app.supabase.com")
print("2. Select your project")
print("3. Navigate to the SQL Editor")
print("4. Create a new query")
print("5. Copy and paste the contents of 'create_prompt_tables.sql'")
print("6. Click 'Run' to execute the SQL")
print("\nAlternatively, you can use the Supabase CLI if you have it installed.")
print("\nOnce the tables are created, run 'python sync_prompts_simple.py' again.")