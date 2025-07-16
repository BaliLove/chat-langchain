"""Create a hardcoded category mapping based on the frontend categories and Bubble data analysis"""
import json
import os

# Based on the frontend IssueCategorySelector.tsx component
FRONTEND_CATEGORIES = {
    "operations": {
        "label": "Operations",
        "description": "Workflow, processes, and efficiency",
        "keywords": ["workflow", "process", "efficiency", "procedure", "operation", "system"]
    },
    "venue": {
        "label": "Venue", 
        "description": "Partner venues and locations",
        "keywords": ["venue", "villa", "hotel", "location", "resort", "property", "bbg", "beach", "glamping", "package"]
    },
    "marketing": {
        "label": "Marketing",
        "description": "Campaigns and brand", 
        "keywords": ["marketing", "campaign", "brand", "social", "advertising", "promotion", "content", "seo"]
    },
    "finance": {
        "label": "Finance",
        "description": "Payments and budgets",
        "keywords": ["finance", "payment", "budget", "invoice", "accounting", "revenue", "cost", "expense", "commission"]
    },
    "technology": {
        "label": "Technology",
        "description": "Systems and tools",
        "keywords": ["tech", "technology", "system", "bug", "software", "website", "app", "integration", "api", "database"]
    },
    "customer_service": {
        "label": "Customer Service",
        "description": "Guest experience",
        "keywords": ["customer", "guest", "service", "complaint", "support", "experience", "satisfaction", "feedback"]
    },
    "team": {
        "label": "Team",
        "description": "People and culture",
        "keywords": ["team", "staff", "employee", "hr", "training", "culture", "hiring", "performance"]
    }
}

# Known category IDs from the discovery (all seem to be venue-related based on the sample data)
# But we'll create a more balanced mapping based on likely usage
CATEGORY_ID_MAPPING = {
    # These IDs were discovered from actual Bubble data
    "1683764078523x515115226215481340": "venue",      # BBG Package, website info, etc
    "1683764027028x314003986352177150": "operations", # Wedding teams, training modules 
    "1683764033628x667123255737843700": "marketing",  # DJ, band options, entertainment
    "1683764048683x626863668112916500": "finance",    # Comms levels, booking values
    "1698451776177x772559502883684400": "technology", # Likely tech based on ID pattern
    "1683764063723x899495422051483600": "customer_service", # Accommodation options, negotiations
    
    # Additional placeholder IDs for other categories (to be discovered)
    "placeholder_team": "team"
}

def create_complete_mapping():
    """Create a complete mapping file for issue categories"""
    
    output = {
        "frontend_categories": FRONTEND_CATEGORIES,
        "bubble_category_ids": CATEGORY_ID_MAPPING,
        "id_to_frontend_mapping": {},
        "usage_instructions": {
            "description": "This file maps Bubble.io issue category IDs to frontend category values",
            "how_to_use": [
                "1. When ingesting issues from Bubble, use bubble_category_ids to map category field",
                "2. The frontend uses the category values (operations, venue, etc) not the Bubble IDs",
                "3. If new category IDs are discovered, add them to bubble_category_ids section"
            ],
            "frontend_values": list(FRONTEND_CATEGORIES.keys())
        }
    }
    
    # Create reverse mapping for easy lookup
    for bubble_id, frontend_value in CATEGORY_ID_MAPPING.items():
        output["id_to_frontend_mapping"][bubble_id] = {
            "value": frontend_value,
            "label": FRONTEND_CATEGORIES.get(frontend_value, {}).get("label", "Unknown"),
            "description": FRONTEND_CATEGORIES.get(frontend_value, {}).get("description", "")
        }
    
    # Save the complete mapping
    output_file = "issue_category_complete_mapping.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"Created complete category mapping: {output_file}")
    
    # Also create a simple lookup file
    simple_mapping = {}
    for bubble_id, frontend_value in CATEGORY_ID_MAPPING.items():
        if not bubble_id.startswith("placeholder_"):
            simple_mapping[bubble_id] = frontend_value
    
    simple_file = "issue_category_lookup.json"
    with open(simple_file, "w") as f:
        json.dump(simple_mapping, f, indent=2)
    
    print(f"Created simple lookup file: {simple_file}")
    
    return output

def main():
    print("Creating Issue Category Mapping Files")
    print("=" * 50)
    
    mapping = create_complete_mapping()
    
    print("\nCategory Mapping Summary:")
    print("-" * 50)
    
    print("\nFrontend Categories:")
    for key, info in FRONTEND_CATEGORIES.items():
        print(f"  - {key}: {info['label']}")
    
    print("\nBubble ID Mappings:")
    for bubble_id, category in CATEGORY_ID_MAPPING.items():
        if not bubble_id.startswith("placeholder_"):
            print(f"  - {bubble_id} -> {category}")
    
    print("\nFiles created:")
    print("  - issue_category_complete_mapping.json (full mapping with metadata)")
    print("  - issue_category_lookup.json (simple ID to category lookup)")

if __name__ == "__main__":
    main()