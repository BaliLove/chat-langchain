"""Example script showing how to ingest issues with proper category mapping"""
import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# Add backend to path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from utils.issue_category_mapper import IssueCategoryMapper

# Load environment variables from parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, '.env'))

def fetch_and_process_issues(limit: int = 10):
    """Fetch issues from Bubble and process with category mapping"""
    
    # Initialize category mapper
    mapper = IssueCategoryMapper()
    
    # Bubble API configuration
    app_url = os.environ.get("BUBBLE_APP_URL", "")
    api_token = os.environ.get("BUBBLE_API_TOKEN", "")
    
    if not app_url or not api_token:
        print("Error: Missing Bubble.io configuration!")
        return
    
    base_url = f"{app_url.rstrip('/')}/api/1.1/obj"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    print(f"Fetching issues from Bubble.io (limit: {limit})...")
    
    try:
        # Fetch issues
        response = requests.get(
            f"{base_url}/issue",
            headers=headers,
            params={"limit": limit},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Error fetching issues: Status {response.status_code}")
            return
        
        data = response.json()
        issues = data.get("response", {}).get("results", [])
        
        print(f"\nFetched {len(issues)} issues")
        print("-" * 80)
        
        # Track unmapped categories
        unmapped_categories = set()
        
        # Process each issue
        processed_issues = []
        
        for issue in issues:
            # Extract issue data
            issue_id = issue.get("_id")
            name = issue.get("name", "Untitled")
            bubble_category_id = issue.get("category")
            status = issue.get("status", "Unknown")
            priority = issue.get("priority", "Unknown")
            created_date = issue.get("Created Date")
            
            # Map category
            category = mapper.map_category(bubble_category_id)
            category_label = mapper.get_category_label(category)
            
            # Track unmapped categories
            if category == "unknown" and bubble_category_id:
                unmapped_categories.add(bubble_category_id)
            
            # Create processed issue object
            processed_issue = {
                "id": issue_id,
                "name": name,
                "bubble_category_id": bubble_category_id,
                "category": category,  # Frontend category value
                "category_label": category_label,  # Display label
                "status": status,
                "priority": priority,
                "created_date": created_date,
                "metadata": {
                    "ingested_at": datetime.now().isoformat(),
                    "source": "bubble_api"
                }
            }
            
            processed_issues.append(processed_issue)
            
            # Display summary
            print(f"\nIssue: {name}")
            print(f"  ID: {issue_id}")
            print(f"  Bubble Category ID: {bubble_category_id or 'None'}")
            print(f"  Mapped Category: {category} ({category_label})")
            print(f"  Status: {status}")
            print(f"  Priority: {priority}")
        
        print("\n" + "-" * 80)
        print(f"Processing complete. {len(processed_issues)} issues processed.")
        
        # Report unmapped categories
        if unmapped_categories:
            print(f"\nWarning: Found {len(unmapped_categories)} unmapped category IDs:")
            for cat_id in unmapped_categories:
                print(f"  - {cat_id}")
            print("\nTo map these categories, use:")
            print("  mapper.add_mapping(bubble_category_id, frontend_category)")
        
        # Example: How to use processed issues for vector database
        print("\nExample Vector Database Documents:")
        for issue in processed_issues[:3]:  # Show first 3
            print(f"\n{issue['name']}:")
            print(f"  Document ID: issue_{issue['id']}")
            print(f"  Category Filter: {issue['category']}")
            print(f"  Metadata: category={issue['category']}, status={issue['status']}, priority={issue['priority']}")
        
        return processed_issues
        
    except Exception as e:
        print(f"Error processing issues: {e}")
        return None


def main():
    """Main function"""
    print("=== Issue Ingestion with Category Mapping ===\n")
    
    # Process issues
    processed_issues = fetch_and_process_issues(limit=20)
    
    if processed_issues:
        print(f"\nSuccessfully processed {len(processed_issues)} issues with category mapping")
        
        # Show category distribution
        category_counts = {}
        for issue in processed_issues:
            cat = issue['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        print("\nCategory Distribution:")
        for category, count in sorted(category_counts.items()):
            mapper = IssueCategoryMapper()
            label = mapper.get_category_label(category)
            print(f"  {label}: {count} issues")


if __name__ == "__main__":
    main()