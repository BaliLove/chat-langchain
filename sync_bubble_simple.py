#!/usr/bin/env python3
"""
Simplified Bubble sync script using only standard libraries.
Run this if you don't have the required Python packages installed.
"""

import json
import urllib.request
import urllib.parse
import ssl
import os
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

print("🔍 Bubble Sync Script (Simple Version)")
print("=" * 50)

if not all([BUBBLE_API_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    print("❌ Missing required environment variables in .env file:")
    print(f"   BUBBLE_API_TOKEN: {'✅' if BUBBLE_API_TOKEN else '❌'}")
    print(f"   BUBBLE_APP_URL: {'✅' if BUBBLE_APP_URL else '❌'}")
    print(f"   SUPABASE_URL: {'✅' if SUPABASE_URL else '❌'}")
    print(f"   SUPABASE_SERVICE_ROLE_KEY: {'✅' if SUPABASE_SERVICE_KEY else '❌'}")
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

# Test Bubble connection
print("\n📡 Testing Bubble connection...")
bubble_headers = {
    "Authorization": f"Bearer {BUBBLE_API_TOKEN}"
}

# Try to fetch users
users_url = f"{BUBBLE_APP_URL}/api/1.1/obj/user?limit=100"
response = make_request(users_url, headers=bubble_headers)

if response:
    users = response.get("response", {}).get("results", [])
    print(f"✅ Found {len(users)} total users in Bubble")
    
    # Filter for @bali.love emails
    bali_users = [u for u in users if "@bali.love" in u.get("email", "").lower()]
    print(f"✅ Found {len(bali_users)} users with @bali.love emails")
    
    if bali_users:
        print("\n📧 Sample users:")
        for user in bali_users[:5]:  # Show first 5
            email = user.get("email", "Unknown")
            created = user.get("Created Date", "Unknown")
            print(f"   - {email} (created: {created})")
    
    # Try to fetch teams
    print("\n🏢 Checking for teams...")
    for team_endpoint in ["team", "teams", "department", "group"]:
        teams_url = f"{BUBBLE_APP_URL}/api/1.1/obj/{team_endpoint}?limit=10"
        team_response = make_request(teams_url, headers=bubble_headers)
        
        if team_response and team_response.get("response", {}).get("results"):
            teams = team_response.get("response", {}).get("results", [])
            print(f"✅ Found {len(teams)} teams at endpoint: {team_endpoint}")
            break
    else:
        print("⚠️  No team endpoints found")
    
    # Show sync preview
    print("\n📋 Sync Preview:")
    print(f"   Would sync {len(bali_users)} users to Supabase")
    print(f"   Endpoint: {SUPABASE_URL}")
    
    # Create sample SQL for manual import
    print("\n💡 To manually import these users, run this SQL in Supabase:")
    print("```sql")
    print("-- Insert users from Bubble")
    for user in bali_users[:3]:  # Show first 3 as examples
        email = user.get("email", "").lower()
        user_id = user.get("_id", "")
        print(f"""
INSERT INTO public.user_teams (email, bubble_user_id, team_name, role)
VALUES ('{email}', '{user_id}', 'Bali Love', 'member')
ON CONFLICT (email) DO UPDATE
SET bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();""")
    
    if len(bali_users) > 3:
        print(f"\n-- ... and {len(bali_users) - 3} more users")
    print("```")
    
else:
    print("❌ Could not connect to Bubble API")
    print("   Please check your BUBBLE_API_TOKEN and BUBBLE_APP_URL")

print("\n" + "=" * 50)
print("📌 Next steps:")
print("   1. Install required packages: pip3 install supabase httpx python-dotenv")
print("   2. Run full sync: python3 sync_bubble_permissions.py")
print("   3. Or use the SQL above to manually import users")