#!/usr/bin/env python3
"""
Bubble sync script that handles nested email structure.
The email is stored in authentication.email.email
"""

import json
import urllib.request
import ssl
import os
import time
from datetime import datetime

# Load environment variables
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

env = load_env()
BUBBLE_API_TOKEN = env.get("BUBBLE_API_TOKEN")
BUBBLE_APP_URL = env.get("BUBBLE_APP_URL", "https://app.bali.love")
SUPABASE_URL = env.get("SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL")
BUBBLE_BATCH_SIZE = int(env.get("BUBBLE_BATCH_SIZE", "100"))

ssl_context = ssl.create_default_context()

def make_request(url, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, context=ssl_context) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def get_user_email(user):
    """Extract email from nested authentication structure"""
    try:
        auth = user.get("authentication", {})
        if isinstance(auth, str):
            # Try to parse if it's a JSON string
            try:
                auth = json.loads(auth.replace("'", '"'))
            except:
                return None
        
        email_obj = auth.get("email", {})
        if isinstance(email_obj, dict):
            return email_obj.get("email", "").lower()
    except:
        pass
    
    # Fallback to direct email field if it exists
    return user.get("email", "").lower()

def fetch_bali_users_paginated():
    """Fetch all users with @bali.love emails using pagination"""
    print("\n📡 Fetching users from Bubble...")
    
    bubble_headers = {"Authorization": f"Bearer {BUBBLE_API_TOKEN}"}
    all_users = []
    bali_users = []
    cursor = 0
    batch_count = 0
    
    while True:
        batch_count += 1
        print(f"   Batch {batch_count} (cursor: {cursor})...", end='', flush=True)
        
        users_url = f"{BUBBLE_APP_URL}/api/1.1/obj/user?cursor={cursor}&limit={BUBBLE_BATCH_SIZE}"
        response = make_request(users_url, headers=bubble_headers)
        
        if not response:
            print(" ❌ Failed")
            break
            
        batch_results = response.get("response", {}).get("results", [])
        
        if not batch_results:
            print(" ✅ Complete")
            break
        
        # Process users and extract emails
        batch_bali_count = 0
        for user in batch_results:
            email = get_user_email(user)
            if email and "@bali.love" in email:
                user["extracted_email"] = email  # Store for easy access
                bali_users.append(user)
                batch_bali_count += 1
        
        all_users.extend(batch_results)
        print(f" ✅ {len(batch_results)} users ({batch_bali_count} @bali.love)")
        
        cursor += len(batch_results)
        
        if len(batch_results) < BUBBLE_BATCH_SIZE:
            break
        
        time.sleep(0.3)  # Rate limiting
    
    print(f"\n📊 Found {len(bali_users)} users with @bali.love emails out of {len(all_users)} total")
    return bali_users

def fetch_teams():
    """Fetch teams from Bubble"""
    print("\n🏢 Fetching teams...")
    bubble_headers = {"Authorization": f"Bearer {BUBBLE_API_TOKEN}"}
    
    for endpoint in ["team", "teams", "department", "group"]:
        url = f"{BUBBLE_APP_URL}/api/1.1/obj/{endpoint}?limit=100"
        response = make_request(url, headers=bubble_headers)
        
        if response and response.get("response", {}).get("results"):
            teams = response.get("response", {}).get("results", [])
            print(f"✅ Found {len(teams)} teams")
            return teams
    
    print("⚠️  No teams found")
    return []

def generate_sql(bali_users, teams):
    """Generate SQL for Supabase import"""
    print("\n💾 Generating SQL...")
    
    sql_lines = ["-- Bubble to Supabase sync", f"-- Generated: {datetime.now()}", ""]
    
    # Teams
    if teams:
        sql_lines.append("-- Insert teams")
        for team in teams[:5]:  # First 5 teams
            tid = team.get("_id", "")
            name = team.get("name", "").replace("'", "''")
            desc = team.get("description", "").replace("'", "''")
            
            sql_lines.append(f"""
INSERT INTO public.teams (bubble_id, name, description)
VALUES ('{tid}', '{name}', '{desc}')
ON CONFLICT (bubble_id) DO UPDATE SET name = EXCLUDED.name;""")
    
    # Users
    sql_lines.append("\n-- Insert users")
    for i, user in enumerate(bali_users):
        if i >= 20:  # Limit to 20 for display
            sql_lines.append(f"\n-- Plus {len(bali_users) - 20} more users...")
            break
        
        email = user.get("extracted_email", "").replace("'", "''")
        uid = user.get("_id", "")
        
        # Extract user details
        first_name = user.get("firstName", "")
        last_name = user.get("lastName", "")
        full_name = user.get("fullName", f"{first_name} {last_name}".strip())
        
        # Determine role from type field
        user_type = user.get("type", "").lower()
        role = "member"
        if "admin" in user_type:
            role = "admin"
        elif "manager" in user_type:
            role = "manager"
        
        # Get team (if any)
        team_name = "Bali Love"  # Default
        
        sql_lines.append(f"""
-- User: {full_name} ({email})
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    '{email}', '{uid}', '{team_name}', '{role}', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();""")
    
    # Special case for tom@bali.love
    sql_lines.append("""
-- Ensure tom@bali.love is admin
UPDATE public.user_teams 
SET role = 'admin',
    allowed_agents = '["chat", "search", "analytics"]'::jsonb,
    allowed_data_sources = '["public", "company_wide", "team_specific", "admin_only"]'::jsonb,
    permissions = '{"can_manage_team": true, "can_export_data": true}'::jsonb
WHERE email = 'tom@bali.love';""")
    
    # Save to file
    with open('bubble_bali_users.sql', 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"✅ SQL saved to: bubble_bali_users.sql")
    
    # Show sample users
    if bali_users:
        print("\n👥 Sample @bali.love users:")
        for user in bali_users[:5]:
            email = user.get("extracted_email")
            name = user.get("fullName", "Unknown")
            user_type = user.get("type", "Member")
            print(f"   - {email} | {name} | {user_type}")

# Main execution
def main():
    print("🔍 Bubble Sync - Nested Email Structure")
    print("=" * 50)
    
    # Fetch users
    bali_users = fetch_bali_users_paginated()
    
    # Fetch teams
    teams = fetch_teams()
    
    # Generate SQL
    if bali_users or teams:
        generate_sql(bali_users, teams)
        
        print("\n✅ Success! Next steps:")
        print("   1. Review: bubble_bali_users.sql")
        print("   2. Run the SQL in Supabase SQL Editor")
        print("   3. Check the admin panel at /admin/permissions")
    else:
        print("\n⚠️  No data to sync")

if __name__ == "__main__":
    main()