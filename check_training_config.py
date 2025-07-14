"""Check training data ingestion configuration"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Training Data Ingestion Configuration ===\n")

# Check required environment variables
env_status = {
    "BUBBLE_API_TOKEN": os.getenv("BUBBLE_API_TOKEN") is not None,
    "SUPABASE_URL": os.getenv("SUPABASE_URL") is not None,
    "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY") is not None,
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY") is not None,
    "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY") is not None,
    "PINECONE_INDEX_NAME": os.getenv("PINECONE_INDEX_NAME") is not None
}

configured = sum(env_status.values())
total = len(env_status)

print("Environment Variables:")
for var, is_set in env_status.items():
    status = "[OK]" if is_set else "[MISSING]"
    print(f"{status} {var}")

print(f"\nConfigured: {configured}/{total}")

# Check Bubble connection if token is available
if env_status["BUBBLE_API_TOKEN"]:
    print("\n=== Testing Bubble API Connection ===")
    import requests
    
    try:
        headers = {"Authorization": f"Bearer {os.getenv('BUBBLE_API_TOKEN')}"}
        response = requests.get(
            "https://app.bali.love/api/1.1/obj/training_module",
            headers=headers,
            params={"limit": 1}
        )
        
        if response.status_code == 200:
            print("[OK] Successfully connected to Bubble API")
            data = response.json()
            results = data.get("response", {}).get("results", [])
            print(f"[OK] Found {len(results)} training module(s)")
            
            # Check other training data types
            print("\nChecking available training data types:")
            training_types = [
                "training_module",
                "training_session", 
                "employee_training_plan",
                "training_attendance",
                "training_assessment",
                "training_feedback"
            ]
            
            for data_type in training_types:
                try:
                    r = requests.get(
                        f"https://app.bali.love/api/1.1/obj/{data_type}",
                        headers=headers,
                        params={"limit": 1}
                    )
                    if r.status_code == 200:
                        count = len(r.json().get("response", {}).get("results", []))
                        print(f"  {data_type}: Found {count} record(s)")
                    else:
                        print(f"  {data_type}: Error {r.status_code}")
                except:
                    print(f"  {data_type}: Failed to check")
                    
        else:
            print(f"[ERROR] Bubble API returned status {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Error connecting to Bubble: {e}")

# Check if we need Supabase for staging
print("\n=== Database Status ===")
if not env_status["SUPABASE_URL"]:
    print("[WARNING] SUPABASE_URL not configured")
    print("The staging pipeline requires Supabase for data persistence.")
    print("You can still test with sample data or use direct vector store ingestion.")
else:
    print("[OK] Supabase URL configured")

print("\n=== Recommendations ===")
if configured == total:
    print("1. All environment variables are configured!")
    print("2. Run the migration: cd supabase && npx supabase db push")
    print("3. Test with: python test_training_ingestion.py")
    print("4. Run full ingestion: python backend/training_data_pipeline.py")
elif env_status["BUBBLE_API_TOKEN"] and env_status["PINECONE_API_KEY"]:
    print("1. You have Bubble and Pinecone configured")
    print("2. You can test with sample data: python test_training_ingestion.py")
    print("3. For full staging pipeline, configure SUPABASE_URL")
else:
    print("1. Configure missing environment variables in .env file")
    print("2. Get Bubble API token from your Bubble app Settings > API")
    print("3. Ensure Data API is enabled for training data types")