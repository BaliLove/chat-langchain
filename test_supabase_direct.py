"""Test Supabase connection directly"""

import os
from dotenv import load_dotenv

load_dotenv()

# Test direct import
try:
    from supabase import create_client, Client
    print("Supabase import successful")
    
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    print(f"URL: {url}")
    print(f"Key: {key[:20]}...")
    
    if url and key:
        client = create_client(url, key)
        print(f"Client created: {type(client)}")
        
        # Try a simple operation
        try:
            result = client.table("raw_data_staging").select("*").limit(1).execute()
            print(f"Query successful: {result}")
        except Exception as e:
            print(f"Query failed: {e}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()