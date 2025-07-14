"""Test Bubble API connection and discover data types"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Get API credentials
api_token = os.getenv("BUBBLE_API_TOKEN")
base_url = "https://app.bali.love/api/1.1/obj/"

if not api_token:
    print("BUBBLE_API_TOKEN not found")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_token}"
}

# Test different possible data type names
test_types = [
    "training_module",
    "Training_Module", 
    "TrainingModule",
    "training-module",
    "module",
    "Training module",
    "training",
    "Training",
]

print("Testing Bubble API endpoints...")
print("=" * 60)

for data_type in test_types:
    url = f"{base_url}{data_type}"
    
    try:
        response = requests.get(url, headers=headers, params={"limit": 1})
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("response", {}).get("results", [])
            print(f"[OK] {data_type}: SUCCESS - Found {len(results)} records")
            if results:
                print(f"  Sample keys: {list(results[0].keys())[:5]}")
        else:
            print(f"[FAIL] {data_type}: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] {data_type}: Error - {e}")

# Also try to get metadata
print("\nTrying to get API metadata...")
metadata_url = "https://app.bali.love/api/1.1/meta"
try:
    response = requests.get(metadata_url, headers=headers)
    if response.status_code == 200:
        print("Metadata available:")
        print(response.json())
except Exception as e:
    print(f"Metadata not available: {e}")