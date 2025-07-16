"""Test Bubble API connection"""
import os
from dotenv import load_dotenv

# Load environment variables from root .env
load_dotenv(dotenv_path="../.env")

# Check if token is set
token = os.getenv("BUBBLE_API_TOKEN", "")
base_url = os.getenv("BUBBLE_API_BASE", "https://app.bali.love/api/1.1/obj")

print("Environment check:")
print(f"BUBBLE_API_TOKEN is {'set' if token else 'NOT set'}")
print(f"BUBBLE_API_BASE: {base_url}")

if not token:
    print("\n[ERROR] BUBBLE_API_TOKEN is not set in .env file")
    print("Please add it to your .env file:")
    print("BUBBLE_API_TOKEN=your_token_here")
else:
    print("\n[OK] Token is configured, you can run fetch_issues_category_table.py")