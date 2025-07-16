"""Discover issue category IDs and their names from Bubble.io"""
import os
import sys
import requests
from dotenv import load_dotenv
import json
from collections import defaultdict

# Load .env from parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, '.env'))

def fetch_issue_categories():
    """Try to fetch issue categories from Bubble API"""
    
    app_url = os.environ.get("BUBBLE_APP_URL", "")
    api_token = os.environ.get("BUBBLE_API_TOKEN", "")
    
    if not app_url or not api_token:
        print("Missing Bubble.io configuration!")
        return None
    
    base_url = f"{app_url.rstrip('/')}/api/1.1/obj"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Try to fetch IssueCategory or similar data types
    potential_category_types = [
        "issuecategory", "IssueCategory", "issue_category",
        "category", "Category", "issue_type", "IssueType"
    ]
    
    print("Searching for issue category data type...")
    
    for data_type in potential_category_types:
        try:
            response = requests.get(
                f"{base_url}/{data_type}",
                headers=headers,
                params={"limit": 100},  # Get all categories
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("response", {}).get("results", [])
                if results:
                    print(f"Found category data in '{data_type}'!")
                    return results
                    
        except Exception as e:
            continue
    
    return None

def analyze_issues_for_categories():
    """Analyze actual issues to discover category patterns"""
    
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
    
    # Fetch a larger sample of issues to analyze categories
    print("Fetching issues to analyze categories...")
    
    try:
        response = requests.get(
            f"{base_url}/issue",
            headers=headers,
            params={"limit": 100},  # Get more issues
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            issues = data.get("response", {}).get("results", [])
            
            # Analyze categories
            category_analysis = defaultdict(list)
            
            for issue in issues:
                category_id = issue.get("category")
                if category_id:
                    # Collect issue details for each category
                    category_analysis[category_id].append({
                        "name": issue.get("name", ""),
                        "description": issue.get("description", "")[:200],  # First 200 chars
                        "lead": issue.get("lead"),
                        "team": issue.get("team", [])
                    })
            
            # Print analysis
            print(f"\nFound {len(category_analysis)} unique categories across {len(issues)} issues:")
            print("-" * 80)
            
            # Try to infer category names from issue patterns
            category_mapping = {}
            
            for category_id, issues_list in category_analysis.items():
                print(f"\nCategory ID: {category_id}")
                print(f"Number of issues: {len(issues_list)}")
                
                # Show sample issues to help identify the category
                print("Sample issues:")
                for i, issue in enumerate(issues_list[:3]):  # Show first 3
                    print(f"  {i+1}. {issue['name']}")
                    if issue['description']:
                        print(f"     {issue['description'][:100]}...")
                
                # Try to guess the category based on issue names/descriptions
                all_text = " ".join([issue['name'] + " " + issue['description'] 
                                   for issue in issues_list]).lower()
                
                # Category detection logic
                if any(keyword in all_text for keyword in ['venue', 'bbg', 'location', 'resort', 'hotel']):
                    category_mapping[category_id] = "venue"
                elif any(keyword in all_text for keyword in ['marketing', 'campaign', 'brand', 'social']):
                    category_mapping[category_id] = "marketing"
                elif any(keyword in all_text for keyword in ['finance', 'payment', 'budget', 'invoice']):
                    category_mapping[category_id] = "finance"
                elif any(keyword in all_text for keyword in ['tech', 'system', 'bug', 'software', 'website']):
                    category_mapping[category_id] = "technology"
                elif any(keyword in all_text for keyword in ['customer', 'guest', 'service', 'complaint']):
                    category_mapping[category_id] = "customer_service"
                elif any(keyword in all_text for keyword in ['team', 'staff', 'employee', 'hr']):
                    category_mapping[category_id] = "team"
                elif any(keyword in all_text for keyword in ['operation', 'process', 'workflow', 'procedure']):
                    category_mapping[category_id] = "operations"
                else:
                    category_mapping[category_id] = "unknown"
                
                print(f"Inferred category: {category_mapping[category_id]}")
            
            # Save the mapping
            output = {
                "category_mapping": category_mapping,
                "category_details": dict(category_analysis)
            }
            
            with open("issue_category_mapping.json", "w") as f:
                json.dump(output, f, indent=2)
            
            print(f"\nCategory mapping saved to: issue_category_mapping.json")
            
            # Also create a simple mapping file
            simple_mapping = {
                "# Issue Category ID to Name Mapping": "",
                "# Generated from Bubble.io data analysis": "",
                "mapping": category_mapping
            }
            
            with open("category_id_mapping.json", "w") as f:
                json.dump(simple_mapping, f, indent=2)
            
            return category_mapping
            
    except Exception as e:
        print(f"Error fetching issues: {e}")
        return None

def main():
    """Main function to discover issue categories"""
    
    print("=== Issue Category Discovery ===\n")
    
    # First try to find a dedicated category data type
    categories = fetch_issue_categories()
    
    if categories:
        print("\nFound dedicated category data:")
        for cat in categories:
            print(f"- ID: {cat.get('_id')}, Name: {cat.get('name', 'Unknown')}")
    else:
        print("\nNo dedicated category data type found.")
        print("Analyzing issues to discover categories...\n")
        
        # Analyze actual issues to discover categories
        category_mapping = analyze_issues_for_categories()
        
        if category_mapping:
            print("\n=== Final Category Mapping ===")
            for cat_id, cat_name in category_mapping.items():
                print(f"{cat_id} -> {cat_name}")

if __name__ == "__main__":
    main()