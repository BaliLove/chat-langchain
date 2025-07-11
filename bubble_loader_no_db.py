#!/usr/bin/env python3
"""
Bubble.io Data Loader WITHOUT Database Dependency

This version works without Supabase for immediate LangSmith testing.
Use this while fixing your Supabase connection.
"""

import os
import json
import requests
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_bubble_data_no_db() -> List[Dict]:
    """
    Load Bubble.io data WITHOUT database sync management.
    Perfect for LangSmith dataset creation and testing.
    """
    
    app_url = os.environ.get('BUBBLE_APP_URL', 'https://app.bali.love/version-test/api/1.1/obj')
    api_token = os.environ.get('BUBBLE_API_TOKEN')
    
    if not api_token:
        logger.error("BUBBLE_API_TOKEN not found")
        return []
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # Your actual data types
    data_types = ['event', 'venue', 'product', 'booking', 'comment', 'user', 'team', 'client']
    all_documents = []
    
    logger.info("🔄 Loading Bubble.io data (no database sync)...")
    
    for data_type in data_types:
        try:
            logger.info(f"Loading {data_type}...")
            
            response = requests.get(
                f'{app_url}/{data_type}',
                headers=headers,
                params={'limit': 50},  # More records for testing
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('response', {}).get('results', [])
                
                # Convert to document format
                for record in records:
                    doc = convert_record_to_document(record, data_type)
                    if doc:
                        all_documents.append(doc)
                
                logger.info(f"✅ Loaded {len(records)} {data_type} records")
                
            else:
                logger.warning(f"❌ Error loading {data_type}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Failed to load {data_type}: {e}")
    
    logger.info(f"🎉 Total documents loaded: {len(all_documents)}")
    return all_documents


def convert_record_to_document(record: Dict, data_type: str) -> Optional[Dict]:
    """Convert Bubble.io record to LangChain-style document"""
    
    try:
        # Extract content based on data type
        content = extract_content_by_type(record, data_type)
        
        if not content or len(content.strip()) < 10:
            return None  # Skip empty content
        
        # Create metadata
        metadata = {
            'data_type': data_type,
            'id': record.get('_id', f'{data_type}_{datetime.now().timestamp()}'),
            'created_date': record.get('Created Date'),
            'modified_date': record.get('Modified Date'),
            'source': 'bubble_io_production'
        }
        
        # Add type-specific metadata
        if data_type == 'venue':
            metadata.update({
                'venue_type': record.get('type'),
                'capacity': record.get('seats'),
                'name': record.get('name')
            })
        elif data_type == 'event':
            metadata.update({
                'event_name': record.get('name'),
                'venue': record.get('venue')
            })
        elif data_type == 'product':
            metadata.update({
                'product_name': record.get('name'),
                'price_model': record.get('priceModel')
            })
        
        return {
            'page_content': content,
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"Error converting {data_type} record: {e}")
        return None


def extract_content_by_type(record: Dict, data_type: str) -> str:
    """Extract meaningful content from different data types"""
    
    content_parts = []
    
    if data_type == 'venue':
        if record.get('name'):
            content_parts.append(f"Venue: {record['name']}")
        
        if record.get('type'):
            content_parts.append(f"Type: {record['type']}")
        
        if record.get('seats'):
            content_parts.append(f"Capacity: {record['seats']} guests")
        
        if record.get('eventTypes'):
            event_types = record['eventTypes']
            if isinstance(event_types, list):
                content_parts.append(f"Supports: {len(event_types)} event types")
        
        if record.get('location'):
            content_parts.append(f"Location: {record['location']}")
    
    elif data_type == 'event':
        if record.get('name'):
            content_parts.append(f"Event: {record['name']}")
        
        if record.get('eventType'):
            content_parts.append(f"Type: {record['eventType']}")
        
        if record.get('venue'):
            content_parts.append(f"Venue: {record['venue']}")
        
        if record.get('bookingCount'):
            content_parts.append(f"Bookings: {record['bookingCount']}")
    
    elif data_type == 'product':
        if record.get('name'):
            content_parts.append(f"Service: {record['name']}")
        
        if record.get('priceModel'):
            content_parts.append(f"Pricing: {record['priceModel']}")
        
        if record.get('categories'):
            categories = record['categories']
            if isinstance(categories, list):
                content_parts.append(f"Categories: {len(categories)} types")
    
    elif data_type == 'booking':
        if record.get('code'):
            content_parts.append(f"Booking: {record['code']}")
        
        if record.get('currency'):
            content_parts.append(f"Currency: {record['currency']}")
        
        if record.get('fullyPaidClient?'):
            status = "Paid" if record['fullyPaidClient?'] else "Pending"
            content_parts.append(f"Payment: {status}")
    
    elif data_type == 'comment':
        if record.get('Comment Text'):
            text = record['Comment Text'][:200]  # Limit length
            content_parts.append(f"Comment: {text}")
        
        if record.get('Created By'):
            content_parts.append(f"By: {record['Created By']}")
    
    else:
        # Generic extraction for other types
        for field in ['name', 'title', 'fullName', 'description', 'content']:
            if record.get(field):
                content_parts.append(f"{field.title()}: {record[field]}")
    
    return "\n".join(content_parts)


def create_simple_datasets(documents: List[Dict]) -> Dict[str, List[Dict]]:
    """Create LangSmith datasets from documents (no database required)"""
    
    # Group documents by type
    by_type = {}
    for doc in documents:
        data_type = doc['metadata'].get('data_type', 'unknown')
        if data_type not in by_type:
            by_type[data_type] = []
        by_type[data_type].append(doc)
    
    datasets = {}
    
    # Venue recommendation dataset
    if 'venue' in by_type:
        venues = by_type['venue']
        venue_dataset = []
        
        for venue_doc in venues[:5]:  # Top 5 venues
            venue_name = venue_doc['metadata'].get('name', 'Unknown Venue')
            capacity = venue_doc['metadata'].get('capacity', 'Unknown')
            venue_type = venue_doc['metadata'].get('venue_type', 'venue')
            
            test_case = {
                "input": f"I need a {venue_type.lower()} for {capacity} guests",
                "expected_venue": venue_name,
                "venue_content": venue_doc['page_content'],
                "metadata": {
                    "source": "real_bubble_data",
                    "data_type": "venue_recommendation"
                }
            }
            venue_dataset.append(test_case)
        
        datasets['venue_recommendations'] = venue_dataset
    
    # Service inquiry dataset
    if 'product' in by_type:
        products = by_type['product']
        service_dataset = []
        
        for product_doc in products[:3]:  # Top 3 services
            service_name = product_doc['metadata'].get('product_name', 'Service')
            
            test_case = {
                "input": f"Tell me about {service_name}",
                "expected_service": service_name,
                "service_content": product_doc['page_content'],
                "metadata": {
                    "source": "real_bubble_data",
                    "data_type": "service_inquiry"
                }
            }
            service_dataset.append(test_case)
        
        datasets['service_inquiries'] = service_dataset
    
    return datasets


def main():
    """Test the database-free Bubble.io loader"""
    
    print("🚀 TESTING BUBBLE.IO LOADER (NO DATABASE)")
    print("=" * 50)
    
    # Load data
    documents = load_bubble_data_no_db()
    
    if not documents:
        print("❌ No documents loaded")
        return
    
    # Analyze data
    type_counts = {}
    for doc in documents:
        data_type = doc['metadata'].get('data_type', 'unknown')
        type_counts[data_type] = type_counts.get(data_type, 0) + 1
    
    print(f"\n📊 LOADED DATA:")
    for data_type, count in type_counts.items():
        print(f"  {data_type}: {count} documents")
    
    # Create simple datasets
    datasets = create_simple_datasets(documents)
    
    print(f"\n📋 CREATED DATASETS:")
    for dataset_name, dataset_data in datasets.items():
        print(f"  {dataset_name}: {len(dataset_data)} test cases")
    
    # Save datasets
    os.makedirs('langsmith_datasets_no_db', exist_ok=True)
    
    for dataset_name, dataset_data in datasets.items():
        filename = f'langsmith_datasets_no_db/{dataset_name}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dataset_data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Saved {filename}")
    
    print(f"\n🎯 SUCCESS! You can use LangSmith while fixing Supabase.")


if __name__ == "__main__":
    main() 