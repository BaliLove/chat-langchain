#!/usr/bin/env python3
"""
Create realistic LangSmith datasets from your actual Bali event planning data.

This script:
1. Loads your real venue and event data from Bubble.io
2. Analyzes for potential duplicates (real ones, not artificial)
3. Creates LangSmith-ready datasets for evaluation
4. Works without database dependency
"""

import os
import json
import sys
from typing import List, Dict, Any
from collections import defaultdict
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_bubble_data_simple() -> Dict[str, List[Dict]]:
    """Load data directly from Bubble.io API without database sync"""
    
    app_url = 'https://app.bali.love/version-test/api/1.1/obj'
    api_token = os.environ.get('BUBBLE_API_TOKEN')
    
    if not api_token:
        print("❌ BUBBLE_API_TOKEN not found in environment variables")
        return {}
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    data_types = ['event', 'venue', 'product', 'booking', 'comment']
    all_data = {}
    
    print("🔄 Loading your actual Bali event planning data...")
    
    for data_type in data_types:
        try:
            print(f"  Loading {data_type}...")
            
            response = requests.get(
                f'{app_url}/{data_type}',
                headers=headers,
                params={'limit': 20},  # Get more records for analysis
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('response', {}).get('results', [])
                all_data[data_type] = results
                print(f"    ✅ Found {len(results)} records")
                
                # Show sample for first data type
                if results and data_type == 'venue':
                    sample = results[0]
                    name = sample.get('name', 'Unknown')
                    print(f"    📍 Sample venue: {name}")
                    
            else:
                print(f"    ❌ Error {response.status_code}")
                all_data[data_type] = []
                
        except Exception as e:
            print(f"    ❌ Error loading {data_type}: {e}")
            all_data[data_type] = []
    
    return all_data


def analyze_venue_duplicates(venues: List[Dict]) -> List[Dict]:
    """Analyze venues for potential duplicates based on real data"""
    
    print(f"\n🔍 Analyzing {len(venues)} venues for potential duplicates...")
    
    potential_duplicates = []
    
    for i, venue1 in enumerate(venues):
        for j, venue2 in enumerate(venues[i+1:], i+1):
            
            name1 = venue1.get('name', '').lower()
            name2 = venue2.get('name', '').lower()
            
            # Check for similar names
            similarity_score = calculate_name_similarity(name1, name2)
            
            if similarity_score > 0.6:  # 60% similarity threshold
                potential_duplicates.append({
                    'venue_1': {
                        'id': venue1.get('_id', f'venue_{i}'),
                        'name': venue1.get('name', 'Unknown'),
                        'details': extract_venue_details(venue1)
                    },
                    'venue_2': {
                        'id': venue2.get('_id', f'venue_{j}'),
                        'name': venue2.get('name', 'Unknown'),
                        'details': extract_venue_details(venue2)
                    },
                    'similarity_score': similarity_score,
                    'potential_issues': identify_duplicate_issues(venue1, venue2)
                })
    
    if potential_duplicates:
        print(f"  ⚠️  Found {len(potential_duplicates)} potential duplicate pairs")
        for dup in potential_duplicates[:3]:  # Show top 3
            print(f"    🔄 '{dup['venue_1']['name']}' vs '{dup['venue_2']['name']}' ({dup['similarity_score']:.1%} similar)")
    else:
        print("  ✅ No obvious duplicates found in venue names")
    
    return potential_duplicates


def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two venue names"""
    if not name1 or not name2:
        return 0.0
    
    # Simple word overlap calculation
    words1 = set(name1.lower().split())
    words2 = set(name2.lower().split())
    
    if len(words1) == 0 or len(words2) == 0:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


def extract_venue_details(venue: Dict) -> str:
    """Extract key details from venue record"""
    details = []
    
    # Common venue fields
    fields = ['type', 'seats', 'eventTypes', 'location', 'amenities', 'capacity']
    
    for field in fields:
        if field in venue and venue[field]:
            value = venue[field]
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value[:3])  # First 3 items
            details.append(f"{field}: {value}")
    
    return '; '.join(details) if details else "No additional details"


def identify_duplicate_issues(venue1: Dict, venue2: Dict) -> List[str]:
    """Identify specific issues if these venues are duplicates"""
    issues = []
    
    # Check for different IDs but same name
    if venue1.get('name') == venue2.get('name'):
        issues.append("Identical names")
    
    # Check for different capacities
    seats1 = venue1.get('seats')
    seats2 = venue2.get('seats')
    if seats1 and seats2 and seats1 != seats2:
        issues.append(f"Different capacities ({seats1} vs {seats2})")
    
    # Check for different types
    type1 = venue1.get('type')
    type2 = venue2.get('type')
    if type1 and type2 and type1 != type2:
        issues.append(f"Different types ({type1} vs {type2})")
    
    return issues if issues else ["Similar names, needs review"]


def create_langsmith_datasets(data: Dict[str, List[Dict]], duplicates: List[Dict]) -> Dict[str, List[Dict]]:
    """Create LangSmith datasets from real data"""
    
    print("\n📊 Creating LangSmith datasets from your actual data...")
    
    datasets = {}
    
    # Dataset 1: Venue Recommendation
    datasets['venue_recommendations'] = create_venue_recommendation_dataset(data.get('venue', []))
    
    # Dataset 2: Duplicate Detection  
    datasets['duplicate_detection'] = create_duplicate_detection_dataset(duplicates)
    
    # Dataset 3: Service Integration
    datasets['service_integration'] = create_service_integration_dataset(
        data.get('product', []), 
        data.get('venue', [])
    )
    
    # Dataset 4: Client Inquiry Handling
    datasets['client_inquiries'] = create_client_inquiry_dataset(
        data.get('booking', []),
        data.get('event', [])
    )
    
    return datasets


def create_venue_recommendation_dataset(venues: List[Dict]) -> List[Dict]:
    """Create venue recommendation test cases from real venues"""
    
    dataset = []
    
    for venue in venues[:5]:  # Use first 5 venues
        name = venue.get('name', 'Unknown Venue')
        seats = venue.get('seats', 'Unknown')
        venue_type = venue.get('type', 'event space')
        
        # Create realistic queries based on actual venue features
        test_case = {
            "input": f"I need a {venue_type.lower()} venue for approximately {seats} guests",
            "expected_venues": [name],
            "requirements": {
                "capacity": seats,
                "type": venue_type,
                "features": extract_venue_features(venue)
            },
            "metadata": {
                "venue_id": venue.get('_id'),
                "source": "real_venue_data"
            }
        }
        
        dataset.append(test_case)
    
    print(f"  📍 Created {len(dataset)} venue recommendation test cases")
    return dataset


def create_duplicate_detection_dataset(duplicates: List[Dict]) -> List[Dict]:
    """Create duplicate detection test cases from real potential duplicates"""
    
    dataset = []
    
    if not duplicates:
        # If no real duplicates found, create a placeholder
        dataset.append({
            "input": "Review all venues for duplicate listings",
            "expected_output": "No duplicate venues detected in current listings",
            "has_duplicates": False,
            "metadata": {"source": "real_data_analysis"}
        })
        print("  🔍 Created 1 duplicate detection test case (no duplicates found)")
    else:
        for dup in duplicates:
            test_case = {
                "input": f"Are '{dup['venue_1']['name']}' and '{dup['venue_2']['name']}' the same venue?",
                "venue_1_details": dup['venue_1']['details'],
                "venue_2_details": dup['venue_2']['details'],
                "similarity_score": dup['similarity_score'],
                "expected_issues": dup['potential_issues'],
                "requires_review": True,
                "metadata": {"source": "real_duplicate_analysis"}
            }
            dataset.append(test_case)
        
        print(f"  🔄 Created {len(dataset)} duplicate detection test cases")
    
    return dataset


def create_service_integration_dataset(products: List[Dict], venues: List[Dict]) -> List[Dict]:
    """Create service integration test cases"""
    
    dataset = []
    
    if products and venues:
        # Create realistic service + venue combinations
        product_name = products[0].get('name', 'Event Service')
        venue_name = venues[0].get('name', 'Event Venue')
        
        test_case = {
            "input": f"Plan an event using {product_name} at {venue_name}",
            "expected_services": [product_name],
            "expected_venue": venue_name,
            "integration_requirements": ["timing", "logistics", "setup"],
            "metadata": {"source": "real_product_venue_data"}
        }
        
        dataset.append(test_case)
    
    print(f"  🎯 Created {len(dataset)} service integration test cases")
    return dataset


def create_client_inquiry_dataset(bookings: List[Dict], events: List[Dict]) -> List[Dict]:
    """Create client inquiry handling test cases"""
    
    dataset = []
    
    # Create realistic client inquiry scenarios
    common_inquiries = [
        "What's included in your wedding planning package?",
        "Do you handle traditional Balinese ceremonies?",
        "What's the pricing for a 100-person event?",
        "Can you recommend venues for a beachfront wedding?"
    ]
    
    for inquiry in common_inquiries:
        test_case = {
            "input": inquiry,
            "expected_tone": "professional_helpful",
            "should_include_pricing": "pricing" in inquiry.lower(),
            "should_mention_venues": "venue" in inquiry.lower() or "beachfront" in inquiry.lower(),
            "follow_up_required": True,
            "metadata": {"source": "common_client_inquiries"}
        }
        dataset.append(test_case)
    
    print(f"  💬 Created {len(dataset)} client inquiry test cases")
    return dataset


def extract_venue_features(venue: Dict) -> List[str]:
    """Extract key features from venue data"""
    features = []
    
    if venue.get('type'):
        features.append(f"Type: {venue['type']}")
    
    if venue.get('seats'):
        features.append(f"Capacity: {venue['seats']}")
    
    if venue.get('eventTypes'):
        event_types = venue['eventTypes']
        if isinstance(event_types, list) and event_types:
            features.append("Supports multiple event types")
    
    return features


def save_datasets(datasets: Dict[str, List[Dict]], output_dir: str = "langsmith_datasets"):
    """Save datasets to JSON files for LangSmith import"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n💾 Saving datasets to {output_dir}/...")
    
    for dataset_name, dataset_data in datasets.items():
        if dataset_data:  # Only save non-empty datasets
            filename = f"{output_dir}/{dataset_name}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dataset_data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ Saved {len(dataset_data)} examples to {filename}")
    
    print(f"\n🎉 Datasets ready for LangSmith import!")
    print(f"📂 Location: {os.path.abspath(output_dir)}")


def main():
    """Main function to generate LangSmith datasets from real Bali event data"""
    
    print("🚀 CREATING LANGSMITH DATASETS FROM YOUR REAL DATA")
    print("=" * 55)
    
    # Load actual data from Bubble.io
    data = load_bubble_data_simple()
    
    if not any(data.values()):
        print("❌ No data loaded. Check your BUBBLE_API_TOKEN and connection.")
        return
    
    # Analyze for real duplicates
    venues = data.get('venue', [])
    duplicates = analyze_venue_duplicates(venues) if venues else []
    
    # Create LangSmith datasets
    datasets = create_langsmith_datasets(data, duplicates)
    
    # Save datasets
    save_datasets(datasets)
    
    print(f"\n📋 SUMMARY:")
    print(f"   • Loaded data from {len([k for k, v in data.items() if v])} data types")
    print(f"   • Found {len(duplicates)} potential duplicate pairs")
    print(f"   • Created {len(datasets)} datasets for LangSmith")
    print(f"   • Total test cases: {sum(len(d) for d in datasets.values())}")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Import datasets into LangSmith")
    print(f"   2. Set up evaluators from BALI_EVENT_LANGSMITH_GUIDE.md")
    print(f"   3. Start testing with your actual venue data!")


if __name__ == "__main__":
    main() 