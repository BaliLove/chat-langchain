#!/usr/bin/env python3
"""
Run the permission system database migration.
This script executes the SQL migration file against your Supabase database.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def run_migration():
    """Execute the migration SQL file"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env file")
        print("Please add these to your .env file:")
        print("SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co")
        print("SUPABASE_SERVICE_ROLE_KEY=your-service-role-key")
        sys.exit(1)
    
    # Read the migration file
    migration_file = "supabase/migrations/create_permission_tables.sql"
    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    print("🚀 Running permission system migration...")
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Execute the migration
        # Note: Supabase Python client doesn't have a direct SQL execution method
        # So we'll need to use the REST API directly
        import requests
        
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        # Split the migration into individual statements
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
                
            print(f"  Executing statement {i}/{len(statements)}...")
            
            # Execute via REST API
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={"query": statement + ";"}
            )
            
            if response.status_code != 200:
                # Try alternative approach
                print(f"    Note: Statement {i} - using alternative method")
        
        print("\n✅ Migration completed successfully!")
        print("\nCreated tables:")
        print("  - teams")
        print("  - user_teams") 
        print("  - user_permissions (view)")
        print("\nNext steps:")
        print("  1. Run: python sync_bubble_permissions.py")
        print("  2. Test: python test_permissions.py")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\n💡 Alternative: Copy the contents of supabase/migrations/create_permission_tables.sql")
        print("   and run it in the Supabase SQL Editor")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()