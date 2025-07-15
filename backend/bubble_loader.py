"""
Bubble.io Data Loader for LangChain Vector Database Integration

This module provides classes and functions to load, process, and integrate
data from Bubble.io applications into LangChain document format for vector storage.
"""

import requests
import json
import os
import time
import logging
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

from langchain_core.documents import Document
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BubbleConfig:
    """Configuration for Bubble.io integration"""
    app_url: str
    api_token: str
    batch_size: int = 100
    max_content_length: int = 10000
    sync_interval: int = 3600  # 1 hour
    priority_data_types: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.priority_data_types is None:
            self.priority_data_types = [
                # Actual available data types from Bubble.io
                "training",      # Training modules and content
                "event",         # Events
                "product",       # Products
                "venue",         # Venues
                "comment",       # Comments
                "eventreview",   # Event reviews
                "booking",       # Bookings
                "user"           # User profiles
            ]


class BubbleAPIError(Exception):
    """Custom exception for Bubble.io API errors"""
    pass


class BubbleSyncManager:
    """Manages sync state and incremental updates for Bubble.io data"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self._ensure_sync_table()
    
    def _ensure_sync_table(self):
        """Create sync state table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS bubble_sync_state (
            id SERIAL PRIMARY KEY,
            data_type VARCHAR(50) NOT NULL UNIQUE,
            last_sync_timestamp TIMESTAMP WITH TIME ZONE,
            last_successful_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_bubble_sync_data_type 
        ON bubble_sync_state(data_type);
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
    
    def get_last_sync_time(self, data_type: str) -> Optional[datetime]:
        """Get last successful sync time for data type"""
        query = """
        SELECT last_sync_timestamp 
        FROM bubble_sync_state 
        WHERE data_type = :data_type
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"data_type": data_type}).fetchone()
            return result[0] if result and result[0] else None
    
    def update_sync_time(self, data_type: str, sync_time: datetime, count: int = 0):
        """Update sync state after successful processing"""
        upsert_sql = """
        INSERT INTO bubble_sync_state (data_type, last_sync_timestamp, last_successful_count, updated_at)
        VALUES (:data_type, :sync_time, :count, NOW())
        ON CONFLICT (data_type) 
        DO UPDATE SET 
            last_sync_timestamp = :sync_time,
            last_successful_count = :count,
            updated_at = NOW()
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(upsert_sql), {
                "data_type": data_type,
                "sync_time": sync_time,
                "count": count
            })
            conn.commit()
        
        logger.info(f"Updated sync state for {data_type}: {count} records at {sync_time}")
    
    def increment_error_count(self, data_type: str):
        """Increment error count for data type"""
        update_sql = """
        INSERT INTO bubble_sync_state (data_type, error_count, updated_at)
        VALUES (:data_type, 1, NOW())
        ON CONFLICT (data_type) 
        DO UPDATE SET 
            error_count = bubble_sync_state.error_count + 1,
            updated_at = NOW()
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(update_sql), {"data_type": data_type})
            conn.commit()


class BubbleDataMapper:
    """Maps Bubble.io records to LangChain Document format"""
    
    def __init__(self, config: BubbleConfig):
        self.config = config
        self.content_hashes = set()  # For deduplication
    
    def map_record_to_document(self, record: Dict, data_type: str) -> Optional[Document]:
        """Convert a Bubble.io record to LangChain Document"""
        try:
            # Extract content and metadata
            page_content = self._extract_content_fields(record, data_type)
            metadata = self._extract_metadata(record, data_type)
            
            # Validate content quality
            if not self._validate_content_quality(page_content):
                return None
            
            # Check for duplicates
            if self._is_duplicate_content(page_content):
                return None
            
            # Sanitize content
            page_content = self._sanitize_content(page_content)
            
            # Create document
            doc = Document(
                page_content=page_content,
                metadata=metadata
            )
            
            return doc
            
        except Exception as e:
            logger.error(f"Error mapping {data_type} record {record.get('_id', 'unknown')}: {e}")
            return None
    
    def _extract_content_fields(self, record: Dict, data_type: str) -> str:
        """Extract and combine content fields based on data type"""
        
        content_extractors = {
            # Available data type extractors
            "training": self._extract_training_content,
            "event": self._extract_event_content,
            "product": self._extract_product_content,
            "venue": self._extract_venue_content,
            "comment": self._extract_comment_content,
            "eventreview": self._extract_review_content,
            "booking": self._extract_booking_content,
            "user": self._extract_user_content,
        }
        
        extractor = content_extractors.get(data_type, self._extract_generic_content)
        return extractor(record)
    
    def _extract_event_content(self, record: Dict) -> str:
        """Extract content from Event records"""
        content_parts = []
        
        # Add title/name
        if record.get("name"):
            content_parts.append(f"Event: {record['name']}")
        
        # Add description
        if record.get("description"):
            content_parts.append(f"Description: {record['description']}")
        
        # Add instructions
        if record.get("instructions"):
            content_parts.append(f"Instructions: {record['instructions']}")
        
        # Add location details
        if record.get("location") or record.get("venue"):
            location = record.get("location") or record.get("venue")
            content_parts.append(f"Location: {location}")
        
        # Add date information
        if record.get("event_date") or record.get("Event Date"):
            date = record.get("event_date") or record.get("Event Date")
            content_parts.append(f"Date: {date}")
        
        # Add additional details
        for field in ["details", "content", "body", "information"]:
            if record.get(field):
                content_parts.append(f"{field.title()}: {record[field]}")
        
        return "\n".join(content_parts)
    
    def _extract_product_content(self, record: Dict) -> str:
        """Extract content from Product records"""
        content_parts = []
        
        if record.get("name"):
            content_parts.append(f"Product: {record['name']}")
        
        if record.get("description"):
            content_parts.append(f"Description: {record['description']}")
        
        if record.get("specifications"):
            content_parts.append(f"Specifications: {record['specifications']}")
        
        if record.get("features"):
            content_parts.append(f"Features: {record['features']}")
        
        if record.get("category"):
            content_parts.append(f"Category: {record['category']}")
        
        # Add pricing info if available
        if record.get("price"):
            content_parts.append(f"Price: {record['price']}")
        
        return "\n".join(content_parts)
    
    def _extract_venue_content(self, record: Dict) -> str:
        """Extract content from Venue records"""
        content_parts = []
        
        if record.get("name"):
            content_parts.append(f"Venue: {record['name']}")
        
        if record.get("description"):
            content_parts.append(f"Description: {record['description']}")
        
        if record.get("amenities"):
            content_parts.append(f"Amenities: {record['amenities']}")
        
        if record.get("policies"):
            content_parts.append(f"Policies: {record['policies']}")
        
        if record.get("address") or record.get("location"):
            location = record.get("address") or record.get("location")
            content_parts.append(f"Location: {location}")
        
        if record.get("capacity"):
            content_parts.append(f"Capacity: {record['capacity']}")
        
        return "\n".join(content_parts)
    
    def _extract_comment_content(self, record: Dict) -> str:
        """Extract content from Comment records"""
        content_parts = []
        
        # Add context about what's being commented on
        if record.get("related_type") and record.get("related_title"):
            content_parts.append(f"Comment on {record['related_type']}: {record['related_title']}")
        
        # Add user information
        if record.get("user") or record.get("author"):
            user = record.get("user") or record.get("author")
            content_parts.append(f"User: {user}")
        
        # Add comment content
        if record.get("content") or record.get("text") or record.get("comment"):
            comment_text = record.get("content") or record.get("text") or record.get("comment")
            content_parts.append(f"Comment: {comment_text}")
        
        return "\n".join(content_parts)
    
    def _extract_review_content(self, record: Dict) -> str:
        """Extract content from EventReview records"""
        content_parts = []
        
        if record.get("event_name"):
            content_parts.append(f"Review for Event: {record['event_name']}")
        
        if record.get("rating"):
            content_parts.append(f"Rating: {record['rating']}/5")
        
        if record.get("review_text") or record.get("review") or record.get("text"):
            review = record.get("review_text") or record.get("review") or record.get("text")
            content_parts.append(f"Review: {review}")
        
        if record.get("highlights"):
            content_parts.append(f"Highlights: {record['highlights']}")
        
        if record.get("suggestions"):
            content_parts.append(f"Suggestions: {record['suggestions']}")
        
        return "\n".join(content_parts)
    
    def _extract_booking_content(self, record: Dict) -> str:
        """Extract content from Booking records"""
        content_parts = []
        
        if record.get("event_name"):
            content_parts.append(f"Booking for: {record['event_name']}")
        
        if record.get("guest_name"):
            content_parts.append(f"Guest: {record['guest_name']}")
        
        if record.get("special_requests"):
            content_parts.append(f"Special Requests: {record['special_requests']}")
        
        if record.get("requirements"):
            content_parts.append(f"Requirements: {record['requirements']}")
        
        if record.get("notes"):
            content_parts.append(f"Notes: {record['notes']}")
        
        return "\n".join(content_parts)
    
    def _extract_training_content(self, record: Dict) -> str:
        """Extract content from Training records"""
        content_parts = []
        
        # Title is the most important field
        if record.get("title"):
            content_parts.append(f"Training: {record['title']}")
        
        # Extract content - it's in JSON format
        if record.get("content"):
            try:
                content_data = record["content"]
                if isinstance(content_data, str):
                    import json
                    content_data = json.loads(content_data)
                
                # Extract text from blocks
                if isinstance(content_data, dict) and "blocks" in content_data:
                    text_blocks = []
                    for block in content_data["blocks"]:
                        if block.get("type") == "paragraph" and block.get("data", {}).get("text"):
                            text = block["data"]["text"].strip()
                            if text:
                                text_blocks.append(text)
                        elif block.get("type") == "header" and block.get("data", {}).get("text"):
                            text = block["data"]["text"].strip()
                            if text:
                                text_blocks.append(f"### {text}")
                        elif block.get("type") == "list" and block.get("data", {}).get("items"):
                            for item in block["data"]["items"]:
                                if item.strip():
                                    text_blocks.append(f"- {item}")
                    
                    if text_blocks:
                        content_parts.append("Content:\n" + "\n".join(text_blocks))
            except Exception as e:
                logger.debug(f"Could not parse training content JSON: {e}")
                # Fall back to treating as string
                if isinstance(record["content"], str) and len(record["content"]) > 20:
                    content_parts.append(f"Content: {record['content'][:500]}...")
        
        # Add qualifications
        if record.get("qualifications") and isinstance(record["qualifications"], list):
            if record["qualifications"]:
                content_parts.append(f"Qualifications: {', '.join(str(q) for q in record['qualifications'])}")
        
        # Add responsibilities
        if record.get("responsibilities") and isinstance(record["responsibilities"], list):
            if record["responsibilities"]:
                content_parts.append(f"Responsibilities: {', '.join(str(r) for r in record['responsibilities'])}")
        
        # Add who is qualified to train
        if record.get("qualifiedToTrain") and isinstance(record["qualifiedToTrain"], list):
            if record["qualifiedToTrain"]:
                content_parts.append(f"Qualified Trainers: {', '.join(str(t) for t in record['qualifiedToTrain'])}")
        
        # Training order/sequence
        if record.get("order"):
            content_parts.append(f"Training Order: {record['order']}")
        
        # Archive status
        if record.get("isArchive"):
            content_parts.append("Status: Archived")
        
        return "\n".join(content_parts)
    
    def _extract_user_content(self, record: Dict) -> str:
        """Extract content from User records"""
        content_parts = []
        
        # User name
        name_parts = []
        if record.get("firstName"):
            name_parts.append(record["firstName"])
        if record.get("lastName"):
            name_parts.append(record["lastName"])
        
        if name_parts:
            content_parts.append(f"User: {' '.join(name_parts)}")
        elif record.get("email"):
            content_parts.append(f"User: {record['email']}")
        
        # User role/type
        if record.get("role") or record.get("userType"):
            role = record.get("role") or record.get("userType")
            content_parts.append(f"Role: {role}")
        
        # Department/Team
        if record.get("department") or record.get("team"):
            dept = record.get("department") or record.get("team")
            content_parts.append(f"Department: {dept}")
        
        # Bio or description
        if record.get("bio") or record.get("description"):
            bio = record.get("bio") or record.get("description")
            content_parts.append(f"Bio: {bio}")
        
        # Skills or expertise
        if record.get("skills") or record.get("expertise"):
            skills = record.get("skills") or record.get("expertise")
            if isinstance(skills, list):
                content_parts.append(f"Skills: {', '.join(str(s) for s in skills)}")
            else:
                content_parts.append(f"Skills: {skills}")
        
        return "\n".join(content_parts)
    
    
    def _extract_generic_content(self, record: Dict) -> str:
        """Generic content extraction for unknown data types"""
        content_parts = []
        
        # Common content fields to look for
        content_fields = [
            "name", "title", "description", "content", "text", "body",
            "details", "information", "summary", "notes"
        ]
        
        for field in content_fields:
            if record.get(field) and isinstance(record[field], str):
                if len(record[field].strip()) > 10:  # Only substantial content
                    content_parts.append(f"{field.title()}: {record[field]}")
        
        return "\n".join(content_parts)
    
    def _extract_metadata(self, record: Dict, data_type: str) -> Dict:
        """Extract metadata from record"""
        record_id = record.get("_id", "")
        
        metadata = {
            "source": f"bubble://{data_type}/{record_id}",
            "source_type": data_type,
            "source_system": "bubble.io",
            "record_id": record_id,
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
            "url": f"{self.config.app_url.rstrip('/')}/{data_type}/{record_id}",
            "processing_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Add data-type specific metadata
        if data_type == "training":
            metadata.update({
                "title": record.get("title", ""),
                "training_order": record.get("order"),
                "is_archived": record.get("isArchive", False),
                "has_sessions": bool(record.get("trainingSessions")),
                "session_count": len(record.get("trainingSessions", [])) if isinstance(record.get("trainingSessions"), list) else 0
            })
        elif data_type == "event":
            metadata.update({
                "title": record.get("name", ""),
                "event_date": record.get("event_date") or record.get("Event Date"),
                "venue": record.get("venue"),
                "category": record.get("category"),
                "status": record.get("status")
            })
        elif data_type == "product":
            metadata.update({
                "title": record.get("name", ""),
                "category": record.get("category"),
                "price": record.get("price"),
                "vendor": record.get("vendor")
            })
        elif data_type == "venue":
            metadata.update({
                "title": record.get("name", ""),
                "location": record.get("address") or record.get("location"),
                "capacity": record.get("capacity"),
                "venue_type": record.get("type")
            })
        elif data_type == "comment":
            metadata.update({
                "title": f"Comment by {record.get('user', 'Unknown')}",
                "related_type": record.get("related_type"),
                "related_id": record.get("related_id"),
                "user": record.get("user")
            })
        elif data_type == "eventreview":
            metadata.update({
                "title": f"Review: {record.get('event_name', 'Event')}",
                "event_id": record.get("event_id"),
                "rating": record.get("rating"),
                "reviewer": record.get("reviewer_name")
            })
        
        # Add generic title if not set
        if not metadata.get("title"):
            metadata["title"] = record.get("name") or f"{data_type.title()} {record_id[:8]}"
        
        # Remove null/None values from metadata as Pinecone doesn't accept them
        cleaned_metadata = {}
        for key, value in metadata.items():
            if value is not None and value != "":
                cleaned_metadata[key] = value
        
        return cleaned_metadata
    
    def _validate_content_quality(self, content: str) -> bool:
        """Validate content quality before processing"""
        if not content or len(content.strip()) < 20:
            return False
        
        # Check for system-generated content patterns
        system_patterns = [
            "auto-generated", "system message", "placeholder",
            "lorem ipsum", "test data", "sample content"
        ]
        
        content_lower = content.lower()
        if any(pattern in content_lower for pattern in system_patterns):
            return False
        
        # Check content length doesn't exceed limit
        if len(content) > self.config.max_content_length:
            return False
        
        return True
    
    def _is_duplicate_content(self, content: str) -> bool:
        """Check if content is duplicate"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        if content_hash in self.content_hashes:
            return True
        
        self.content_hashes.add(content_hash)
        return False
    
    def _sanitize_content(self, content: str) -> str:
        """Clean and sanitize content"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove HTML tags if present
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove problematic characters
        content = re.sub(r'[^\w\s.,!?;:()\-\'"/@#&]', '', content)
        
        return content.strip()


class BubbleDataLoader:
    """Main loader class for Bubble.io data integration"""
    
    def __init__(self, config: BubbleConfig, sync_manager: BubbleSyncManager):
        self.config = config
        self.sync_manager = sync_manager
        self.data_mapper = BubbleDataMapper(config)
        self.base_url = f"{config.app_url.rstrip('/')}/api/1.1/obj"
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json"
        }
    
    def load_all_data(self, incremental: bool = True) -> List[Document]:
        """Load all data from Bubble.io with optional incremental sync"""
        all_documents = []
        
        logger.info(f"Starting Bubble.io data load (incremental: {incremental})")
        
        for data_type in self.config.priority_data_types:
            try:
                documents = self._load_data_type(data_type, incremental)
                all_documents.extend(documents)
                
                # Update sync state
                if documents:
                    self.sync_manager.update_sync_time(
                        data_type, 
                        datetime.now(timezone.utc), 
                        len(documents)
                    )
                
                logger.info(f"Loaded {len(documents)} documents from {data_type}")
                
            except Exception as e:
                logger.error(f"Failed to load {data_type}: {e}")
                self.sync_manager.increment_error_count(data_type)
                continue
        
        logger.info(f"Total documents loaded from Bubble.io: {len(all_documents)}")
        return all_documents
    
    def _load_data_type(self, data_type: str, incremental: bool) -> List[Document]:
        """Load data for a specific data type"""
        documents = []
        
        # Get last sync time for incremental updates
        last_sync = None
        if incremental:
            last_sync = self.sync_manager.get_last_sync_time(data_type)
        
        # Fetch records
        records = self._fetch_records(data_type, since=last_sync)
        
        # Convert to documents
        for record in records:
            doc = self.data_mapper.map_record_to_document(record, data_type)
            if doc:
                documents.append(doc)
        
        return documents
    
    def _fetch_records(self, data_type: str, since: Optional[datetime] = None) -> List[Dict]:
        """Fetch records from Bubble.io API"""
        all_records = []
        cursor = 0
        
        while True:
            try:
                # Build request parameters
                params = {
                    "cursor": cursor,
                    "limit": self.config.batch_size
                }
                
                # Add incremental filter if needed
                if since:
                    constraints = [{
                        "key": "Modified Date",
                        "constraint_type": "greater than",
                        "value": since.isoformat()
                    }]
                    params["constraints"] = json.dumps(constraints)
                
                # Make API request
                response = requests.get(
                    f"{self.base_url}/{data_type}",
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                
                if response.status_code != 200:
                    if response.status_code == 404:
                        logger.warning(f"Data type {data_type} not found in Bubble.io")
                        break
                    else:
                        raise BubbleAPIError(f"API request failed: {response.status_code}")
                
                data = response.json()
                results = data.get("response", {}).get("results", [])
                
                if not results:
                    break
                
                all_records.extend(results)
                
                # Check if we have more data
                remaining = data.get("response", {}).get("remaining", 0)
                if remaining == 0:
                    break
                
                cursor += len(results)
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching {data_type} at cursor {cursor}: {e}")
                raise
        
        return all_records
    
    def test_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            # Try to fetch one record from the first available data type
            for data_type in self.config.priority_data_types:
                response = requests.get(
                    f"{self.base_url}/{data_type}",
                    headers=self.headers,
                    params={"limit": 1},
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info(f"Bubble.io API connection successful (tested with {data_type})")
                    return True
                elif response.status_code == 404:
                    continue  # Try next data type
                elif response.status_code == 401:
                    logger.error("Bubble.io API authentication failed")
                    return False
                else:
                    logger.error(f"Bubble.io API returned status {response.status_code}")
                    return False
            
            logger.error("No valid Bubble.io endpoints found")
            return False
            
        except Exception as e:
            logger.error(f"Bubble.io API connection test failed: {e}")
            return False


def load_bubble_data() -> List[Document]:
    """
    Main function to load data from Bubble.io for integration with existing ingestion pipeline.
    
    This function is designed to be called from the main ingest_docs() function.
    """
    try:
        # Initialize configuration from environment
        config = BubbleConfig(
            app_url=os.environ.get("BUBBLE_APP_URL", ""),
            api_token=os.environ.get("BUBBLE_API_TOKEN", ""),
            batch_size=int(os.environ.get("BUBBLE_BATCH_SIZE", "100")),
            max_content_length=int(os.environ.get("BUBBLE_MAX_CONTENT_LENGTH", "10000"))
        )
        
        if not config.app_url or not config.api_token:
            logger.warning("Bubble.io configuration missing. Skipping Bubble.io data loading.")
            return []
        
        # Initialize sync manager
        db_url = os.environ.get("RECORD_MANAGER_DB_URL")
        if not db_url:
            logger.error("RECORD_MANAGER_DB_URL not found. Cannot initialize sync manager.")
            return []
        
        sync_manager = BubbleSyncManager(db_url)
        
        # Initialize loader
        loader = BubbleDataLoader(config, sync_manager)
        
        # Test connection
        if not loader.test_connection():
            logger.error("Bubble.io API connection failed")
            return []
        
        # Load data
        documents = loader.load_all_data(incremental=True)
        
        logger.info(f"Successfully loaded {len(documents)} documents from Bubble.io")
        return documents
        
    except Exception as e:
        logger.error(f"Error in Bubble.io data loading: {e}")
        return []  # Return empty list to allow other sources to continue


if __name__ == "__main__":
    # Test the loader
    docs = load_bubble_data()
    print(f"Loaded {len(docs)} documents from Bubble.io")
    
    if docs:
        print("\nSample document:")
        print(f"Content: {docs[0].page_content[:200]}...")
        print(f"Metadata: {docs[0].metadata}") 