"""Verify actual Bubble API structure and available data types"""

import os
import requests
from dotenv import load_dotenv
import json

# Load environment
load_dotenv()

def test_bubble_api():
    """Test Bubble API and discover available data types"""
    
    api_token = os.getenv("BUBBLE_API_TOKEN")
    if not api_token:
        print("[ERROR] BUBBLE_API_TOKEN not found in environment")
        return
    
    headers = {"Authorization": f"Bearer {api_token}"}
    base_url = "https://app.bali.love/api/1.1"
    
    print("=== Testing Bubble API Connection ===\n")
    
    # Test basic connection
    print("1. Testing API connection...")
    try:
        response = requests.get(f"{base_url}/obj/", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   [ERROR] Connection failed: {e}")
        return
    
    # Test various potential data types
    print("\n2. Testing common data type patterns...")
    
    # Common patterns based on the schema analysis
    test_endpoints = [
        # Training-related (from our previous attempt)
        "training_module",
        "training_session",
        "employee_training_plan",
        "training_attendance",
        "training_assessment",
        "training_feedback",
        
        # Event/Venue related (from schema)
        "Event",
        "event",
        "Venue", 
        "venue",
        "Product",
        "product",
        "Booking",
        "booking",
        "Guest",
        "guest",
        
        # Try with different naming conventions
        "events",
        "venues",
        "products",
        "bookings",
        
        # From the bubble schema analysis
        "EventReview",
        "EventRSVP",
        "ProductLinks",
        "VenueImage",
        "Comment",
        "Payment"
    ]
    
    working_endpoints = []
    
    for endpoint in test_endpoints:
        try:
            url = f"{base_url}/obj/{endpoint}"
            response = requests.get(url, headers=headers, params={"limit": 1})
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("response", {}).get("results", [])
                if results or "response" in data:
                    print(f"   [OK] {endpoint}: SUCCESS - Found {len(results)} record(s)")
                    working_endpoints.append(endpoint)
                    
                    # Show first record structure
                    if results:
                        print(f"     Sample fields: {list(results[0].keys())[:5]}...")
                else:
                    print(f"   ? {endpoint}: Empty response")
            elif response.status_code == 404:
                # Skip 404s to reduce noise
                pass
            else:
                print(f"   [FAIL] {endpoint}: Status {response.status_code}")
                
        except Exception as e:
            print(f"   [ERROR] {endpoint}: Error - {e}")
    
    print(f"\n3. Working endpoints found: {len(working_endpoints)}")
    
    # Detailed analysis of working endpoints
    if working_endpoints:
        print("\n4. Detailed analysis of working endpoints...")
        
        for endpoint in working_endpoints[:5]:  # Analyze first 5
            print(f"\n   === {endpoint} ===")
            try:
                url = f"{base_url}/obj/{endpoint}"
                response = requests.get(url, headers=headers, params={"limit": 3})
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("response", {}).get("results", [])
                    
                    if results:
                        # Show structure of first record
                        first_record = results[0]
                        print(f"   Total records available: {data.get('response', {}).get('count', 'unknown')}")
                        print(f"   Sample record structure:")
                        
                        for key, value in list(first_record.items())[:10]:
                            value_type = type(value).__name__
                            value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                            print(f"     - {key}: {value_type} = {value_preview}")
                            
            except Exception as e:
                print(f"   Error analyzing {endpoint}: {e}")
    
    # Save working endpoints for future use
    if working_endpoints:
        with open("bubble_working_endpoints.json", "w") as f:
            json.dump({
                "base_url": base_url,
                "working_endpoints": working_endpoints,
                "tested_at": str(os.popen('date').read().strip())
            }, f, indent=2)
        print(f"\n5. Saved {len(working_endpoints)} working endpoints to bubble_working_endpoints.json")
    
    return working_endpoints


def test_specific_endpoint(endpoint_name):
    """Test a specific endpoint in detail"""
    
    api_token = os.getenv("BUBBLE_API_TOKEN")
    headers = {"Authorization": f"Bearer {api_token}"}
    base_url = "https://app.bali.love/api/1.1"
    
    print(f"\n=== Detailed Test: {endpoint_name} ===")
    
    try:
        # Get multiple records
        url = f"{base_url}/obj/{endpoint_name}"
        response = requests.get(url, headers=headers, params={"limit": 5})
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("response", {}).get("results", [])
            
            print(f"Found {len(results)} records")
            print(f"Total count: {data.get('response', {}).get('count', 'unknown')}")
            
            # Analyze field patterns
            if results:
                all_fields = set()
                for record in results:
                    all_fields.update(record.keys())
                
                print(f"\nAll fields found ({len(all_fields)}):")
                for field in sorted(all_fields):
                    # Check field consistency
                    field_types = set()
                    has_data = False
                    
                    for record in results:
                        if field in record and record[field] is not None:
                            field_types.add(type(record[field]).__name__)
                            has_data = True
                    
                    if has_data:
                        print(f"  - {field}: {', '.join(field_types)}")
                
                # Show full first record
                print(f"\nFirst complete record:")
                print(json.dumps(results[0], indent=2, default=str))
                
        else:
            print(f"Error: Status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error testing {endpoint_name}: {e}")


if __name__ == "__main__":
    # First, discover working endpoints
    working = test_bubble_api()
    
    # Then test the first few in detail
    if working:
        print("\n" + "="*60 + "\n")
        for endpoint in working[:3]:
            test_specific_endpoint(endpoint)
            print("\n" + "-"*60)