"""Verify the training pipeline setup and environment"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("Training Pipeline Setup Verification")
print("=" * 80)

# Check required environment variables
env_checks = {
    "Bubble API": {
        "BUBBLE_API_TOKEN": os.getenv("BUBBLE_API_TOKEN"),
        "BUBBLE_APP_URL": os.getenv("BUBBLE_APP_URL"),
    },
    "Supabase": {
        "NEXT_PUBLIC_SUPABASE_URL": os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
        "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        "DATABASE_URL": os.getenv("DATABASE_URL"),
    },
    "Pinecone": {
        "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY"),
        "PINECONE_INDEX_NAME": os.getenv("PINECONE_INDEX_NAME"),
        "PINECONE_ENVIRONMENT": os.getenv("PINECONE_ENVIRONMENT"),
    },
    "OpenAI": {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    }
}

all_good = True

for category, vars in env_checks.items():
    print(f"\n{category}:")
    print("-" * 40)
    for var_name, var_value in vars.items():
        if var_value:
            # Mask sensitive values
            if "KEY" in var_name or "TOKEN" in var_name:
                masked_value = var_value[:8] + "..." + var_value[-4:] if len(var_value) > 12 else "***"
                print(f"[OK] {var_name}: {masked_value}")
            else:
                print(f"[OK] {var_name}: {var_value}")
        else:
            print(f"[MISSING] {var_name}: NOT SET")
            all_good = False

# Test imports
print("\nPython Package Imports:")
print("-" * 40)

packages = [
    ("langchain_core", "LangChain Core"),
    ("langchain_openai", "LangChain OpenAI"),
    ("langchain_pinecone", "LangChain Pinecone"),
    ("supabase", "Supabase Client"),
    ("aiohttp", "Async HTTP Client"),
]

for package_name, display_name in packages:
    try:
        __import__(package_name)
        print(f"[OK] {display_name}")
    except ImportError:
        print(f"[MISSING] {display_name} - Run: pip install {package_name}")
        all_good = False

# Test connections
print("\nConnection Tests:")
print("-" * 40)

# Test Supabase connection
try:
    from backend.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    # Try a simple query
    result = supabase.table("raw_data_staging").select("*").limit(1).execute()
    print("[OK] Supabase connection successful")
except Exception as e:
    print(f"[FAILED] Supabase connection failed: {e}")
    all_good = False

# Test Pinecone connection
try:
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME")
    if index_name in [idx.name for idx in pc.list_indexes()]:
        print(f"[OK] Pinecone index '{index_name}' exists")
    else:
        print(f"[MISSING] Pinecone index '{index_name}' not found")
        all_good = False
except Exception as e:
    print(f"[FAILED] Pinecone connection failed: {e}")
    all_good = False

# Summary
print("\n" + "=" * 80)
if all_good:
    print("[SUCCESS] All checks passed! Ready to run the training pipeline.")
    print("\nNext steps:")
    print("1. Ensure Supabase tables are created (run migration)")
    print("2. Run test pipeline: python run_training_pipeline.py test")
    print("3. Run full pipeline: python run_training_pipeline.py full")
else:
    print("[ERROR] Some checks failed. Please fix the issues above before running the pipeline.")
    sys.exit(1)