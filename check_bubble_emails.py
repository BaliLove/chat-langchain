#!/usr/bin/env python3
"""
Check email patterns in Bubble to understand the data structure.
"""

import json
import urllib.request
import ssl
import os

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

ssl_context = ssl.create_default_context()

def make_request(url, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, context=ssl_context) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

print("🔍 Checking Bubble Email Structure")
print("=" * 50)

bubble_headers = {"Authorization": f"Bearer {BUBBLE_API_TOKEN}"}

# Fetch a small batch to examine structure
users_url = f"{BUBBLE_APP_URL}/api/1.1/obj/user?limit=10"
response = make_request(users_url, headers=bubble_headers)

if response:
    users = response.get("response", {}).get("results", [])
    
    if users:
        print(f"\n📋 Sample user structure (first user):")
        first_user = users[0]
        
        # Show all fields
        for key, value in sorted(first_user.items()):
            value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            print(f"   {key}: {value_str}")
        
        print(f"\n🔍 Checking email-related fields in {len(users)} sample users:")
        
        # Look for any field that might contain email
        email_fields = {}
        email_domains = {}
        
        for user in users:
            for key, value in user.items():
                if value and isinstance(value, str):
                    # Check if value looks like an email
                    if "@" in value and "." in value.split("@")[-1]:
                        if key not in email_fields:
                            email_fields[key] = []
                        email_fields[key].append(value)
                        
                        # Track domains
                        domain = value.split("@")[-1].lower()
                        email_domains[domain] = email_domains.get(domain, 0) + 1
        
        if email_fields:
            print("\n📧 Found email addresses in these fields:")
            for field, emails in email_fields.items():
                print(f"   {field}: {len(emails)} emails")
                for email in emails[:3]:  # Show first 3
                    print(f"      - {email}")
        else:
            print("\n⚠️  No email addresses found in sample data")
        
        if email_domains:
            print("\n🌐 Email domains found:")
            for domain, count in sorted(email_domains.items(), key=lambda x: x[1], reverse=True):
                print(f"   {domain}: {count} users")
                
        # Check specific for bali.love pattern
        print("\n🔍 Searching for 'bali' in all text fields:")
        bali_found = False
        for user in users:
            for key, value in user.items():
                if value and isinstance(value, str) and "bali" in value.lower():
                    print(f"   Found 'bali' in {key}: {value}")
                    bali_found = True
        
        if not bali_found:
            print("   No 'bali' references found in sample data")
                
    else:
        print("❌ No users found")
else:
    print("❌ Could not connect to Bubble API")

print("\n" + "=" * 50)
print("💡 Next: Update sync script with correct email field name")