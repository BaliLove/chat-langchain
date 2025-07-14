"""Simple test to verify Bubble API connection and structure"""

import os
import requests
from dotenv import load_dotenv
import json

# Load environment
load_dotenv()

def simple_bubble_test():
    """Basic test of Bubble API"""
    
    api_token = os.getenv("BUBBLE_API_TOKEN")
    if not api_token:
        print("[ERROR] BUBBLE_API_TOKEN not found")
        return
    
    print(f"[INFO] API Token found: {api_token[:10]}...")
    
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Try different URL patterns
    test_urls = [
        "https://app.bali.love/api/1.1/obj/",
        "https://app.bali.love/api/1.1/obj/User",
        "https://app.bali.love/api/1.1/obj/user",
        "https://app.bali.love/version-test/api/1.1/obj/User",
        "https://app.bali.love/version-live/api/1.1/obj/User",
    ]
    
    print("\n=== Testing Different URL Patterns ===")
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        try:
            response = requests.get(url, headers=headers, params={"limit": 1})
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  [SUCCESS] Found endpoint!")
                data = response.json()
                print(f"  Response keys: {list(data.keys())}")
                
                if "response" in data:
                    resp = data["response"]
                    print(f"  Response has: {list(resp.keys()) if isinstance(resp, dict) else 'not a dict'}")
                    
                    if isinstance(resp, dict) and "results" in resp:
                        results = resp["results"]
                        print(f"  Found {len(results)} results")
                        
                        if results and len(results) > 0:
                            print(f"  First record keys: {list(results[0].keys())[:5]}...")
                            
            elif response.status_code == 401:
                print(f"  [AUTH ERROR] Check your API token")
            elif response.status_code == 404:
                print(f"  [NOT FOUND] Endpoint doesn't exist")
            else:
                print(f"  Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"  [ERROR] {e}")
    
    # Also try to check API documentation endpoint
    print("\n=== Checking API Documentation ===")
    doc_urls = [
        "https://app.bali.love/api/1.1",
        "https://app.bali.love/documentation",
        "https://app.bali.love/api",
    ]
    
    for url in doc_urls:
        try:
            response = requests.get(url, headers=headers)
            print(f"\n{url}: Status {response.status_code}")
            if response.status_code == 200:
                print(f"  Content preview: {response.text[:200]}")
        except Exception as e:
            print(f"{url}: Error - {e}")


if __name__ == "__main__":
    simple_bubble_test()