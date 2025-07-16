"""
Event Ecosystem Ingestion Script
Ingests events and all related data with proper relationships for event-scoped searches
"""
import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

from dotenv import load_dotenv
from pinecone import Pinecone
from langchain.indexes import SQLRecordManager, index
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

from embeddings import get_embeddings_model
from bubble_loader import BubbleConfig, BubbleSyncManager, BubbleDataLoader

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventEcosystemLoader(BubbleDataLoader):
    """Loader for complete event ecosystem with relationship tracking"""
    
    # Core event data types
    CORE_EVENT_TYPES = [
        "event",  # Main event records
    ]
    
    # Related data types that reference events
    EVENT_RELATED_TYPES = [
        "eventsatellite",   # Event extended data
        "eventreview",      # Event reviews
        "eventrsvp",        # RSVP data
        "guestevent",       # Guest-event relationships
        "task",             # Tasks linked to events
        "comment",          # Comments (may be event-related)
        "commentthread",    # Comment threads
        "eventteam",        # Team assignments
    ]
    
    # Contact/Guest types
    CONTACT_TYPES = [
        "guest",            # Guest records
        "guestlist",        # Guest lists
        "contact",          # Contacts
        "client",           # Clients
    ]
    
    def __init__(self, config: BubbleConfig, sync_manager: BubbleSyncManager):
        super().__init__(config, sync_manager)
        # Caches for relationship resolution
        self.events_cache = {}  # event_id -> event details
        self.event_code_map = {}  # event_code -> event_id
        self.guests_cache = {}
        self.users_cache = {}
        self.venues_cache = {}
        self.event_types_cache = {}
        
        # Track relationships
        self.event_documents = defaultdict(list)  # event_code -> [documents]
        
    async def load_event_ecosystem(self, limit_per_type: int = 500) -> List[Document]:
        """Load complete event ecosystem with proper relationships"""
        all_documents = []
        
        logger.info("Starting EVENT ECOSYSTEM ingestion...")
        logger.info("This will enable event-scoped searches using event codes")
        
        # First, load all events to build the code map
        logger.info("\nPhase 1: Loading core event data...")
        await self._load_events(limit_per_type)
        logger.info(f"Loaded {len(self.events_cache)} events with codes")
        
        # Load reference data
        logger.info("\nPhase 2: Loading reference data...")
        await self._load_reference_data()
        
        # Process core events
        logger.info("\nPhase 3: Processing event documents...")
        for event_id, event_data in self.events_cache.items():
            doc = self._process_event(event_data)
            if doc:
                all_documents.append(doc)
                event_code = event_data.get("code", "")
                if event_code:
                    self.event_documents[event_code].append(doc)
        
        # Load and process all related data
        logger.info("\nPhase 4: Loading event-related data...")
        for data_type in self.EVENT_RELATED_TYPES:
            logger.info(f"  Loading {data_type}...")
            related_docs = await self._load_event_related_data(data_type, limit_per_type)
            all_documents.extend(related_docs)
            logger.info(f"  Loaded {len(related_docs)} {data_type} documents")
        
        # Load contact/guest data
        logger.info("\nPhase 5: Loading contact/guest data...")
        for data_type in self.CONTACT_TYPES:
            logger.info(f"  Loading {data_type}...")
            contact_docs = await self._load_contact_data(data_type, limit_per_type)
            all_documents.extend(contact_docs)
            logger.info(f"  Loaded {len(contact_docs)} {data_type} documents")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("EVENT ECOSYSTEM SUMMARY:")
        logger.info("=" * 80)
        logger.info(f"Total documents: {len(all_documents)}")
        logger.info(f"Events with codes: {len(self.event_code_map)}")
        logger.info(f"\nDocuments by event code:")
        for code, docs in sorted(self.event_documents.items())[:10]:
            logger.info(f"  {code}: {len(docs)} documents")
        if len(self.event_documents) > 10:
            logger.info(f"  ... and {len(self.event_documents) - 10} more events")
        logger.info("=" * 80)
        
        return all_documents
    
    async def _load_events(self, limit: int):
        """Load all events and build code mapping"""
        events = await self._fetch_all_records("event", limit)
        
        for event in events:
            event_id = event.get("_id")
            event_code = event.get("code", "")
            
            self.events_cache[event_id] = event
            
            if event_code:
                self.event_code_map[event_code] = event_id
                logger.debug(f"Mapped event code {event_code} -> {event_id}")
    
    async def _load_reference_data(self):
        """Load reference data for enrichment"""
        # Load users
        try:
            users = await self._fetch_all_records("user", limit=200)
            for user in users:
                self.users_cache[user.get("_id")] = {
                    "name": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or user.get("email", "Unknown"),
                    "email": user.get("email", "")
                }
            logger.info(f"  Cached {len(self.users_cache)} users")
        except:
            logger.warning("  Could not load user data")
        
        # Load venues
        try:
            venues = await self._fetch_all_records("venue", limit=100)
            for venue in venues:
                self.venues_cache[venue.get("_id")] = venue.get("name", "Unknown Venue")
            logger.info(f"  Cached {len(self.venues_cache)} venues")
        except:
            logger.warning("  Could not load venue data")
        
        # Load event types
        try:
            event_types = await self._fetch_all_records("eventtype", limit=50)
            for et in event_types:
                self.event_types_cache[et.get("_id")] = {
                    "name": et.get("name", "Unknown Type"),
                    "code": et.get("code", "")
                }
            logger.info(f"  Cached {len(self.event_types_cache)} event types")
        except:
            logger.warning("  Could not load event type data")
    
    async def _load_event_related_data(self, data_type: str, limit: int) -> List[Document]:
        """Load data that has event references"""
        documents = []
        records = await self._fetch_all_records(data_type, limit)
        
        for record in records:
            # Find the event reference
            event_id = self._extract_event_id(record, data_type)
            event_code = None
            
            if event_id and event_id in self.events_cache:
                event_code = self.events_cache[event_id].get("code")
            
            # Process the record
            doc = self._process_event_related_record(record, data_type, event_code)
            if doc:
                documents.append(doc)
                if event_code:
                    self.event_documents[event_code].append(doc)
        
        return documents
    
    async def _load_contact_data(self, data_type: str, limit: int) -> List[Document]:
        """Load contact/guest data"""
        documents = []
        records = await self._fetch_all_records(data_type, limit)
        
        for record in records:
            doc = self._process_contact_record(record, data_type)
            if doc:
                documents.append(doc)
                # Note: Contacts might be linked to multiple events via guestEvents
        
        return documents
    
    def _extract_event_id(self, record: Dict, data_type: str) -> Optional[str]:
        """Extract event ID from various record types"""
        # Direct event field
        if "event" in record:
            return record["event"]
        
        # EventReference field (for timelines)
        if "eventReference" in record:
            return record["eventReference"]
        
        # For guest events
        if data_type.lower() == "guestevent" and "event" in record:
            return record["event"]
        
        return None
    
    def _process_event(self, event: Dict) -> Document:
        """Process main event record"""
        content_parts = []
        
        # Event name and code
        name = event.get("name", "Unnamed Event")
        code = event.get("code", "")
        
        content_parts.append(f"# Event: {name}")
        if code:
            content_parts.append(f"## Event Code: {code}")
            content_parts.append(f"*Use this code to search for all related information*")
        
        # Status
        content_parts.append(f"\n## Status")
        content_parts.append(f"- Status: {event.get('status', 'Unknown')}")
        if event.get("isWedding"):
            content_parts.append(f"- Wedding Event: Yes")
        
        # Event type
        event_type_id = event.get("eventType")
        if event_type_id and event_type_id in self.event_types_cache:
            et_info = self.event_types_cache[event_type_id]
            content_parts.append(f"\n## Event Type")
            content_parts.append(f"- {et_info['name']} ({et_info['code']})")
        
        # Hosts
        if event.get("hosts"):
            content_parts.append(f"\n## Hosts")
            for host_id in event["hosts"]:
                host_name = self.users_cache.get(host_id, {}).get("name", "Host")
                content_parts.append(f"- {host_name}")
        
        # Contact
        if event.get("contactName"):
            content_parts.append(f"\n## Primary Contact")
            content_parts.append(f"- {event['contactName']}")
        
        # Team
        if event.get("team"):
            content_parts.append(f"\n## Team Members")
            content_parts.append(f"- {len(event['team'])} team members assigned")
        
        # Venues
        if event.get("venues"):
            content_parts.append(f"\n## Venues")
            for venue_id in event["venues"][:3]:  # Show first 3
                venue_name = self.venues_cache.get(venue_id, "Venue")
                content_parts.append(f"- {venue_name}")
            if len(event["venues"]) > 3:
                content_parts.append(f"- ... and {len(event['venues']) - 3} more venues")
        
        # Dates
        if event.get("creationDate"):
            content_parts.append(f"\n## Key Dates")
            content_parts.append(f"- Created: {event['creationDate']}")
        
        # Statistics
        content_parts.append(f"\n## Event Statistics")
        if event.get("bookingCount"):
            content_parts.append(f"- Bookings: {event['bookingCount']}")
        if event.get("totalValue"):
            content_parts.append(f"- Total Value: ${event['totalValue']:,.2f}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://event/{event.get('_id')}",
            "source_type": "event",
            "event_code": code,  # CRITICAL for event-scoped search
            "title": f"{name} ({code})" if code else name,
            "record_id": event.get("_id"),
            "event_name": name,
            "status": event.get("status"),
            "is_wedding": event.get("isWedding", False),
            "event_type_id": event.get("eventType"),
            "host_count": len(event.get("hosts", [])),
            "team_count": len(event.get("team", [])),
            "venue_count": len(event.get("venues", [])),
            "booking_count": event.get("bookingCount"),
            "created_date": event.get("Created Date"),
            "modified_date": event.get("Modified Date"),
            "url": f"{self.config.app_url}/event/{event.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_event_related_record(self, record: Dict, data_type: str, event_code: Optional[str]) -> Optional[Document]:
        """Process records that are related to events"""
        
        if data_type == "task":
            return self._process_event_task(record, event_code)
        elif data_type == "comment":
            return self._process_event_comment(record, event_code)
        elif data_type == "guestevent":
            return self._process_guest_event(record, event_code)
        elif data_type == "eventsatellite":
            return self._process_event_satellite(record, event_code)
        elif data_type == "eventreview":
            return self._process_event_review(record, event_code)
        else:
            # Generic processing for other types
            return self._process_generic_event_related(record, data_type, event_code)
    
    def _process_event_task(self, record: Dict, event_code: Optional[str]) -> Document:
        """Process task linked to event"""
        content_parts = []
        
        task_name = record.get("taskName", "Untitled Task")
        content_parts.append(f"# Task: {task_name}")
        
        if event_code:
            content_parts.append(f"\n## Event: {event_code}")
        
        # Task details
        if record.get("taskCode"):
            content_parts.append(f"\n## Task Code: {record['taskCode']}")
        
        content_parts.append(f"\n## Status: {record.get('status', 'Unknown')}")
        
        if record.get("description"):
            content_parts.append(f"\n## Description")
            content_parts.append(record["description"])
        
        if record.get("dueDate"):
            content_parts.append(f"\n## Due Date: {record['dueDate']}")
        
        metadata = {
            "source": f"bubble://task/{record.get('_id')}",
            "source_type": "event_task",
            "event_code": event_code,  # Links to event
            "title": task_name,
            "record_id": record.get("_id"),
            "status": record.get("status"),
            "due_date": record.get("dueDate"),
            "created_date": record.get("Created Date"),
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_event_comment(self, record: Dict, event_code: Optional[str]) -> Document:
        """Process comment that might be event-related"""
        content_parts = []
        
        comment_text = record.get("Comment Text", "")
        content_parts.append(f"# Comment")
        
        if event_code:
            content_parts.append(f"\n## Related to Event: {event_code}")
        
        content_parts.append(f"\n## Content")
        content_parts.append(comment_text)
        
        metadata = {
            "source": f"bubble://comment/{record.get('_id')}",
            "source_type": "event_comment" if event_code else "comment",
            "event_code": event_code,
            "title": f"Comment: {comment_text[:50]}..." if len(comment_text) > 50 else f"Comment: {comment_text}",
            "record_id": record.get("_id"),
            "created_date": record.get("Created Date"),
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_guest_event(self, record: Dict, event_code: Optional[str]) -> Document:
        """Process guest-event relationship"""
        content_parts = []
        
        content_parts.append(f"# Guest Event Record")
        
        if event_code:
            content_parts.append(f"\n## Event: {event_code}")
        
        # Guest info
        guest_id = record.get("guest")
        if guest_id and guest_id in self.guests_cache:
            guest_info = self.guests_cache[guest_id]
            content_parts.append(f"\n## Guest: {guest_info.get('name', 'Unknown Guest')}")
        
        # RSVP Status
        content_parts.append(f"\n## RSVP Status: {record.get('rsvpStatus', 'Unknown')}")
        content_parts.append(f"## Invitation Status: {record.get('invitationStatus', 'Unknown')}")
        
        # Special role
        if record.get("specialRole"):
            content_parts.append(f"\n## Special Role: {record['specialRole']}")
        
        metadata = {
            "source": f"bubble://guestevent/{record.get('_id')}",
            "source_type": "guest_event",
            "event_code": event_code,
            "title": f"Guest RSVP for {event_code}" if event_code else "Guest RSVP",
            "record_id": record.get("_id"),
            "rsvp_status": record.get("rsvpStatus"),
            "invitation_status": record.get("invitationStatus"),
            "created_date": record.get("Created Date"),
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_event_satellite(self, record: Dict, event_code: Optional[str]) -> Document:
        """Process event satellite data"""
        content_parts = []
        
        content_parts.append(f"# Event Additional Information")
        
        if event_code:
            content_parts.append(f"\n## Event: {event_code}")
        
        # Client timezone
        if record.get("clientTZOffset"):
            content_parts.append(f"\n## Client Timezone Offset: {record['clientTZOffset']}")
        
        # Add any other satellite data fields
        for field, value in record.items():
            if field not in ["_id", "event", "Created Date", "Modified Date", "Created By", "clientTZOffset"]:
                content_parts.append(f"\n## {field}: {value}")
        
        metadata = {
            "source": f"bubble://eventsatellite/{record.get('_id')}",
            "source_type": "event_satellite",
            "event_code": event_code,
            "title": f"Event Details for {event_code}" if event_code else "Event Details",
            "record_id": record.get("_id"),
            "created_date": record.get("Created Date"),
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_event_review(self, record: Dict, event_code: Optional[str]) -> Document:
        """Process event review"""
        content_parts = []
        
        content_parts.append(f"# Event Review")
        
        if event_code:
            content_parts.append(f"\n## Event: {event_code}")
        
        # Review status
        content_parts.append(f"\n## Review Status: {record.get('reviewStatus', 'Unknown')}")
        
        # Dates
        if record.get("reviewEmailSentDate"):
            content_parts.append(f"\n## Email Sent: {record['reviewEmailSentDate']}")
        if record.get("reviewSubmittedDate"):
            content_parts.append(f"## Submitted: {record['reviewSubmittedDate']}")
        
        metadata = {
            "source": f"bubble://eventreview/{record.get('_id')}",
            "source_type": "event_review",
            "event_code": event_code,
            "title": f"Review for {event_code}" if event_code else "Event Review",
            "record_id": record.get("_id"),
            "review_status": record.get("reviewStatus"),
            "created_date": record.get("Created Date"),
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_generic_event_related(self, record: Dict, data_type: str, event_code: Optional[str]) -> Document:
        """Generic processor for other event-related types"""
        content_parts = []
        
        content_parts.append(f"# {data_type.title()}")
        
        if event_code:
            content_parts.append(f"\n## Event: {event_code}")
        
        # Add key fields
        for field, value in record.items():
            if field not in ["_id", "event", "Created Date", "Modified Date", "Created By"] and value:
                content_parts.append(f"\n## {field}: {value}")
        
        metadata = {
            "source": f"bubble://{data_type}/{record.get('_id')}",
            "source_type": f"event_{data_type}",
            "event_code": event_code,
            "title": f"{data_type.title()} for {event_code}" if event_code else data_type.title(),
            "record_id": record.get("_id"),
            "created_date": record.get("Created Date"),
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_contact_record(self, record: Dict, data_type: str) -> Document:
        """Process contact/guest records"""
        content_parts = []
        
        if data_type in ["guest", "Guest"]:
            name = f"{record.get('firstName', '')} {record.get('lastName', '')}".strip() or "Unknown Guest"
            content_parts.append(f"# Guest: {name}")
            
            # Guest events
            if record.get("guestEvents"):
                content_parts.append(f"\n## Attending {len(record['guestEvents'])} events")
            
            # Guest lists
            if record.get("guestLists"):
                content_parts.append(f"\n## On {len(record['guestLists'])} guest lists")
                
        elif data_type in ["contact", "Contact"]:
            name = record.get("fullName") or record.get("firstName", "Unknown Contact")
            content_parts.append(f"# Contact: {name}")
            
            if record.get("code"):
                content_parts.append(f"\n## Contact Code: {record['code']}")
                
        elif data_type in ["client", "Client"]:
            content_parts.append(f"# Client Record")
            
            if record.get("events"):
                content_parts.append(f"\n## Associated with {len(record['events'])} events")
        
        # Common fields
        if record.get("email"):
            content_parts.append(f"\n## Email: {record['email']}")
        if record.get("phone"):
            content_parts.append(f"\n## Phone: {record['phone']}")
        
        metadata = {
            "source": f"bubble://{data_type.lower()}/{record.get('_id')}",
            "source_type": data_type.lower(),
            "title": name if 'name' in locals() else f"{data_type} Record",
            "record_id": record.get("_id"),
            "created_date": record.get("Created Date"),
        }
        
        # Add event codes if this contact is linked to specific events
        if record.get("guestEvents") and isinstance(record["guestEvents"], list):
            event_codes = []
            for guest_event_id in record["guestEvents"]:
                # Would need to look up the event code from guest event records
                pass
            if event_codes:
                metadata["related_event_codes"] = event_codes
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    async def _fetch_all_records(self, data_type: str, limit: int = 1000) -> List[Dict]:
        """Fetch all records of a given type"""
        all_records = []
        cursor = 0
        
        while cursor < limit:
            records = await self.fetch_data_from_bubble(
                data_type, 
                limit=min(100, limit - cursor), 
                cursor=cursor
            )
            
            if not records:
                break
                
            all_records.extend(records)
            cursor += len(records)
            
            if len(records) < 100:  # No more records
                break
        
        return all_records
    
    async def fetch_data_from_bubble(self, data_type: str, 
                                   limit: int = 100, 
                                   cursor: int = 0) -> List[Dict[str, Any]]:
        """Fetch data from Bubble API"""
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.config.api_token}"
        }
        
        params = {
            "limit": limit,
            "cursor": cursor
        }
        
        url = f"{self.base_url}/{data_type}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", {}).get("results", [])
                    else:
                        logger.error(f"Error fetching {data_type}: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching from Bubble: {e}")
            return []


async def ingest_event_ecosystem():
    """Main function to ingest complete event ecosystem"""
    
    # Get configuration
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]
    
    logger.info("Starting EVENT ECOSYSTEM ingestion...")
    logger.info("This will enable event-scoped searches using event codes")
    
    # Initialize components
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    embedding = get_embeddings_model()
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_obj = pc.Index(PINECONE_INDEX_NAME)
    vectorstore = PineconeVectorStore(index=index_obj, embedding=embedding)
    
    # Initialize record manager
    record_manager = SQLRecordManager(
        f"pinecone/{PINECONE_INDEX_NAME}", db_url=RECORD_MANAGER_DB_URL
    )
    record_manager.create_schema()
    
    # Initialize Bubble configuration
    config = BubbleConfig(
        app_url=os.environ.get("BUBBLE_APP_URL", ""),
        api_token=os.environ.get("BUBBLE_API_TOKEN", ""),
        batch_size=int(os.environ.get("BUBBLE_BATCH_SIZE", "100")),
        max_content_length=int(os.environ.get("BUBBLE_MAX_CONTENT_LENGTH", "10000"))
    )
    
    if not config.app_url or not config.api_token:
        logger.error("Missing Bubble.io configuration")
        return
    
    # Initialize sync manager
    sync_manager = BubbleSyncManager(RECORD_MANAGER_DB_URL)
    
    # Initialize event ecosystem loader
    loader = EventEcosystemLoader(config, sync_manager)
    
    # Test connection
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    # Load complete event ecosystem
    event_docs = await loader.load_event_ecosystem(limit_per_type=300)
    logger.info(f"\nLoaded {len(event_docs)} event ecosystem documents")
    
    if not event_docs:
        logger.warning("No event documents found!")
        return
    
    # Split documents if needed
    logger.info("Splitting documents...")
    docs_transformed = text_splitter.split_documents(event_docs)
    logger.info(f"Split into {len(docs_transformed)} chunks")
    
    # Ensure metadata is clean
    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""
        # Ensure event_code is preserved
        if "event_code" not in doc.metadata:
            doc.metadata["event_code"] = ""
    
    # Index documents
    logger.info("Indexing event ecosystem documents...")
    indexing_stats = index(
        docs_transformed,
        record_manager,
        vectorstore,
        cleanup="incremental",
        source_id_key="source",
        force_update=(os.environ.get("FORCE_UPDATE") or "false").lower() == "true",
    )
    
    logger.info(f"Indexing complete! Stats: {indexing_stats}")
    
    # Get index stats
    stats = index_obj.describe_index_stats()
    logger.info(f"Pinecone index stats: {stats}")
    
    # Summary by type and event
    type_counts = defaultdict(int)
    event_code_counts = defaultdict(int)
    
    for doc in event_docs:
        type_counts[doc.metadata.get("source_type", "unknown")] += 1
        event_code = doc.metadata.get("event_code", "")
        if event_code:
            event_code_counts[event_code] += 1
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("EVENT ECOSYSTEM INGESTION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total documents loaded: {len(event_docs)}")
    logger.info(f"\nDocuments by type:")
    for doc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  - {doc_type}: {count}")
    logger.info(f"\nEvents with documents:")
    for event_code, count in sorted(event_code_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"  - {event_code}: {count} documents")
    if len(event_code_counts) > 10:
        logger.info(f"  ... and {len(event_code_counts) - 10} more events")
    logger.info(f"\nTotal chunks created: {len(docs_transformed)}")
    logger.info(f"Indexing results: {indexing_stats}")
    logger.info("\n[IMPORTANT] Event codes can now be used to filter searches!")
    logger.info("Example: Search for 'SARLEAD' to find all data for that event")
    logger.info("=" * 80)
    
    return indexing_stats


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_event_ecosystem())