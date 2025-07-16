"""Import IssuesCategory data from Bubble to Supabase for easier management"""
import os
import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
import supabase

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IssueCategoryImporter:
    def __init__(self):
        # Bubble API setup
        self.bubble_api_token = os.getenv("BUBBLE_API_TOKEN", "")
        self.bubble_api_base = os.getenv("BUBBLE_API_BASE", "https://app.bali.love/api/1.1/obj")
        
        # Supabase setup
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        
        if not all([self.bubble_api_token, self.supabase_url, self.supabase_key]):
            raise ValueError("Missing required environment variables")
            
        self.supabase_client = supabase.create_client(
            self.supabase_url,
            self.supabase_key
        )
        
    def create_supabase_table(self):
        """Create the issue_categories table in Supabase if it doesn't exist"""
        # Note: This SQL should be run in Supabase SQL editor
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS issue_categories (
            id TEXT PRIMARY KEY,
            bubble_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            display_name TEXT,
            description TEXT,
            sort_order INTEGER,
            is_active BOOLEAN DEFAULT true,
            created_date TIMESTAMP,
            modified_date TIMESTAMP,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create an index on bubble_id for fast lookups
        CREATE INDEX IF NOT EXISTS idx_issue_categories_bubble_id ON issue_categories(bubble_id);
        
        -- Create an index on name for searching
        CREATE INDEX IF NOT EXISTS idx_issue_categories_name ON issue_categories(name);
        
        -- Add RLS policies
        ALTER TABLE issue_categories ENABLE ROW LEVEL SECURITY;
        
        -- Allow all authenticated users to read
        CREATE POLICY "Allow all to read issue categories" ON issue_categories
            FOR SELECT USING (true);
            
        -- Only allow service role to modify
        CREATE POLICY "Only service role can modify issue categories" ON issue_categories
            FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
        """
        
        print("Please run the following SQL in your Supabase SQL editor:")
        print(create_table_sql)
        
    def fetch_bubble_categories(self) -> List[Dict]:
        """Fetch IssuesCategory data from Bubble API"""
        headers = {
            "Authorization": f"Bearer {self.bubble_api_token}",
            "Content-Type": "application/json"
        }
        
        categories = []
        
        # First, let's try to fetch from IssuesCategory data type
        data_types_to_try = ["IssuesCategory", "issuescategory", "issue_category", "category"]
        
        for data_type in data_types_to_try:
            try:
                logger.info(f"Trying to fetch from data type: {data_type}")
                url = f"{self.bubble_api_base}/{data_type}"
                
                cursor = 0
                limit = 100
                
                while True:
                    params = {
                        "cursor": cursor,
                        "limit": limit
                    }
                    
                    response = requests.get(url, headers=headers, params=params)
                    
                    if response.status_code == 404:
                        logger.info(f"Data type {data_type} not found")
                        break
                        
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data.get("response", {}).get("results", []):
                        break
                        
                    results = data["response"]["results"]
                    categories.extend(results)
                    
                    cursor += limit
                    
                    if data.get("response", {}).get("remaining", 0) == 0:
                        break
                
                if categories:
                    logger.info(f"Found {len(categories)} categories from {data_type}")
                    return categories
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code != 404:
                    logger.error(f"Error fetching {data_type}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error fetching {data_type}: {e}")
        
        # If no IssuesCategory table found, extract unique categories from issues
        logger.info("No IssuesCategory data type found. Extracting from issues...")
        return self.extract_categories_from_issues()
    
    def extract_categories_from_issues(self) -> List[Dict]:
        """Extract unique categories from issue data"""
        headers = {
            "Authorization": f"Bearer {self.bubble_api_token}",
            "Content-Type": "application/json"
        }
        
        category_map = {}
        cursor = 0
        limit = 100
        
        while len(category_map) < 50:  # Stop after finding 50 unique categories
            try:
                url = f"{self.bubble_api_base}/issue"
                params = {
                    "cursor": cursor,
                    "limit": limit
                }
                
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                if not data.get("response", {}).get("results", []):
                    break
                    
                issues = data["response"]["results"]
                
                for issue in issues:
                    cat_id = issue.get("category")
                    if cat_id and cat_id not in category_map:
                        # Try to infer category name from issue content
                        category_map[cat_id] = {
                            "_id": cat_id,
                            "bubble_id": cat_id,
                            "name": f"Category_{len(category_map) + 1}",  # Placeholder
                            "example_issue": issue.get("name", ""),
                            "created_date": issue.get("Created Date"),
                            "modified_date": issue.get("Modified Date")
                        }
                
                cursor += limit
                
                if data.get("response", {}).get("remaining", 0) == 0:
                    break
                    
            except Exception as e:
                logger.error(f"Error extracting categories from issues: {e}")
                break
        
        return list(category_map.values())
    
    def map_category_names(self, categories: List[Dict]) -> List[Dict]:
        """Map category IDs to known names"""
        known_mappings = {
            "1683764063723x899495422051483600": "Client Exp",
            "1683764078523x515115226215481340": "Weddings",
            "1698451776177x772559502883684400": "Guests & Accom",
            "1683764027028x314003986352177150": "Event Requests",
            "1683764033628x667123255737843700": "Vendor & Product Requests",
            "1683764048683x626863668112916500": "Catalog",
            # Add more mappings as we discover them
        }
        
        for category in categories:
            bubble_id = category.get("bubble_id") or category.get("_id")
            if bubble_id in known_mappings:
                category["display_name"] = known_mappings[bubble_id]
                category["name"] = known_mappings[bubble_id].lower().replace(" ", "_").replace("&", "and")
            elif "name" not in category:
                category["name"] = f"category_{bubble_id[:8]}"
                category["display_name"] = f"Category {bubble_id[:8]}"
                
        return categories
    
    def import_to_supabase(self, categories: List[Dict]):
        """Import categories to Supabase"""
        # Map and prepare data
        categories = self.map_category_names(categories)
        
        records = []
        for idx, cat in enumerate(categories):
            bubble_id = cat.get("bubble_id") or cat.get("_id")
            
            record = {
                "id": f"cat_{bubble_id[:16]}",  # Shortened ID for Supabase
                "bubble_id": bubble_id,
                "name": cat.get("name", f"category_{idx + 1}"),
                "display_name": cat.get("display_name") or cat.get("name", f"Category {idx + 1}"),
                "description": cat.get("description", ""),
                "sort_order": idx + 1,
                "is_active": True,
                "created_date": cat.get("created_date"),
                "modified_date": cat.get("modified_date"),
                "metadata": {
                    "example_issue": cat.get("example_issue", ""),
                    "original_data": cat
                }
            }
            records.append(record)
        
        # Upsert to Supabase
        try:
            result = self.supabase_client.table("issue_categories").upsert(
                records,
                on_conflict="bubble_id"
            ).execute()
            
            logger.info(f"Successfully imported {len(records)} categories to Supabase")
            return result
            
        except Exception as e:
            logger.error(f"Error importing to Supabase: {e}")
            # Try inserting one by one to identify problematic records
            successful = 0
            for record in records:
                try:
                    self.supabase_client.table("issue_categories").upsert(
                        record,
                        on_conflict="bubble_id"
                    ).execute()
                    successful += 1
                except Exception as e:
                    logger.error(f"Failed to import category {record['bubble_id']}: {e}")
            
            logger.info(f"Imported {successful}/{len(records)} categories")
    
    def export_mapping_file(self, categories: List[Dict]):
        """Export a mapping file for the application"""
        mapping = {}
        
        for cat in categories:
            bubble_id = cat.get("bubble_id") or cat.get("_id")
            mapping[bubble_id] = {
                "name": cat.get("name"),
                "display_name": cat.get("display_name"),
                "description": cat.get("description", "")
            }
        
        # Save to file
        with open("issue_categories_from_bubble.json", "w") as f:
            json.dump(mapping, f, indent=2)
            
        logger.info("Exported category mapping to issue_categories_from_bubble.json")
        
        # Also create a simple lookup
        simple_mapping = {k: v["name"] for k, v in mapping.items()}
        with open("issue_category_bubble_lookup.json", "w") as f:
            json.dump(simple_mapping, f, indent=2)
            
        logger.info("Exported simple lookup to issue_category_bubble_lookup.json")

def main():
    """Main function to run the import"""
    try:
        importer = IssueCategoryImporter()
        
        # Show SQL for table creation
        print("\n=== Step 1: Create Supabase Table ===")
        importer.create_supabase_table()
        
        input("\nPress Enter after creating the table in Supabase...")
        
        # Fetch categories from Bubble
        print("\n=== Step 2: Fetching Categories from Bubble ===")
        categories = importer.fetch_bubble_categories()
        
        if not categories:
            logger.error("No categories found")
            return
            
        print(f"\nFound {len(categories)} categories")
        
        # Show first few categories
        print("\nFirst 5 categories:")
        for cat in categories[:5]:
            print(f"  - {cat.get('_id', 'N/A')}: {cat.get('name', 'Unknown')}")
        
        # Import to Supabase
        print("\n=== Step 3: Importing to Supabase ===")
        importer.import_to_supabase(categories)
        
        # Export mapping files
        print("\n=== Step 4: Exporting Mapping Files ===")
        importer.export_mapping_file(categories)
        
        print("\n✅ Import complete!")
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise

if __name__ == "__main__":
    main()