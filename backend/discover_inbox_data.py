"""
Discover the complete schema and field structure of inbox messages.
This script will examine raw data from InboxConversation and InboxConversationUser
to understand all available fields and relationships.
"""
import os
import json
import logging
import asyncio
from typing import Dict, List, Any
from collections import defaultdict
from dotenv import load_dotenv

from bubble_loader import BubbleConfig, BubbleSyncManager, BubbleDataLoader

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def discover_data_type(loader, data_type: str, sample_size: int = 100) -> Dict[str, Any]:
    """Discover the structure of a data type by examining sample records"""
    import aiohttp
    
    headers = loader.headers if hasattr(loader, 'headers') else {"Authorization": f"Bearer {loader.config.api_token}"}
    url = f"{loader.base_url}/{data_type}"
    
    discovery = {
        "data_type": data_type,
        "total_records": 0,
        "sample_size": 0,
        "fields": {},
        "field_types": defaultdict(set),
        "field_examples": defaultdict(list),
        "relationships": defaultdict(set),
        "event_references": [],
        "contact_fields": [],
        "status_fields": [],
        "reply_fields": [],
        "message_type_indicators": []
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Get total count
            params = {"limit": 1}
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    count = data.get("response", {}).get("count", 0)
                    discovery["total_records"] = count
                    logger.info(f"{data_type}: Found {count} total records")
            
            # Get sample records
            params = {"limit": sample_size}
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    records = data.get("response", {}).get("results", [])
                    discovery["sample_size"] = len(records)
                    
                    # Analyze each record
                    for record in records:
                        for field, value in record.items():
                            # Track field existence
                            if field not in discovery["fields"]:
                                discovery["fields"][field] = {
                                    "count": 0,
                                    "types": set(),
                                    "sample_values": []
                                }
                            
                            discovery["fields"][field]["count"] += 1
                            
                            # Track value types
                            value_type = type(value).__name__
                            if value is not None:
                                discovery["fields"][field]["types"].add(value_type)
                                discovery["field_types"][value_type].add(field)
                            
                            # Collect sample values
                            if value and len(discovery["fields"][field]["sample_values"]) < 5:
                                if isinstance(value, str) and len(value) > 100:
                                    discovery["fields"][field]["sample_values"].append(value[:100] + "...")
                                else:
                                    discovery["fields"][field]["sample_values"].append(str(value))
                            
                            # Check for event references
                            field_lower = field.lower()
                            if "event" in field_lower:
                                discovery["event_references"].append({
                                    "field": field,
                                    "sample_value": str(value) if value else None
                                })
                            
                            # Check for contact/email fields
                            if any(term in field_lower for term in ["email", "contact", "user", "client", "vendor"]):
                                discovery["contact_fields"].append({
                                    "field": field,
                                    "sample_value": str(value)[:50] if value else None
                                })
                            
                            # Check for status/reply fields
                            if any(term in field_lower for term in ["status", "state", "reply", "response", "answered"]):
                                if "reply" in field_lower or "response" in field_lower:
                                    discovery["reply_fields"].append({
                                        "field": field,
                                        "sample_value": str(value) if value else None
                                    })
                                else:
                                    discovery["status_fields"].append({
                                        "field": field,
                                        "sample_value": str(value) if value else None
                                    })
                            
                            # Check for message type indicators
                            if any(term in field_lower for term in ["type", "category", "source", "origin", "sender"]):
                                discovery["message_type_indicators"].append({
                                    "field": field,
                                    "sample_value": str(value)[:50] if value else None
                                })
                            
                            # Track relationships (fields ending with common relationship patterns)
                            if any(pattern in field for pattern in ["_id", "(o)", "_ref", "ID"]) and field != "_id":
                                discovery["relationships"][field].add(str(value) if value else "None")
                    
                    # Convert sets to lists for JSON serialization
                    for field_info in discovery["fields"].values():
                        field_info["types"] = list(field_info["types"])
                    
                    for key in discovery["field_types"]:
                        discovery["field_types"][key] = list(discovery["field_types"][key])
                    
                    for key in discovery["relationships"]:
                        discovery["relationships"][key] = list(discovery["relationships"][key])[:5]  # Limit samples
                    
                    # Remove duplicate entries in special field lists
                    for field_list in ["event_references", "contact_fields", "status_fields", 
                                     "reply_fields", "message_type_indicators"]:
                        seen = set()
                        unique_list = []
                        for item in discovery[field_list]:
                            if item["field"] not in seen:
                                seen.add(item["field"])
                                unique_list.append(item)
                        discovery[field_list] = unique_list
                    
                else:
                    logger.error(f"Failed to fetch {data_type}: {response.status}")
                    
    except Exception as e:
        logger.error(f"Error discovering {data_type}: {e}")
    
    return discovery

async def main():
    """Main discovery function"""
    logger.info("Starting inbox data discovery...")
    
    # Initialize Bubble configuration
    config = BubbleConfig(
        app_url=os.environ.get("BUBBLE_APP_URL", ""),
        api_token=os.environ.get("BUBBLE_API_TOKEN", ""),
        batch_size=int(os.environ.get("BUBBLE_BATCH_SIZE", "100")),
        max_content_length=int(os.environ.get("BUBBLE_MAX_CONTENT_LENGTH", "10000"))
    )
    
    # Initialize sync manager (optional for discovery)
    sync_manager = None
    db_url = os.environ.get("RECORD_MANAGER_DB_URL")
    if db_url:
        sync_manager = BubbleSyncManager(db_url)
    
    # Initialize loader with simple API access
    class SimpleLoader:
        def __init__(self, config):
            self.config = config
            self.base_url = f"{config.app_url.rstrip('/')}/api/1.1/obj"
            self.headers = {
                "Authorization": f"Bearer {config.api_token}",
                "Content-Type": "application/json"
            }
        
        def test_connection(self):
            import requests
            try:
                response = requests.get(
                    f"{self.base_url}/user",
                    headers=self.headers,
                    params={"limit": 1},
                    timeout=10
                )
                return response.status_code == 200
            except:
                return False
    
    loader = SimpleLoader(config)
    
    # Test connection
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    # Discover inbox data types
    discoveries = {}
    
    for data_type in ["InboxConversation", "InboxConversationUser"]:
        logger.info(f"\nDiscovering {data_type} structure...")
        discovery = await discover_data_type(loader, data_type, sample_size=100)
        discoveries[data_type] = discovery
        
        # Print summary
        logger.info(f"\n{data_type} Discovery Summary:")
        logger.info(f"  Total records: {discovery['total_records']}")
        logger.info(f"  Sample size: {discovery['sample_size']}")
        logger.info(f"  Total fields: {len(discovery['fields'])}")
        
        if discovery['event_references']:
            logger.info(f"\n  Event-related fields:")
            for ref in discovery['event_references']:
                logger.info(f"    - {ref['field']}: {ref['sample_value']}")
        
        if discovery['contact_fields']:
            logger.info(f"\n  Contact/User fields:")
            for ref in discovery['contact_fields']:
                logger.info(f"    - {ref['field']}: {ref['sample_value']}")
        
        if discovery['reply_fields']:
            logger.info(f"\n  Reply/Response fields:")
            for ref in discovery['reply_fields']:
                logger.info(f"    - {ref['field']}: {ref['sample_value']}")
        
        if discovery['message_type_indicators']:
            logger.info(f"\n  Message type indicators:")
            for ref in discovery['message_type_indicators']:
                logger.info(f"    - {ref['field']}: {ref['sample_value']}")
    
    # Save to JSON file
    output_file = "inbox_data_discovery.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(discoveries, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nDiscovery results saved to {output_file}")
    
    # Print critical findings
    logger.info("\n" + "="*60)
    logger.info("CRITICAL FINDINGS FOR INBOX MESSAGE MAPPING:")
    logger.info("="*60)
    
    for data_type, discovery in discoveries.items():
        logger.info(f"\n{data_type}:")
        
        # Event mapping fields
        event_fields = [ref['field'] for ref in discovery['event_references']]
        if event_fields:
            logger.info(f"  Event mapping fields: {', '.join(event_fields)}")
        else:
            logger.info("  ⚠️  NO EVENT FIELDS FOUND")
        
        # Contact fields
        contact_fields = [ref['field'] for ref in discovery['contact_fields']]
        if contact_fields:
            logger.info(f"  Contact fields: {', '.join(contact_fields[:5])}")
        
        # Reply status fields
        reply_fields = [ref['field'] for ref in discovery['reply_fields']]
        if reply_fields:
            logger.info(f"  Reply status fields: {', '.join(reply_fields)}")
        
        # Relationships
        if discovery['relationships']:
            logger.info(f"  Relationships: {', '.join(list(discovery['relationships'].keys())[:5])}")
    
    logger.info("\n" + "="*60)
    
    return discoveries

if __name__ == "__main__":
    asyncio.run(main())