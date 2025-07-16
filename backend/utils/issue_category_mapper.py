"""Utility for mapping Bubble issue category IDs to frontend category names"""
import json
import os
from typing import Optional, Dict

class IssueCategoryMapper:
    """Maps Bubble.io issue category IDs to frontend category names"""
    
    def __init__(self, mapping_file: Optional[str] = None):
        """Initialize the category mapper
        
        Args:
            mapping_file: Path to the category mapping JSON file. 
                         If not provided, looks for issue_category_lookup.json in backend directory
        """
        if mapping_file is None:
            # Default to the lookup file in backend directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mapping_file = os.path.join(backend_dir, "issue_category_lookup.json")
        
        self.mapping_file = mapping_file
        self.category_mapping = self._load_mapping()
        
        # Frontend categories for validation
        self.valid_categories = [
            "operations", "venue", "marketing", "finance", 
            "technology", "customer_service", "team"
        ]
    
    def _load_mapping(self) -> Dict[str, str]:
        """Load the category mapping from JSON file"""
        try:
            with open(self.mapping_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Category mapping file not found at {self.mapping_file}")
            return {}
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in category mapping file {self.mapping_file}")
            return {}
    
    def map_category(self, bubble_category_id: Optional[str]) -> str:
        """Map a Bubble category ID to frontend category name
        
        Args:
            bubble_category_id: The category ID from Bubble.io
            
        Returns:
            The frontend category name (e.g., 'venue', 'operations', etc.)
            Returns 'unknown' if the ID is not found in mapping
        """
        if not bubble_category_id:
            return "unknown"
        
        return self.category_mapping.get(bubble_category_id, "unknown")
    
    def get_category_label(self, category_name: str) -> str:
        """Get the display label for a category name
        
        Args:
            category_name: The frontend category name (e.g., 'customer_service')
            
        Returns:
            The display label (e.g., 'Customer Service')
        """
        labels = {
            "operations": "Operations",
            "venue": "Venue",
            "marketing": "Marketing",
            "finance": "Finance",
            "technology": "Technology",
            "customer_service": "Customer Service",
            "team": "Team",
            "unknown": "Unknown"
        }
        return labels.get(category_name, "Unknown")
    
    def is_valid_category(self, category_name: str) -> bool:
        """Check if a category name is valid"""
        return category_name in self.valid_categories
    
    def add_mapping(self, bubble_category_id: str, frontend_category: str) -> bool:
        """Add a new category mapping (updates the JSON file)
        
        Args:
            bubble_category_id: The Bubble.io category ID
            frontend_category: The frontend category name
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_valid_category(frontend_category):
            print(f"Error: '{frontend_category}' is not a valid category")
            return False
        
        self.category_mapping[bubble_category_id] = frontend_category
        
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(self.category_mapping, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving category mapping: {e}")
            return False
    
    def get_all_mappings(self) -> Dict[str, str]:
        """Get all category mappings"""
        return self.category_mapping.copy()
    
    def get_unmapped_categories(self, bubble_category_ids: list) -> list:
        """Find category IDs that don't have mappings
        
        Args:
            bubble_category_ids: List of category IDs from Bubble
            
        Returns:
            List of IDs that are not in the mapping
        """
        return [
            cat_id for cat_id in bubble_category_ids 
            if cat_id and cat_id not in self.category_mapping
        ]


# Example usage
if __name__ == "__main__":
    # Initialize mapper
    mapper = IssueCategoryMapper()
    
    # Example: Map a known category ID
    bubble_id = "1683764078523x515115226215481340"
    category = mapper.map_category(bubble_id)
    label = mapper.get_category_label(category)
    
    print(f"Bubble ID: {bubble_id}")
    print(f"Frontend Category: {category}")
    print(f"Display Label: {label}")
    
    # Show all mappings
    print("\nAll Category Mappings:")
    for bubble_id, category in mapper.get_all_mappings().items():
        label = mapper.get_category_label(category)
        print(f"  {bubble_id} -> {category} ({label})")