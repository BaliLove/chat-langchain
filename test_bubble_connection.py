#!/usr/bin/env python3
"""
Quick test script to verify Bubble.io API connection
Run this after setting up your .env file with BUBBLE_APP_URL and BUBBLE_API_TOKEN
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_bubble_connection():
    """Test basic API connection"""
    import requests
    
    app_url = os.getenv("BUBBLE_APP_URL")
    api_token = os.getenv("BUBBLE_API_TOKEN")
    
    if not app_url or not api_token:
        print("❌ Missing environment variables:")
        print(f"   BUBBLE_APP_URL: {'✅ Set' if app_url else '❌ Missing'}")
        print(f"   BUBBLE_API_TOKEN: {'✅ Set' if api_token else '❌ Missing'}")
        print("\n💡 Make sure to add these to your .env file")
        return False
    
    print(f"🔍 Testing connection to: {app_url}")
    
    # Test API connection with a simple request
    headers = {"Authorization": f"Bearer {api_token}"}
    test_url = f"{app_url.rstrip('/')}/api/1.1/obj/event"
    
    try:
        response = requests.get(f"{test_url}?limit=1", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get("response", {}).get("count", 0)
            print(f"✅ Connection successful!")
            print(f"📊 Found {count} events in your database")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed - check your API token")
            return False
        elif response.status_code == 404:
            print("⚠️  Event endpoint not found - trying other data types...")
            # Try other common endpoints
            for data_type in ["product", "venue", "comment"]:
                test_url = f"{app_url.rstrip('/')}/api/1.1/obj/{data_type}"
                try:
                    resp = requests.get(f"{test_url}?limit=1", headers=headers, timeout=5)
                    if resp.status_code == 200:
                        print(f"✅ Found {data_type} endpoint working!")
                        return True
                except:
                    continue
            print("❌ No working endpoints found")
            return False
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_full_integration():
    """Test the full integration"""
    print("\n🚀 Testing full Bubble.io integration...")
    
    try:
        from backend.bubble_loader import load_bubble_data
        
        # Test data loading
        docs = load_bubble_data()
        
        if docs:
            print(f"✅ Success! Loaded {len(docs)} documents")
            
            # Show sample data
            print(f"\n📄 Sample document:")
            sample_doc = docs[0]
            print(f"   Type: {sample_doc.metadata.get('source_type')}")
            print(f"   Title: {sample_doc.metadata.get('title')}")
            print(f"   Content: {sample_doc.page_content[:100]}...")
            print(f"   Source: {sample_doc.metadata.get('source')}")
            
            # Show statistics
            type_counts = {}
            for doc in docs:
                doc_type = doc.metadata.get('source_type', 'unknown')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            print(f"\n📊 Documents by type:")
            for doc_type, count in sorted(type_counts.items()):
                print(f"   {doc_type}: {count}")
                
            return True
        else:
            print("❌ No documents loaded - check your configuration")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Bubble.io Integration Test")
    print("=" * 40)
    
    # Test 1: Basic API connection
    if test_bubble_connection():
        # Test 2: Full integration (only if basic connection works)
        test_full_integration()
    
    print("\n" + "=" * 40)
    print("💡 Next steps:")
    print("   1. If tests pass: Run 'python backend/ingest.py' for full ingestion")
    print("   2. If tests fail: Check your .env file and API settings")
    print("   3. See BUBBLE_INTEGRATION_SETUP.md for detailed troubleshooting") 