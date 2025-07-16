"""Check all fields in issue records to find the private checkbox"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def check_issue_fields():
    """Fetch issue records and examine all fields"""
    
    app_url = os.environ.get("BUBBLE_APP_URL", "")
    api_token = os.environ.get("BUBBLE_API_TOKEN", "")
    
    if not app_url or not api_token:
        print("Missing Bubble.io configuration!")
        return
    
    base_url = f"{app_url.rstrip('/')}/api/1.1/obj"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Check both issue types
    for data_type in ["issue", "Issue"]:
        print(f"\nChecking {data_type} records...")
        print("-" * 60)
        
        try:
            response = requests.get(
                f"{base_url}/{data_type}",
                headers=headers,
                params={"limit": 10},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("response", {}).get("results", [])
                
                if results:
                    # Analyze first record in detail
                    first = results[0]
                    print(f"Fields in {data_type}:")
                    for field, value in sorted(first.items()):
                        value_type = type(value).__name__
                        if isinstance(value, bool):
                            print(f"  {field}: {value} (BOOLEAN)")
                        elif "private" in field.lower() or "public" in field.lower():
                            print(f"  {field}: {value} (PRIVACY FIELD?)")
                        else:
                            print(f"  {field}: {value_type}")
                    
                    # Check for privacy indicators across all records
                    print(f"\nChecking for privacy patterns across {len(results)} records:")
                    privacy_fields = {}
                    for record in results:
                        for field, value in record.items():
                            if isinstance(value, bool) or "private" in str(field).lower():
                                if field not in privacy_fields:
                                    privacy_fields[field] = []
                                privacy_fields[field].append(value)
                    
                    for field, values in privacy_fields.items():
                        unique_values = list(set(str(v) for v in values))
                        print(f"  {field}: {unique_values}")
                        
        except Exception as e:
            print(f"Error checking {data_type}: {e}")


if __name__ == "__main__":
    check_issue_fields()