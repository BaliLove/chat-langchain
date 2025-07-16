"""Fetch the IssuesCategory table from Bubble API"""
import os
import json
import requests
from dotenv import load_dotenv
import logging

# Load from root .env file
load_dotenv(dotenv_path="../.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_issues_category():
    """Try to fetch the IssuesCategory data type from Bubble"""
    
    api_token = os.getenv("BUBBLE_API_TOKEN", "")
    api_base = os.getenv("BUBBLE_API_BASE", "https://app.bali.love/api/1.1/obj")
    
    if not api_token:
        logger.error("BUBBLE_API_TOKEN not set in .env file")
        return
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Try different possible naming conventions
    possible_names = [
        "IssuesCategory",
        "IssueCategory", 
        "issuescategory",
        "issue_category",
        "issues_category",
        "category",
        "Category",
        "issue-category",
        "issues-category"
    ]
    
    for table_name in possible_names:
        logger.info(f"Trying to fetch table: {table_name}")
        
        try:
            url = f"{api_base}/{table_name}"
            params = {
                "limit": 100,
                "cursor": 0
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("response", {}).get("results", [])
                
                if results:
                    logger.info(f"✅ Found {table_name} table with {len(results)} records!")
                    
                    # Display the categories
                    print(f"\n=== Found {len(results)} Categories in '{table_name}' ===\n")
                    
                    # Create mapping for prompt update
                    mapping = {}
                    
                    for idx, category in enumerate(results, 1):
                        cat_id = category.get("_id")
                        cat_name = category.get("name") or category.get("Name") or category.get("title") or category.get("Title") or f"Category_{idx}"
                        
                        print(f"{idx}. {cat_name}")
                        print(f"   ID: {cat_id}")
                        
                        # Show all fields
                        print("   Fields:")
                        for field, value in category.items():
                            if field not in ["_id", "Created Date", "Modified Date", "Created By"]:
                                print(f"     - {field}: {value}")
                        print()
                        
                        mapping[cat_name] = cat_id
                    
                    # Save the mapping
                    with open("bubble_categories_actual.json", "w") as f:
                        json.dump({
                            "table_name": table_name,
                            "categories": mapping,
                            "raw_data": results
                        }, f, indent=2)
                    
                    print(f"✅ Saved category data to bubble_categories_actual.json")
                    
                    # Generate the prompt update
                    print("\n=== Update for issue_category_review_prompt.py ===\n")
                    for name, bubble_id in mapping.items():
                        print(f'- **{name}** - (Bubble ID: {bubble_id})')
                    
                    return results
                    
            elif response.status_code == 404:
                logger.debug(f"Table {table_name} not found (404)")
            else:
                logger.warning(f"Table {table_name} returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching {table_name}: {e}")
    
    logger.error("❌ Could not find IssuesCategory table with any common naming convention")
    logger.info("\nTo find the correct table name:")
    logger.info("1. Check your Bubble.io Data tab")
    logger.info("2. Look for the data type that stores issue categories")
    logger.info("3. Note the exact name (case-sensitive)")
    logger.info("4. Update the 'possible_names' list in this script")

if __name__ == "__main__":
    fetch_issues_category()