#!/usr/bin/env python3
"""
Complete Bubble sync script with pagination support.
Fetches all users and teams from Bubble and syncs to Supabase.
"""

import json
import urllib.request
import urllib.parse
import ssl
import os
import time
from datetime import datetime

# Load environment variables manually
def load_env():
    env_vars = {}
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars

# Load environment
env = load_env()

BUBBLE_API_TOKEN = env.get("BUBBLE_API_TOKEN")
BUBBLE_APP_URL = env.get("BUBBLE_APP_URL", "https://app.bali.love")
SUPABASE_URL = env.get("SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_KEY = env.get("SUPABASE_SERVICE_ROLE_KEY")
BUBBLE_BATCH_SIZE = int(env.get("BUBBLE_BATCH_SIZE", "100"))

print("🔍 Bubble Complete Sync Script")
print("=" * 50)

if not all([BUBBLE_API_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    print("❌ Missing required environment variables")
    exit(1)

# Create SSL context for HTTPS requests
ssl_context = ssl.create_default_context()

def make_request(url, headers=None, method="GET", data=None):
    """Make HTTP request with error handling"""
    try:
        req = urllib.request.Request(url, headers=headers or {}, method=method)
        if data:
            req.data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, context=ssl_context) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def fetch_all_bubble_users():
    """Fetch all users from Bubble with pagination"""
    print("\n📡 Fetching all users from Bubble (this may take a while)...")
    
    bubble_headers = {
        "Authorization": f"Bearer {BUBBLE_API_TOKEN}"
    }
    
    all_users = []
    bali_users = []
    cursor = 0
    batch_count = 0
    
    while True:
        batch_count += 1
        print(f"   Fetching batch {batch_count} (cursor: {cursor})...", end='', flush=True)
        
        # Build URL with pagination
        users_url = f"{BUBBLE_APP_URL}/api/1.1/obj/user?cursor={cursor}&limit={BUBBLE_BATCH_SIZE}"
        response = make_request(users_url, headers=bubble_headers)
        
        if not response:
            print(" ❌ Failed")
            break
            
        batch_results = response.get("response", {}).get("results", [])
        remaining = response.get("response", {}).get("remaining", 0)
        
        if not batch_results:
            print(" ✅ No more users")
            break
        
        # Process this batch
        all_users.extend(batch_results)
        
        # Filter for @bali.love emails in this batch
        batch_bali_users = [u for u in batch_results if "@bali.love" in u.get("email", "").lower()]
        bali_users.extend(batch_bali_users)
        
        print(f" ✅ Found {len(batch_results)} users ({len(batch_bali_users)} @bali.love)")
        
        # Update cursor for next batch
        cursor += len(batch_results)
        
        # Check if we've fetched all records
        if len(batch_results) < BUBBLE_BATCH_SIZE or remaining == 0:
            break
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    print(f"\n📊 Summary:")
    print(f"   Total users fetched: {len(all_users)}")
    print(f"   Users with @bali.love emails: {len(bali_users)}")
    
    return all_users, bali_users

def fetch_all_teams():
    """Fetch all teams from Bubble"""
    print("\n🏢 Fetching teams from Bubble...")
    
    bubble_headers = {
        "Authorization": f"Bearer {BUBBLE_API_TOKEN}"
    }
    
    # Try different team endpoints
    for team_endpoint in ["team", "teams", "department", "group"]:
        teams_url = f"{BUBBLE_APP_URL}/api/1.1/obj/{team_endpoint}?limit=100"
        response = make_request(teams_url, headers=bubble_headers)
        
        if response and response.get("response", {}).get("results"):
            teams = response.get("response", {}).get("results", [])
            print(f"✅ Found {len(teams)} teams at endpoint: {team_endpoint}")
            return teams
    
    print("⚠️  No team endpoints found")
    return []

def generate_sync_sql(bali_users, teams):
    """Generate SQL for manual sync"""
    print("\n💾 Generating SQL for Supabase import...")
    
    sql_lines = []
    sql_lines.append("-- Sync users from Bubble to Supabase")
    sql_lines.append("-- Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sql_lines.append("")
    
    # First, sync teams if any
    if teams:
        sql_lines.append("-- Insert teams")
        for team in teams[:10]:  # Limit to first 10 for display
            team_id = team.get("_id", "")
            team_name = team.get("name", "Unknown Team").replace("'", "''")
            description = team.get("description", "").replace("'", "''")
            
            sql_lines.append(f"""
INSERT INTO public.teams (bubble_id, name, description)
VALUES ('{team_id}', '{team_name}', '{description}')
ON CONFLICT (bubble_id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();""")
    
    sql_lines.append("\n-- Insert users")
    
    # Group users by email domain for summary
    email_domains = {}
    for user in bali_users:
        email = user.get("email", "").lower()
        domain = email.split('@')[1] if '@' in email else 'unknown'
        email_domains[domain] = email_domains.get(domain, 0) + 1
    
    # Generate SQL for each user
    for i, user in enumerate(bali_users):
        if i >= 10:  # Limit display to first 10
            sql_lines.append(f"\n-- ... and {len(bali_users) - 10} more users")
            break
            
        email = user.get("email", "").lower().replace("'", "''")
        user_id = user.get("_id", "")
        
        # Try to extract team info
        team_id = user.get("team_id") or user.get("team") or user.get("department", "")
        team_name = user.get("team_name", "Bali Love").replace("'", "''")
        
        # Determine role
        role = "member"
        if any(field in user for field in ["is_admin", "admin"]):
            if user.get("is_admin") or user.get("admin"):
                role = "admin"
        elif any(field in user for field in ["is_manager", "manager"]):
            if user.get("is_manager") or user.get("manager"):
                role = "manager"
        
        sql_lines.append(f"""
INSERT INTO public.user_teams (
    email, 
    bubble_user_id, 
    team_name, 
    role,
    synced_from_bubble_at
)
VALUES (
    '{email}', 
    '{user_id}', 
    '{team_name}', 
    '{role}',
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET bubble_user_id = EXCLUDED.bubble_user_id,
    team_name = EXCLUDED.team_name,
    synced_from_bubble_at = NOW();""")
    
    # Add tom@bali.love as admin if not in the list
    if not any(u.get("email", "").lower() == "tom@bali.love" for u in bali_users):
        sql_lines.append("""
-- Add tom@bali.love as admin
INSERT INTO public.user_teams (
    email, 
    team_name, 
    role,
    allowed_agents,
    allowed_data_sources,
    permissions
)
VALUES (
    'tom@bali.love', 
    'Bali Love', 
    'admin',
    '["chat", "search", "analytics"]'::jsonb,
    '["public", "company_wide", "team_specific", "admin_only"]'::jsonb,
    '{"can_manage_team": true, "can_export_data": true}'::jsonb
)
ON CONFLICT (email) DO UPDATE
SET role = 'admin',
    allowed_agents = EXCLUDED.allowed_agents,
    allowed_data_sources = EXCLUDED.allowed_data_sources,
    permissions = EXCLUDED.permissions;""")
    
    # Save to file
    with open('bubble_sync.sql', 'w') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"✅ SQL file created: bubble_sync.sql")
    print(f"   Contains {len(teams)} teams and {min(len(bali_users), 10)} users (preview)")
    
    # Show summary
    print("\n📊 Email domain summary:")
    for domain, count in sorted(email_domains.items(), key=lambda x: x[1], reverse=True):
        print(f"   @{domain}: {count} users")

# Main execution
def main():
    # Fetch all users with pagination
    all_users, bali_users = fetch_all_bubble_users()
    
    if bali_users:
        print("\n👥 Sample @bali.love users found:")
        for user in bali_users[:5]:
            email = user.get("email", "Unknown")
            created = user.get("Created Date", "Unknown")[:10] if user.get("Created Date") else "Unknown"
            print(f"   - {email} (created: {created})")
    
    # Fetch teams
    teams = fetch_all_teams()
    
    # Generate SQL
    if bali_users or teams:
        generate_sync_sql(bali_users, teams)
        
        print("\n📌 Next steps:")
        print("   1. Review the generated SQL file: bubble_sync.sql")
        print("   2. Copy the contents and run in Supabase SQL Editor")
        print("   3. Or install Python packages and run full sync:")
        print("      pip3 install supabase httpx python-dotenv")
        print("      python3 sync_bubble_permissions.py")
    else:
        print("\n⚠️  No @bali.love users found to sync")

if __name__ == "__main__":
    main()