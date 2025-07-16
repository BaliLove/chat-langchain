"""
Enhanced inbox message ingestion with complete event mapping and contact emails.
Ensures every message has an event code and captures contact information.
"""
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from collections import defaultdict
import re

from dotenv import load_dotenv
from pinecone import Pinecone
from langchain.indexes import SQLRecordManager, index
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

from embeddings import get_embeddings_model
from bubble_loader import BubbleConfig, BubbleSyncManager, BubbleDataLoader

# Load environment variables from parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedInboxIngester:
    def __init__(self, loader):
        self.loader = loader
        self.events_cache = {}       # event_id -> event details  
        self.event_code_map = {}     # event_code -> event_id
        self.users_cache = {}        # user_id -> user details with email
        self.conversations_cache = {}  # conversation_id -> conversation details
        self.event_code_patterns = []  # regex patterns for event codes
        
    async def load_all_caches(self):
        """Load all necessary caches for complete mapping"""
        await self.load_event_cache()
        await self.load_user_cache()
        self.build_event_code_patterns()
        
    async def load_event_cache(self):
        """Load event data to build event_id -> event_code mapping"""
        logger.info("Loading event cache for complete event code mapping...")
        
        import aiohttp
        headers = {"Authorization": f"Bearer {self.loader.config.api_token}"}
        url = f"{self.loader.base_url}/event"
        
        try:
            async with aiohttp.ClientSession() as session:
                cursor = 0
                batch_size = 100
                
                while True:
                    params = {"limit": batch_size, "cursor": cursor}
                    
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            events = data.get("response", {}).get("results", [])
                            
                            if not events:
                                break
                                
                            for event in events:
                                event_id = event.get("_id")
                                event_code = event.get("code", "").strip()
                                event_name = event.get("name", "").strip()
                                
                                if event_id:
                                    self.events_cache[event_id] = {
                                        "code": event_code,
                                        "name": event_name,
                                        "full_data": event
                                    }
                                    
                                    if event_code:
                                        self.event_code_map[event_code] = event_id
                            
                            cursor += len(events)
                            if len(events) < batch_size:
                                break
                                
                        else:
                            logger.error(f"Failed to load events: {response.status}")
                            break
                
                logger.info(f"Cached {len(self.events_cache)} events")
                logger.info(f"Found {len(self.event_code_map)} events with codes")
                
        except Exception as e:
            logger.error(f"Error loading event cache: {e}")
    
    async def load_user_cache(self):
        """Load user data to capture contact emails"""
        logger.info("Loading user cache for contact emails...")
        
        import aiohttp
        headers = {"Authorization": f"Bearer {self.loader.config.api_token}"}
        url = f"{self.loader.base_url}/user"
        
        try:
            async with aiohttp.ClientSession() as session:
                cursor = 0
                batch_size = 100
                
                while True:
                    params = {"limit": batch_size, "cursor": cursor}
                    
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            users = data.get("response", {}).get("results", [])
                            
                            if not users:
                                break
                                
                            for user in users:
                                user_id = user.get("_id")
                                if user_id:
                                    self.users_cache[user_id] = {
                                        "name": user.get("Name", "").strip(),
                                        "email": user.get("email", "").strip(),
                                        "full_data": user
                                    }
                            
                            cursor += len(users)
                            if len(users) < batch_size:
                                break
                                
                        else:
                            logger.error(f"Failed to load users: {response.status}")
                            break
                
                logger.info(f"Cached {len(self.users_cache)} users with contact info")
                
        except Exception as e:
            logger.error(f"Error loading user cache: {e}")
    
    def build_event_code_patterns(self):
        """Build regex patterns to extract event codes from text"""
        # Common event code patterns based on the codes we've seen
        self.event_code_patterns = [
            r'([A-Z]{2}\d{6}(?:BBG|VV|GN))',  # Pattern like KM150726VV
            r'([A-Z]{2,4}LEAD)',               # Pattern like SARLEAD
            r'([A-Z]{2,4}\d{6}[A-Z]{2,3})',   # Generic pattern
        ]
    
    def extract_event_code_from_text(self, text: str) -> Optional[str]:
        """Extract event code from text using patterns"""
        if not text:
            return None
            
        for pattern in self.event_code_patterns:
            match = re.search(pattern, text.upper())
            if match:
                extracted_code = match.group(1)
                # Verify it's a real event code
                if extracted_code in self.event_code_map:
                    return extracted_code
        return None
    
    def get_event_code_for_message(self, record: Dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Get event code for a message using multiple strategies"""
        # Strategy 1: Direct event reference
        event_id = record.get("event", "")
        if event_id and event_id in self.events_cache:
            event_info = self.events_cache[event_id]
            return event_info.get("code"), event_info.get("name"), event_id
        
        # Strategy 2: Extract from subject
        subject = record.get("Subject", "")
        if subject:
            extracted_code = self.extract_event_code_from_text(subject)
            if extracted_code:
                event_id = self.event_code_map.get(extracted_code)
                event_name = self.events_cache.get(event_id, {}).get("name", "")
                return extracted_code, event_name, event_id
        
        # Strategy 3: Extract from last message
        last_message = record.get("Last Message", "")
        if last_message:
            extracted_code = self.extract_event_code_from_text(last_message)
            if extracted_code:
                event_id = self.event_code_map.get(extracted_code)
                event_name = self.events_cache.get(event_id, {}).get("name", "")
                return extracted_code, event_name, event_id
        
        return None, None, None
    
    def determine_needs_reply(self, conversation_record: Dict[str, Any], user_record: Dict[str, Any] = None) -> bool:
        """Determine if a message needs a reply based on status and flags"""
        # Check conversation status
        status = conversation_record.get("Status", "").lower()
        status_needs_reply = status in ["open", "pending", "waiting for client", "in progress"]
        
        # Check user-specific reply flag
        user_needs_reply = True
        if user_record:
            user_needs_reply = not user_record.get("noReplyNeeded?", False)
        
        return status_needs_reply and user_needs_reply
    
    def get_contact_info(self, user_id: str) -> tuple[str, str, str]:
        """Get contact information for a user"""
        if user_id in self.users_cache:
            user_info = self.users_cache[user_id]
            return (
                user_info.get("name", ""),
                user_info.get("email", ""),
                "internal" if "@bali.love" in user_info.get("email", "") else "external"
            )
        return "", "", "unknown"
    
    def process_conversation_record(self, record: Dict[str, Any]) -> Optional[Document]:
        """Process a conversation record with complete event and contact mapping"""
        try:
            record_id = record.get("_id", "")
            if not record_id:
                return None
            
            # Get event code (with fallback strategies)
            event_code, event_name, event_id = self.get_event_code_for_message(record)
            
            # If no event code found, use GENERAL
            if not event_code:
                event_code = "GENERAL"
                event_name = "General Communications"
                logger.debug(f"No event code found for conversation {record_id}, using GENERAL")
            
            # Get assignee info
            assignee_id = record.get("Assignee", "")
            assignee_name, assignee_email, assignee_type = self.get_contact_info(assignee_id)
            
            # Build content
            content_parts = []
            
            subject = record.get("Subject", "").strip()
            if subject:
                content_parts.append(f"Subject: {subject}")
            
            last_message = record.get("Last Message", "").strip()
            if last_message:
                content_parts.append(f"Last Message: {last_message}")
            
            status = record.get("Status", "").strip()
            if status:
                content_parts.append(f"Status: {status}")
            
            # Add event information
            content_parts.append(f"Event Code: {event_code}")
            if event_name:
                content_parts.append(f"Event: {event_name}")
            
            # Add assignee info
            if assignee_name:
                content_parts.append(f"Assignee: {assignee_name}")
            
            # Determine if needs reply
            needs_reply = self.determine_needs_reply(record)
            
            # Create metadata
            metadata = {
                "source": f"bubble://InboxConversation/{record_id}",
                "source_type": "inbox_conversation_event" if event_code != "GENERAL" else "inbox_conversation",
                "title": subject if subject else "Inbox Conversation",
                "is_public": True,
                "created_date": record.get("Created Date", ""),
                "modified_date": record.get("Modified Date", ""),
                "event_code": event_code,  # ALWAYS present
                "status": status,
                "needs_reply": needs_reply,
            }
            
            # Add event details
            if event_name:
                metadata["event_name"] = event_name
            if event_id:
                metadata["event_id"] = event_id
            
            # Add assignee contact info
            if assignee_name:
                metadata["assignee_name"] = assignee_name
            if assignee_email:
                metadata["assignee_email"] = assignee_email
            if assignee_type:
                metadata["assignee_type"] = assignee_type
            
            content = "\n".join(content_parts)
            
            # Cache this conversation for user record processing
            self.conversations_cache[record_id] = {
                "event_code": event_code,
                "event_name": event_name,
                "subject": subject,
                "status": status,
                "needs_reply": needs_reply
            }
            
            return Document(page_content=content, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Error processing conversation record {record.get('_id', 'unknown')}: {e}")
            return None
    
    def process_user_record(self, record: Dict[str, Any]) -> Optional[Document]:
        """Process a user record with contact and conversation context"""
        try:
            record_id = record.get("_id", "")
            if not record_id:
                return None
            
            # Get user contact info
            user_id = record.get("User(o)", "")
            user_name, user_email, user_type = self.get_contact_info(user_id)
            
            # Get conversation context
            conversation_id = record.get("Conversation", "")
            conversation_info = self.conversations_cache.get(conversation_id, {})
            
            # Build content
            content_parts = []
            
            if user_name:
                content_parts.append(f"User: {user_name}")
            if user_email:
                content_parts.append(f"Email: {user_email}")
            
            destination = record.get("Destination", "").strip()
            if destination:
                content_parts.append(f"Destination: {destination}")
            
            no_reply_needed = record.get("noReplyNeeded?", False)
            if no_reply_needed:
                content_parts.append("No reply needed")
            
            # Add conversation context
            event_code = conversation_info.get("event_code", "GENERAL")
            if event_code != "GENERAL":
                content_parts.append(f"Event Code: {event_code}")
            
            # Create metadata
            metadata = {
                "source": f"bubble://InboxConversationUser/{record_id}",
                "source_type": "inbox_conversation_user",
                "title": f"Inbox User: {user_name}" if user_name else "Inbox User Record",
                "is_public": True,
                "created_date": record.get("Created Date", ""),
                "modified_date": record.get("Modified Date", ""),
                "event_code": event_code,  # ALWAYS present from conversation
                "no_reply_needed": no_reply_needed,
            }
            
            # Add user contact info
            if user_name:
                metadata["user_name"] = user_name
            if user_email:
                metadata["user_email"] = user_email
            if user_type:
                metadata["user_type"] = user_type
            
            # Add conversation context
            if conversation_id:
                metadata["conversation_id"] = conversation_id
            
            # Add conversation details from cache
            if conversation_info:
                if conversation_info.get("event_name"):
                    metadata["event_name"] = conversation_info["event_name"]
                if conversation_info.get("status"):
                    metadata["conversation_status"] = conversation_info["status"]
                metadata["conversation_needs_reply"] = conversation_info.get("needs_reply", False)
            
            content = "\n".join(content_parts) if content_parts else "Inbox user record"
            
            return Document(page_content=content, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Error processing user record {record.get('_id', 'unknown')}: {e}")
            return None
    
    async def fetch_and_process_data(self, data_type: str, limit: int = 10000) -> List[Document]:
        """Fetch and process data with complete mapping"""
        import aiohttp
        
        headers = {"Authorization": f"Bearer {self.loader.config.api_token}"}
        all_documents = []
        cursor = 0
        batch_size = min(limit, 100)
        
        try:
            async with aiohttp.ClientSession() as session:
                while cursor < limit:
                    url = f"{self.loader.base_url}/{data_type}"
                    params = {"limit": batch_size, "cursor": cursor}
                    
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            records = data.get("response", {}).get("results", [])
                            
                            if not records:
                                break
                            
                            for record in records:
                                if data_type == "InboxConversation":
                                    doc = self.process_conversation_record(record)
                                elif data_type == "InboxConversationUser":
                                    doc = self.process_user_record(record)
                                else:
                                    doc = None
                                
                                if doc:
                                    all_documents.append(doc)
                            
                            cursor += len(records)
                            
                            if len(records) < batch_size:
                                break
                                
                            if cursor % 500 == 0:
                                logger.info(f"  Processed {cursor} {data_type} records...")
                                
                        else:
                            logger.error(f"Failed to fetch {data_type}: {response.status}")
                            break
            
            logger.info(f"Loaded {len(all_documents)} {data_type} documents")
            return all_documents
                        
        except Exception as e:
            logger.error(f"Error fetching {data_type}: {e}")
            return all_documents


async def main():
    """Main ingestion function"""
    logger.info("Starting ENHANCED inbox message ingestion...")
    logger.info("Features: Complete event mapping + Contact emails + Reply status")
    
    # Environment setup - use same pattern as working scripts
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "chat-langchain")
    RECORD_MANAGER_DB_URL = os.environ.get("RECORD_MANAGER_DB_URL")
    
    # If missing, try to continue with warnings (like other scripts)
    if not PINECONE_API_KEY:
        logger.warning("PINECONE_API_KEY not set, may cause issues")
    if not RECORD_MANAGER_DB_URL:
        logger.warning("RECORD_MANAGER_DB_URL not set, may cause issues")
    
    logger.info("Environment check complete, proceeding with ingestion...")
    
    # Initialize Bubble
    config = BubbleConfig(
        app_url=os.environ.get("BUBBLE_APP_URL", ""),
        api_token=os.environ.get("BUBBLE_API_TOKEN", ""),
        batch_size=int(os.environ.get("BUBBLE_BATCH_SIZE", "100")),
        max_content_length=int(os.environ.get("BUBBLE_MAX_CONTENT_LENGTH", "10000"))
    )
    
    sync_manager = BubbleSyncManager(RECORD_MANAGER_DB_URL)
    loader = BubbleDataLoader(config, sync_manager)
    
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    # Initialize enhanced ingester
    ingester = EnhancedInboxIngester(loader)
    
    # Load all caches for complete mapping
    await ingester.load_all_caches()
    
    all_docs = []
    
    # Process conversations first (to build conversation cache)
    logger.info("\nProcessing ALL InboxConversation data...")
    inbox_docs = await ingester.fetch_and_process_data("InboxConversation", limit=10000)
    all_docs.extend(inbox_docs)
    
    # Process user records (using conversation cache)
    logger.info("\nProcessing ALL InboxConversationUser data...")
    user_docs = await ingester.fetch_and_process_data("InboxConversationUser", limit=10000)
    all_docs.extend(user_docs)
    
    logger.info(f"\nTotal inbox documents loaded: {len(all_docs)}")
    
    if not all_docs:
        logger.warning("No inbox messages found")
        return
    
    # Initialize infrastructure - use same pattern as working scripts
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    embeddings = get_embeddings_model()
    
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY or "dummy")
        index_obj = pc.Index(PINECONE_INDEX_NAME)
        
        vectorstore = PineconeVectorStore(
            index=index_obj,
            embedding=embeddings,
            text_key="text",
            namespace=""
        )
        
        record_manager = SQLRecordManager(
            "pinecone/enhanced_inbox_data",
            db_url=RECORD_MANAGER_DB_URL or "sqlite:///temp.db",
        )
        record_manager.create_schema()
    except Exception as e:
        logger.error(f"Infrastructure setup failed: {e}")
        logger.info("Continuing with data processing only...")
        vectorstore = None
        record_manager = None
    
    # Process and index
    logger.info("Splitting documents...")
    docs_transformed = text_splitter.split_documents(all_docs)
    logger.info(f"Split into {len(docs_transformed)} chunks")
    
    logger.info("Indexing enhanced inbox messages...")
    indexing_stats = index(
        docs_transformed,
        record_manager,
        vectorstore,
        cleanup="incremental",
        source_id_key="source",
        force_update=(os.environ.get("FORCE_UPDATE") or "false").lower() == "true",
    )
    
    logger.info(f"Indexing complete! Stats: {indexing_stats}")
    
    # Statistics
    stats = index_obj.describe_index_stats()
    logger.info(f"Pinecone index stats: {stats}")
    
    # Detailed summary
    event_codes = defaultdict(int)
    needs_reply_count = 0
    contact_emails = set()
    
    for doc in all_docs:
        event_code = doc.metadata.get("event_code", "UNKNOWN")
        event_codes[event_code] += 1
        
        if doc.metadata.get("needs_reply"):
            needs_reply_count += 1
        
        user_email = doc.metadata.get("user_email")
        if user_email:
            contact_emails.add(user_email)
    
    logger.info("=" * 60)
    logger.info("ENHANCED INBOX MESSAGE INGESTION - COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total documents: {len(all_docs)}")
    logger.info(f"Messages needing reply: {needs_reply_count}")
    logger.info(f"Unique contact emails: {len(contact_emails)}")
    logger.info(f"Event codes found: {len(event_codes)}")
    
    # Show event distribution
    logger.info("\nTop event codes:")
    for code, count in sorted(event_codes.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"  {code}: {count} messages")
    
    logger.info(f"\nIndexing results: {indexing_stats}")
    logger.info("\n✅ TEAM SEARCH CAPABILITIES ENABLED:")
    logger.info("• Search by event code: event_code='KM150726VV'")
    logger.info("• Find unreplied messages: needs_reply=True")
    logger.info("• Filter by contact email: user_email='client@example.com'")
    logger.info("• Combine filters: event_code='KM150726VV' AND needs_reply=True")
    logger.info("=" * 60)
    
    return indexing_stats


if __name__ == "__main__":
    asyncio.run(main())