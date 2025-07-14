"""Run Supabase migration for staging tables"""

import os
from supabase import create_client

# Get environment variables
supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    print("Missing Supabase credentials in environment")
    exit(1)

# Create client
supabase = create_client(supabase_url, supabase_key)

# Read migration file
with open("supabase/migrations/003_data_staging_tables.sql", "r") as f:
    migration_sql = f.read()

try:
    # Execute migration
    # Note: Supabase Python client doesn't have direct SQL execution
    # You should run this through Supabase dashboard or use psql directly
    print("Please run the following migration through Supabase SQL Editor:")
    print("=" * 80)
    print(migration_sql)
    print("=" * 80)
    print("\nAlternatively, run this command:")
    print(f"psql {os.getenv('DATABASE_URL')} -f supabase/migrations/003_data_staging_tables.sql")
    
except Exception as e:
    print(f"Error: {e}")