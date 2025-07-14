"""Setup and run training data ingestion"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Training Data Ingestion Setup ===\n")

# Check required environment variables
required_vars = {
    "BUBBLE_API_TOKEN": "Your Bubble.io API token (from Settings > API)",
    "SUPABASE_URL": "Your Supabase project URL",
    "SUPABASE_SERVICE_ROLE_KEY": "Your Supabase service role key",
    "OPENAI_API_KEY": "OpenAI API key for embeddings",
    "PINECONE_API_KEY": "Pinecone API key",
    "PINECONE_INDEX_NAME": "Pinecone index name"
}

missing_vars = []
configured_vars = []

for var, description in required_vars.items():
    if os.getenv(var):
        configured_vars.append(var)
        # Don't print the actual value for security
        print(f"[OK] {var}: Configured")
    else:
        missing_vars.append((var, description))
        print(f"[MISSING] {var}: {description}")

print(f"\nConfigured: {len(configured_vars)}/{len(required_vars)}")

if missing_vars:
    print("\n=== Missing Environment Variables ===")
    print("Please add these to your .env file:\n")
    for var, desc in missing_vars:
        print(f"# {desc}")
        print(f"{var}=your-value-here\n")
    
    print("To get these values:")
    print("1. Bubble API Token: Go to your Bubble app Settings > API")
    print("2. Supabase: Get from your Supabase project settings")
    print("3. OpenAI: Get from platform.openai.com/api-keys")
    print("4. Pinecone: Get from app.pinecone.io")
    
    response = input("\nWould you like to test with sample data instead? (y/n): ")
    if response.lower() != 'y':
        print("Please configure the environment variables and run again.")
        sys.exit(1)
    else:
        print("\nWe'll test with sample data...")
        os.environ["USE_SAMPLE_DATA"] = "true"
else:
    print("\n[SUCCESS] All environment variables configured!")
    
    # Check if we can connect to Bubble
    print("\n=== Testing Bubble Connection ===")
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
            count = len(data.get("response", {}).get("results", []))
            print(f"[OK] Found {count} training module(s)")
        else:
            print(f"[ERROR] Bubble API returned status {response.status_code}")
            print("  Please check your API token and ensure Data API is enabled")
            response = input("\nTest with sample data instead? (y/n): ")
            if response.lower() == 'y':
                os.environ["USE_SAMPLE_DATA"] = "true"
    except Exception as e:
        print(f"[ERROR] Error connecting to Bubble: {e}")
        response = input("\nTest with sample data instead? (y/n): ")
        if response.lower() == 'y':
            os.environ["USE_SAMPLE_DATA"] = "true"

print("\n=== Next Steps ===")
print("1. Run the database migration (if not already done)")
print("2. Test the ingestion pipeline with: python test_training_ingestion.py")
print("3. Run full ingestion with: python backend/training_data_pipeline.py")