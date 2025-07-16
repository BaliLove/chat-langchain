"""Find the private checkbox field by checking more records and field variations"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def find_private_field():
    """Check various issue records to find privacy field"""
    
    app_url = os.environ.get("BUBBLE_APP_URL", "")
    api_token = os.environ.get("BUBBLE_API_TOKEN", "")
    
    base_url = f"{app_url.rstrip('/')}/api/1.1/obj"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Check different cursors to get different records
    all_fields = set()
    boolean_fields = {}
    privacy_candidates = []
    
    print("Scanning issue records for privacy fields...")
    print("=" * 60)
    
    # Check multiple pages of data
    for cursor in [0, 50, 100]:
        try:
            response = requests.get(
                f"{base_url}/issue",
                headers=headers,
                params={"limit": 20, "cursor": cursor},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("response", {}).get("results", [])
                
                for record in results:
                    # Collect all unique fields
                    all_fields.update(record.keys())
                    
                    # Look for boolean fields and privacy-related names
                    for field, value in record.items():
                        # Boolean fields
                        if isinstance(value, bool):
                            if field not in boolean_fields:
                                boolean_fields[field] = set()
                            boolean_fields[field].add(value)
                        
                        # Privacy-related field names
                        field_lower = field.lower()
                        if any(word in field_lower for word in ['private', 'public', 'visibility', 'hidden', 'confidential', 'secret', 'restricted', 'internal']):
                            privacy_candidates.append((field, value, type(value).__name__))
                            
        except Exception as e:
            print(f"Error at cursor {cursor}: {e}")
    
    print(f"\nTotal unique fields found: {len(all_fields)}")
    print("\nAll fields:")
    for field in sorted(all_fields):
        print(f"  - {field}")
    
    print("\nBoolean fields found:")
    for field, values in boolean_fields.items():
        print(f"  - {field}: values={list(values)}")
    
    if privacy_candidates:
        print("\nPrivacy-related field candidates:")
        for field, value, vtype in set(privacy_candidates):
            print(f"  - {field}: {value} (type: {vtype})")
    
    # Also check if readStatus pattern indicates privacy
    print("\nAnalyzing readStatus patterns...")
    read_status_lengths = []
    for cursor in [0, 50, 100]:
        try:
            response = requests.get(
                f"{base_url}/issue",
                headers=headers,
                params={"limit": 20, "cursor": cursor},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("response", {}).get("results", [])
                
                for record in results:
                    rs = record.get("readStatus")
                    if rs:
                        if isinstance(rs, list):
                            read_status_lengths.append(len(rs))
                        else:
                            read_status_lengths.append(1)
                    else:
                        read_status_lengths.append(0)
                        
        except:
            pass
    
    if read_status_lengths:
        print(f"  ReadStatus distribution: min={min(read_status_lengths)}, max={max(read_status_lengths)}, avg={sum(read_status_lengths)/len(read_status_lengths):.1f}")
        print(f"  Records with 0-2 users (likely private): {sum(1 for l in read_status_lengths if l <= 2)}")
        print(f"  Records with 3+ users (likely public): {sum(1 for l in read_status_lengths if l > 2)}")


if __name__ == "__main__":
    find_private_field()