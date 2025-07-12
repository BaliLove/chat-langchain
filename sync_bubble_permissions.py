#!/usr/bin/env python3
"""
Enhanced script to sync user, team, and permission data from Bubble to Supabase.
This script fetches users and their team associations from Bubble and creates
a proper permission structure in Supabase.
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Configuration
BUBBLE_API_TOKEN = os.getenv("BUBBLE_API_TOKEN")
BUBBLE_APP_URL = os.getenv("BUBBLE_APP_URL", "https://app.bali.love")
BUBBLE_BATCH_SIZE = int(os.getenv("BUBBLE_BATCH_SIZE", "100"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


class BubblePermissionSync:
    def __init__(self):
        self.bubble_headers = {
            "Authorization": f"Bearer {BUBBLE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        self.teams_cache = {}
        self.stats = {
            "users_found": 0,
            "users_synced": 0,
            "teams_found": 0,
            "teams_synced": 0,
            "errors": []
        }

    async def fetch_bubble_data(self, endpoint: str, constraints: Optional[List[Dict]] = None) -> List[Dict]:
        """Generic method to fetch data from Bubble API with pagination"""
        url = f"{BUBBLE_APP_URL}/api/1.1/obj/{endpoint}"
        all_results = []
        cursor = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {
                    "cursor": cursor,
                    "limit": BUBBLE_BATCH_SIZE
                }
                
                if constraints:
                    params["constraints"] = json.dumps(constraints)
                
                try:
                    response = await client.get(url, headers=self.bubble_headers, params=params)
                    
                    if response.status_code != 200:
                        print(f"❌ Error fetching {endpoint}: {response.status_code}")
                        self.stats["errors"].append(f"Failed to fetch {endpoint}: {response.status_code}")
                        break
                    
                    data = response.json()
                    results = data.get("response", {}).get("results", [])
                    
                    if not results:
                        break
                    
                    all_results.extend(results)
                    cursor += len(results)
                    
                    # Check if we've fetched all records
                    if len(results) < BUBBLE_BATCH_SIZE:
                        break
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ Exception fetching {endpoint}: {e}")
                    self.stats["errors"].append(f"Exception fetching {endpoint}: {str(e)}")
                    break
        
        return all_results

    async def fetch_teams(self) -> Dict[str, Dict]:
        """Fetch all teams from Bubble"""
        print("📋 Fetching teams from Bubble...")
        
        teams = await self.fetch_bubble_data("team")
        
        # Also try common variations
        if not teams:
            for alt_endpoint in ["teams", "department", "group"]:
                teams = await self.fetch_bubble_data(alt_endpoint)
                if teams:
                    break
        
        self.stats["teams_found"] = len(teams)
        print(f"   Found {len(teams)} teams")
        
        # Cache teams by ID and name for quick lookup
        teams_dict = {}
        for team in teams:
            team_id = team.get("_id")
            if team_id:
                teams_dict[team_id] = team
                # Also cache by name for flexible matching
                team_name = team.get("name", "").lower()
                if team_name:
                    teams_dict[team_name] = team
        
        return teams_dict

    async def fetch_users(self) -> List[Dict]:
        """Fetch users from Bubble with bali.love email domain"""
        print("👥 Fetching users from Bubble...")
        
        # Try to fetch with email constraint
        constraints = [{
            "key": "email",
            "constraint_type": "text contains",
            "value": "@bali.love"
        }]
        
        users = await self.fetch_bubble_data("user", constraints)
        
        # If no users found with constraints, try without
        if not users:
            print("   Trying without email filter...")
            all_users = await self.fetch_bubble_data("user")
            # Filter in Python
            users = [u for u in all_users if "@bali.love" in u.get("email", "").lower()]
        
        self.stats["users_found"] = len(users)
        print(f"   Found {len(users)} users with @bali.love emails")
        
        return users

    def extract_user_permissions(self, user: Dict, teams_cache: Dict) -> Dict:
        """Extract permission data from Bubble user object"""
        email = user.get("email", "").lower()
        
        # Extract team information
        team_id = user.get("team_id") or user.get("team") or user.get("department")
        team_name = "Bali Love"  # Default
        team_uuid = None
        
        if team_id and team_id in teams_cache:
            team_data = teams_cache[team_id]
            team_name = team_data.get("name", team_name)
            # We'll create/get the team UUID when syncing to Supabase
        
        # Determine role based on various fields
        role = "member"  # Default
        
        # Check for role indicators
        if any(field in user for field in ["is_admin", "isAdmin", "admin"]):
            if user.get("is_admin") or user.get("isAdmin") or user.get("admin"):
                role = "admin"
        elif any(field in user for field in ["is_manager", "isManager", "manager"]):
            if user.get("is_manager") or user.get("isManager") or user.get("manager"):
                role = "manager"
        elif user.get("role"):
            role_value = user.get("role", "").lower()
            if "admin" in role_value:
                role = "admin"
            elif "manager" in role_value:
                role = "manager"
        
        # Extract allowed agents (if specified in Bubble)
        allowed_agents = user.get("allowed_agents", ["chat", "search"])
        if isinstance(allowed_agents, str):
            # Handle comma-separated string
            allowed_agents = [a.strip() for a in allowed_agents.split(",")]
        
        # Extract allowed data sources
        allowed_data_sources = ["public", "company_wide"]  # Default
        
        # Enhance based on role
        if role == "admin":
            allowed_data_sources.extend(["team_specific", "department_specific", "admin_only"])
        elif role == "manager":
            allowed_data_sources.extend(["team_specific", "department_specific"])
        
        # Check for specific data source permissions in Bubble
        if user.get("allowed_data_sources"):
            custom_sources = user.get("allowed_data_sources")
            if isinstance(custom_sources, list):
                allowed_data_sources.extend(custom_sources)
            elif isinstance(custom_sources, str):
                allowed_data_sources.extend([s.strip() for s in custom_sources.split(",")])
        
        # Remove duplicates
        allowed_data_sources = list(set(allowed_data_sources))
        
        # Build flexible permissions object
        permissions = {
            "can_create_threads": True,
            "can_delete_own_threads": True,
            "can_view_team_threads": role in ["admin", "manager"],
            "can_export_data": role == "admin",
            "can_manage_team": role == "admin",
            "max_threads_per_day": 100 if role == "admin" else 50,
            "custom_permissions": user.get("custom_permissions", {})
        }
        
        return {
            "email": email,
            "bubble_user_id": user.get("_id"),
            "team_name": team_name,
            "role": role,
            "allowed_agents": allowed_agents,
            "allowed_data_sources": allowed_data_sources,
            "permissions": permissions,
            "bubble_team_id": team_id
        }

    async def sync_teams_to_supabase(self, teams_cache: Dict):
        """Sync teams to Supabase"""
        print("\n🔄 Syncing teams to Supabase...")
        
        unique_teams = {}
        for key, team in teams_cache.items():
            if not key.startswith("_"):  # Skip IDs, process actual team objects
                team_id = team.get("_id")
                if team_id and team_id not in unique_teams:
                    unique_teams[team_id] = team
        
        for bubble_id, team in unique_teams.items():
            try:
                team_data = {
                    "bubble_id": bubble_id,
                    "name": team.get("name", "Unknown Team"),
                    "description": team.get("description", "")
                }
                
                # Upsert team
                result = supabase.table("teams").upsert(
                    team_data,
                    on_conflict="bubble_id"
                ).execute()
                
                if result.data:
                    self.stats["teams_synced"] += 1
                    # Cache the Supabase team ID
                    team["supabase_id"] = result.data[0]["id"]
                    print(f"   ✅ Synced team: {team_data['name']}")
                
            except Exception as e:
                print(f"   ❌ Failed to sync team {bubble_id}: {e}")
                self.stats["errors"].append(f"Team sync failed: {str(e)}")

    async def sync_users_to_supabase(self, users: List[Dict], teams_cache: Dict):
        """Sync users to Supabase with proper permissions"""
        print("\n🔄 Syncing users to Supabase...")
        
        for user in users:
            try:
                # Extract permission data
                user_data = self.extract_user_permissions(user, teams_cache)
                
                # Look up team UUID if we have a team
                if user_data.get("bubble_team_id") and user_data["bubble_team_id"] in teams_cache:
                    team = teams_cache[user_data["bubble_team_id"]]
                    if "supabase_id" in team:
                        user_data["team_id"] = team["supabase_id"]
                
                # Remove bubble_team_id as it's not in our schema
                user_data.pop("bubble_team_id", None)
                
                # Add sync timestamp
                user_data["synced_from_bubble_at"] = datetime.utcnow().isoformat()
                
                # Check if user exists in auth.users
                try:
                    auth_response = supabase.auth.admin.list_users()
                    auth_users = [u for u in auth_response if u.email == user_data["email"]]
                    
                    if auth_users:
                        user_data["user_id"] = auth_users[0].id
                except:
                    # If we can't check auth.users, that's okay
                    pass
                
                # Upsert to user_teams
                result = supabase.table("user_teams").upsert(
                    user_data,
                    on_conflict="email"
                ).execute()
                
                if result.data:
                    self.stats["users_synced"] += 1
                    print(f"   ✅ Synced user: {user_data['email']} ({user_data['role']})")
                
            except Exception as e:
                print(f"   ❌ Failed to sync user {user.get('email', 'unknown')}: {e}")
                self.stats["errors"].append(f"User sync failed: {str(e)}")

    async def run_sync(self):
        """Main sync process"""
        print("🚀 Starting Bubble → Supabase permission sync...")
        
        # Validate environment
        if not all([BUBBLE_API_TOKEN, BUBBLE_APP_URL, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
            print("❌ Missing required environment variables")
            print("Required: BUBBLE_API_TOKEN, BUBBLE_APP_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
            sys.exit(1)
        
        # Fetch teams first
        teams_cache = await self.fetch_teams()
        
        # Sync teams to Supabase
        if teams_cache:
            await self.sync_teams_to_supabase(teams_cache)
        
        # Fetch users
        users = await self.fetch_users()
        
        # Sync users with permissions
        if users:
            await self.sync_users_to_supabase(users, teams_cache)
        
        # Print summary
        print("\n📊 Sync Summary:")
        print(f"   Teams found: {self.stats['teams_found']}")
        print(f"   Teams synced: {self.stats['teams_synced']}")
        print(f"   Users found: {self.stats['users_found']}")
        print(f"   Users synced: {self.stats['users_synced']}")
        
        if self.stats["errors"]:
            print(f"\n⚠️  Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats["errors"][:5]:  # Show first 5 errors
                print(f"   - {error}")
        
        print("\n✅ Sync complete!")


async def main():
    """Entry point"""
    syncer = BubblePermissionSync()
    await syncer.run_sync()


if __name__ == "__main__":
    asyncio.run(main())