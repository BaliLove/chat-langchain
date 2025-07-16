"""
Create Supabase tables for prompt caching
This script creates the necessary tables programmatically
"""

import os
import sys
from supabase import create_client, Client
import requests

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
    print("Please ensure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are set")
    sys.exit(1)

print(f"Connecting to Supabase at {supabase_url}")

# Read SQL file
sql_file = os.path.join(os.path.dirname(__file__), 'create_prompt_tables.sql')
with open(sql_file, 'r') as f:
    sql_content = f.read()

# Unfortunately, the Supabase Python client doesn't support running raw SQL
# We need to use the REST API directly
headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json'
}

# Try to check if tables exist first
supabase: Client = create_client(supabase_url, supabase_key)

# Check if prompts table exists
try:
    result = supabase.table('prompts').select('id').limit(1).execute()
    print("[OK] Tables already exist!")
    print("\nYou can now run: python sync_prompts_simple.py")
except Exception as e:
    if '42P01' in str(e):  # Table doesn't exist
        print("\n[X] Tables don't exist yet.")
        print("\nTo create the tables:")
        print("1. Go to your Supabase dashboard: https://app.supabase.com")
        print("2. Select your project")
        print("3. Navigate to the SQL Editor (left sidebar)")
        print("4. Click 'New query'")
        print("5. Copy and paste the contents of 'create_prompt_tables.sql'")
        print("6. Click 'Run' (or press Ctrl+Enter)")
        print("\nThe SQL file is located at:")
        print(f"   {sql_file}")
        print("\nAfter creating the tables, run:")
        print("   python sync_prompts_simple.py")
    else:
        print(f"Error checking tables: {e}")