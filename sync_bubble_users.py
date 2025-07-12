"""
Simple script to sync user and team data from Bubble to Supabase.
Run this periodically (e.g., via cron or GitHub Actions) to keep data in sync.
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configuration - using existing Bubble env vars
BUBBLE_API_TOKEN = os.getenv("BUBBLE_API_TOKEN")
BUBBLE_APP_URL = os.getenv("BUBBLE_APP_URL", "https://app.bali.love")
BUBBLE_BATCH_SIZE = int(os.getenv("BUBBLE_BATCH_SIZE", "100"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Need service key for RLS bypass

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def fetch_bubble_users() -> List[Dict[str, Any]]:
    """Fetch users from Bubble where email domain is bali.love"""
    
    # Bubble API endpoint for searching users
    url = f"{BUBBLE_APP_URL}/api/1.1/obj/user"
    
    headers = {
        "Authorization": f"Bearer {BUBBLE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Search for users with bali.love email domain
    params = {
        "constraints": [
            {
                "key": "email",
                "constraint_type": "text contains",
                "value": "@bali.love"
            }
        ]
    }
    
    users = []
    cursor = 0
    limit = BUBBLE_BATCH_SIZE
    
    with httpx.Client() as client:
        while True:
            response = client.get(
                url,
                headers=headers,
                params={
                    "cursor": cursor,
                    "limit": limit,
                    "constraints": params["constraints"]
                }
            )
            
            if response.status_code != 200:
                print(f"Error fetching from Bubble: {response.status_code}")
                print(response.text)
                break
                
            data = response.json()
            results = data.get("response", {}).get("results", [])
            
            if not results:
                break
                
            users.extend(results)
            cursor += limit
            
            # Check if we've fetched all records
            if len(results) < limit:
                break
    
    return users


def sync_to_supabase(bubble_users: List[Dict[str, Any]]):
    """Sync user data to Supabase user_teams table"""
    
    for user in bubble_users:
        email = user.get("email", "").lower()
        
        if not email or "@bali.love" not in email:
            continue
            
        # Prepare user data for Supabase
        user_data = {
            "email": email,
            "team_id": user.get("team_id", user.get("_id", "")),  # Use Bubble ID as team_id if no specific team
            "team_name": user.get("team_name", "Bali Love"),
            "role": user.get("role", "member"),
            "allowed_agents": user.get("allowed_agents", []),
            "allowed_data_sources": user.get("allowed_data_sources", []),
            "synced_from_bubble_at": datetime.utcnow().isoformat()
        }
        
        # Check if user exists in auth.users
        auth_user = supabase.auth.admin.list_users(
            page=1,
            per_page=1,
            filters={"email": email}
        )
        
        if auth_user and auth_user.users:
            user_data["user_id"] = auth_user.users[0].id
        
        # Upsert to Supabase (insert or update based on email)
        result = supabase.table("user_teams").upsert(
            user_data,
            on_conflict="email"
        ).execute()
        
        if result.data:
            print(f"✓ Synced user: {email}")
        else:
            print(f"✗ Failed to sync user: {email}")


def main():
    """Main sync process"""
    print("Starting Bubble → Supabase user sync...")
    
    # Validate environment variables
    if not all([BUBBLE_API_TOKEN, BUBBLE_APP_URL, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
        print("Error: Missing required environment variables")
        print("Required: BUBBLE_API_TOKEN, BUBBLE_APP_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    
    # Fetch users from Bubble
    print("Fetching users from Bubble...")
    bubble_users = fetch_bubble_users()
    print(f"Found {len(bubble_users)} users with @bali.love emails")
    
    if bubble_users:
        # Sync to Supabase
        print("Syncing to Supabase...")
        sync_to_supabase(bubble_users)
    
    print("Sync complete!")


if __name__ == "__main__":
    main()