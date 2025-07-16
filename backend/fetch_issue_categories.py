"""Fetch all unique issue categories from Bubble API to find the 19 category IDs"""
import os
import json
import requests
from typing import Dict, List, Set
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_all_issue_categories():
    """Fetch all issues and extract unique categories"""
    
    api_token = os.environ.get("BUBBLE_API_TOKEN", "")
    api_base = os.environ.get("BUBBLE_API_BASE", "https://app.bali.love/api/1.1/obj")
    
    if not api_token:
        logger.error("BUBBLE_API_TOKEN not set")
        return
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Track unique categories
    categories_found = defaultdict(int)
    category_examples = defaultdict(list)
    
    # Fetch issues
    cursor = 0
    limit = 100
    total_issues = 0
    
    while True:
        try:
            url = f"{api_base}/issue"
            params = {
                "cursor": cursor,
                "limit": limit,
                "constraints": json.dumps([])
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data.get("response", {}).get("results", []):
                break
                
            issues = data["response"]["results"]
            total_issues += len(issues)
            
            # Extract categories
            for issue in issues:
                category_id = issue.get("category")
                if category_id:
                    categories_found[category_id] += 1
                    # Store example issue for this category
                    if len(category_examples[category_id]) < 3:
                        category_examples[category_id].append({
                            "name": issue.get("name", ""),
                            "id": issue.get("_id", "")
                        })
            
            cursor += limit
            logger.info(f"Processed {total_issues} issues, found {len(categories_found)} unique categories")
            
            # Stop after 1000 issues for now
            if total_issues >= 1000:
                logger.info("Stopping after 1000 issues for analysis")
                break
                
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            break
    
    # Display results
    print(f"\n=== Found {len(categories_found)} Unique Categories from {total_issues} Issues ===\n")
    
    # Sort by count
    sorted_categories = sorted(categories_found.items(), key=lambda x: x[1], reverse=True)
    
    for category_id, count in sorted_categories:
        print(f"Category ID: {category_id}")
        print(f"  Count: {count} issues")
        print(f"  Example issues:")
        for example in category_examples[category_id][:3]:
            print(f"    - {example['name']} (ID: {example['id']})")
        print()
    
    # Save to file
    output = {
        "total_issues_analyzed": total_issues,
        "unique_categories": len(categories_found),
        "categories": {}
    }
    
    for category_id, count in sorted_categories:
        output["categories"][category_id] = {
            "count": count,
            "examples": category_examples[category_id]
        }
    
    with open("discovered_issue_categories.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"Results saved to discovered_issue_categories.json")
    
    # Also create a simple list for the prompt
    print("\n=== Category IDs for Prompt Update ===")
    for i, (category_id, count) in enumerate(sorted_categories, 1):
        print(f"{i}. Category {i}: {category_id} ({count} issues)")

if __name__ == "__main__":
    fetch_all_issue_categories()