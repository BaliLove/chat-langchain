#!/usr/bin/env python3
"""
Simple Bubble.io test without database dependencies
This tests just the API connection and data mapping
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bubble_api_direct():
    """Test Bubble.io API directly without sync manager"""
    
    app_url = os.getenv("BUBBLE_APP_URL")
    api_token = os.getenv("BUBBLE_API_TOKEN")
    
    if not app_url or not api_token:
        print("❌ Missing environment variables in .env file")
        return
    
    print("🔍 Testing direct Bubble.io API access...")
    
    headers = {"Authorization": f"Bearer {api_token}"}
    base_url = f"{app_url.rstrip('/')}/api/1.1/obj"
    
    # Test different data types
    data_types = ["event", "product", "venue", "comment", "eventreview"]
    total_records = 0
    
    for data_type in data_types:
        try:
            url = f"{base_url}/{data_type}"
            response = requests.get(f"{url}?limit=5", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("response", {}).get("results", [])
                count = len(results)
                total_records += count
                
                print(f"✅ {data_type}: {count} records")
                
                # Show sample data structure
                if results:
                    sample = results[0]
                    print(f"   Sample fields: {list(sample.keys())[:8]}...")
                    
            elif response.status_code == 404:
                print(f"⚠️  {data_type}: endpoint not found")
            else:
                print(f"❌ {data_type}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {data_type}: Error - {e}")
    
    print(f"\n📊 Total accessible records: {total_records}")
    
    if total_records > 0:
        print("✅ Bubble.io integration is ready!")
        print("💡 The database connection just needs to be configured for sync state management")
        return True
    else:
        print("❌ No data found - check your Bubble.io configuration")
        return False

def test_data_mapping():
    """Test the data mapping without database"""
    
    print("\n🔄 Testing data mapping...")
    
    try:
        # Import the mapper class directly
        from backend.bubble_loader import BubbleDataMapper, BubbleConfig
        
        # Create a test configuration
        config = BubbleConfig(
            app_url=os.getenv("BUBBLE_APP_URL"),
            api_token=os.getenv("BUBBLE_API_TOKEN")
        )
        
        # Create mapper
        mapper = BubbleDataMapper(config)
        
        # Test with sample data
        sample_event = {
            "_id": "test123",
            "name": "Test Bali Event",
            "description": "This is a sample event description for testing the mapping functionality.",
            "Created Date": "2024-01-01T00:00:00Z",
            "location": "Canggu, Bali"
        }
        
        # Test mapping
        doc = mapper.map_record_to_document(sample_event, "event")
        
        if doc:
            print("✅ Data mapping works!")
            print(f"   Mapped content: {doc.page_content[:100]}...")
            print(f"   Metadata keys: {list(doc.metadata.keys())}")
            return True
        else:
            print("❌ Data mapping failed")
            return False
            
    except Exception as e:
        print(f"❌ Mapping test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Simple Bubble.io Test (No Database)")
    print("=" * 45)
    
    # Test API access
    api_works = test_bubble_api_direct()
    
    if api_works:
        # Test data mapping
        test_data_mapping()
    
    print("\n" + "=" * 45)
    print("💡 Next steps:")
    print("   1. Fix RECORD_MANAGER_DB_URL in .env file")
    print("   2. Run full integration test")
    print("   3. Run 'python backend/ingest.py' for complete ingestion") 