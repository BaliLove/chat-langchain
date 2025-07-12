#!/usr/bin/env python3
"""
Test script to verify the permission system is working correctly.
This script tests the complete flow from Bubble sync to permission checks.
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    print("❌ Missing required environment variables")
    print("Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

# Initialize clients
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
supabase_anon = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_ANON_KEY else None


class PermissionTester:
    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }

    def test(self, name: str, condition: bool, details: str = ""):
        """Record a test result"""
        result = {
            "name": name,
            "passed": condition,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results["tests"].append(result)
        
        if condition:
            self.test_results["passed"] += 1
            print(f"✅ {name}")
        else:
            self.test_results["failed"] += 1
            print(f"❌ {name}")
            if details:
                print(f"   Details: {details}")

    async def test_database_setup(self):
        """Test that all required tables and views exist"""
        print("\n🔍 Testing Database Setup...")
        
        # Check teams table
        try:
            result = supabase_admin.table("teams").select("*").limit(1).execute()
            self.test("Teams table exists", True)
        except Exception as e:
            self.test("Teams table exists", False, str(e))
        
        # Check user_teams table
        try:
            result = supabase_admin.table("user_teams").select("*").limit(1).execute()
            self.test("User teams table exists", True)
        except Exception as e:
            self.test("User teams table exists", False, str(e))
        
        # Check user_permissions view
        try:
            result = supabase_admin.table("user_permissions").select("*").limit(1).execute()
            self.test("User permissions view exists", True)
        except Exception as e:
            self.test("User permissions view exists", False, str(e))

    async def test_sample_data(self):
        """Test creating sample permission data"""
        print("\n🔍 Testing Sample Data Creation...")
        
        # Create a test team
        test_team = {
            "bubble_id": "test_team_001",
            "name": "Test Team",
            "description": "Team created for permission testing"
        }
        
        try:
            result = supabase_admin.table("teams").upsert(
                test_team,
                on_conflict="bubble_id"
            ).execute()
            team_id = result.data[0]["id"] if result.data else None
            self.test("Create test team", bool(team_id))
        except Exception as e:
            self.test("Create test team", False, str(e))
            team_id = None
        
        # Create test users with different roles
        test_users = [
            {
                "email": "admin@bali.love",
                "bubble_user_id": "test_admin_001",
                "team_id": team_id,
                "team_name": "Test Team",
                "role": "admin",
                "allowed_agents": ["chat", "search", "analytics"],
                "allowed_data_sources": ["public", "company_wide", "team_specific", "admin_only"],
                "permissions": {
                    "can_create_threads": True,
                    "can_delete_own_threads": True,
                    "can_view_team_threads": True,
                    "can_export_data": True,
                    "can_manage_team": True,
                    "max_threads_per_day": 100
                }
            },
            {
                "email": "manager@bali.love",
                "bubble_user_id": "test_manager_001",
                "team_id": team_id,
                "team_name": "Test Team",
                "role": "manager",
                "allowed_agents": ["chat", "search"],
                "allowed_data_sources": ["public", "company_wide", "team_specific"],
                "permissions": {
                    "can_create_threads": True,
                    "can_delete_own_threads": True,
                    "can_view_team_threads": True,
                    "can_export_data": False,
                    "can_manage_team": False,
                    "max_threads_per_day": 50
                }
            },
            {
                "email": "member@bali.love",
                "bubble_user_id": "test_member_001",
                "team_id": team_id,
                "team_name": "Test Team",
                "role": "member",
                "allowed_agents": ["chat"],
                "allowed_data_sources": ["public", "company_wide"],
                "permissions": {
                    "can_create_threads": True,
                    "can_delete_own_threads": True,
                    "can_view_team_threads": False,
                    "can_export_data": False,
                    "can_manage_team": False,
                    "max_threads_per_day": 25
                }
            }
        ]
        
        for user in test_users:
            try:
                result = supabase_admin.table("user_teams").upsert(
                    user,
                    on_conflict="email"
                ).execute()
                self.test(f"Create {user['role']} user", bool(result.data))
            except Exception as e:
                self.test(f"Create {user['role']} user", False, str(e))

    async def test_permission_queries(self):
        """Test various permission queries"""
        print("\n🔍 Testing Permission Queries...")
        
        # Test fetching user permissions
        test_email = "admin@bali.love"
        try:
            result = supabase_admin.from_("user_permissions").select("*").eq("email", test_email).single().execute()
            user_data = result.data
            
            self.test(
                "Fetch admin permissions",
                user_data and user_data.get("role") == "admin",
                f"Role: {user_data.get('role') if user_data else 'None'}"
            )
            
            # Test permission details
            if user_data:
                self.test(
                    "Admin has analytics agent",
                    "analytics" in (user_data.get("allowed_agents") or [])
                )
                self.test(
                    "Admin has admin_only data source",
                    "admin_only" in (user_data.get("allowed_data_sources") or [])
                )
                self.test(
                    "Admin can manage team",
                    user_data.get("permissions", {}).get("can_manage_team") == True
                )
        except Exception as e:
            self.test("Fetch admin permissions", False, str(e))
        
        # Test team member count
        try:
            result = supabase_admin.table("user_teams").select("*", count="exact").execute()
            self.test(
                "Count team members",
                result.count >= 3,
                f"Found {result.count} members"
            )
        except Exception as e:
            self.test("Count team members", False, str(e))

    async def test_rls_policies(self):
        """Test Row Level Security policies"""
        print("\n🔍 Testing RLS Policies...")
        
        if not supabase_anon:
            print("⚠️  Skipping RLS tests - SUPABASE_ANON_KEY not set")
            return
        
        # Test that anonymous users can't access user_teams
        try:
            result = supabase_anon.table("user_teams").select("*").execute()
            self.test(
                "Anonymous can't access user_teams",
                len(result.data) == 0,
                f"Returned {len(result.data)} records"
            )
        except Exception as e:
            # Exception is expected for proper RLS
            self.test("Anonymous can't access user_teams", True, "RLS properly blocked access")

    async def test_permission_edge_cases(self):
        """Test edge cases and validation"""
        print("\n🔍 Testing Edge Cases...")
        
        # Test invalid email domain
        invalid_user = {
            "email": "user@invalid.com",
            "role": "member",
            "team_name": "Test Team"
        }
        
        # This should succeed at database level but be filtered by app logic
        try:
            result = supabase_admin.table("user_teams").upsert(
                invalid_user,
                on_conflict="email"
            ).execute()
            self.test(
                "Can insert non-bali.love email (for testing)",
                bool(result.data),
                "App layer should filter this"
            )
        except Exception as e:
            self.test("Can insert non-bali.love email", False, str(e))
        
        # Test permission inheritance
        try:
            # Fetch a manager's permissions
            result = supabase_admin.from_("user_permissions").select("*").eq("email", "manager@bali.love").single().execute()
            manager_data = result.data
            
            if manager_data:
                self.test(
                    "Manager inherits team_specific data source",
                    "team_specific" in (manager_data.get("allowed_data_sources") or [])
                )
                self.test(
                    "Manager can't access admin_only data",
                    "admin_only" not in (manager_data.get("allowed_data_sources") or [])
                )
        except Exception as e:
            self.test("Test permission inheritance", False, str(e))

    async def generate_report(self):
        """Generate a test report"""
        print("\n" + "="*50)
        print("📊 Permission System Test Report")
        print("="*50)
        print(f"Total Tests: {self.test_results['passed'] + self.test_results['failed']}")
        print(f"Passed: {self.test_results['passed']} ✅")
        print(f"Failed: {self.test_results['failed']} ❌")
        print(f"Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['failed'] > 0:
            print("\n❌ Failed Tests:")
            for test in self.test_results['tests']:
                if not test['passed']:
                    print(f"  - {test['name']}")
                    if test['details']:
                        print(f"    {test['details']}")
        
        # Save detailed report
        report_file = f"permission_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n💾 Detailed report saved to: {report_file}")

    async def cleanup_test_data(self):
        """Clean up test data (optional)"""
        print("\n🧹 Cleaning up test data...")
        
        # Remove test users
        test_emails = ["admin@bali.love", "manager@bali.love", "member@bali.love", "user@invalid.com"]
        for email in test_emails:
            try:
                supabase_admin.table("user_teams").delete().eq("email", email).execute()
            except:
                pass
        
        # Remove test team
        try:
            supabase_admin.table("teams").delete().eq("bubble_id", "test_team_001").execute()
        except:
            pass
        
        print("✅ Test data cleaned up")

    async def run_all_tests(self, cleanup=False):
        """Run all permission tests"""
        print("🚀 Starting Permission System Tests...")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        await self.test_database_setup()
        await self.test_sample_data()
        await self.test_permission_queries()
        await self.test_rls_policies()
        await self.test_permission_edge_cases()
        
        await self.generate_report()
        
        if cleanup:
            await self.cleanup_test_data()


async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the permission system")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test data after running")
    args = parser.parse_args()
    
    tester = PermissionTester()
    await tester.run_all_tests(cleanup=args.cleanup)


if __name__ == "__main__":
    asyncio.run(main())