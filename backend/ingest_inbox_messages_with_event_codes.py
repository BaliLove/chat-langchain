"""
Full inbox message ingestion with proper event code mapping.
Updated to include event_code in metadata for team searchability.
"""
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
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

class InboxIngester:
    def __init__(self, loader):
        self.loader = loader
        self.events_cache = {}      # event_id -> event details  
        self.event_code_map = {}    # event_code -> event_id
        
    async def load_event_cache(self):
        """Load event data to build event_id -> event_code mapping"""
        logger.info("Loading event cache for event code mapping...")
        
        import aiohttp
        headers = {"Authorization": f"Bearer {self.loader.config.api_token}"}
        url = f"{self.loader.base_url}/event"
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {"limit": 1000}  # Load all events for complete mapping
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        events = data.get("response", {}).get("results", [])
                        
                        for event in events:
                            event_id = event.get("_id")
                            event_code = event.get("code", "")  # This is the field teams search by
                            event_name = event.get("name", "")
                            
                            if event_id:
                                self.events_cache[event_id] = {
                                    "code": event_code,
                                    "name": event_name,
                                    "full_data": event
                                }
                                
                                if event_code:
                                    self.event_code_map[event_code] = event_id
                        
                        logger.info(f"Cached {len(self.events_cache)} events")
                        logger.info(f"Found {len(self.event_code_map)} events with codes")
                        
                        # Show sample event codes
                        sample_codes = list(self.event_code_map.keys())[:10]
                        logger.info(f"Sample event codes: {', '.join(sample_codes)}")
                        
                    else:
                        logger.error(f"Failed to load events: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error loading event cache: {e}")
    
    def process_record(self, record: Dict[str, Any], data_type: str) -> Optional[Document]:
        """Process a single record into a Document with event code mapping"""
        try:
            record_id = record.get("_id", "")
            if not record_id:
                return None
            
            content_parts = []
            metadata = {
                "source": f"bubble://{data_type}/{record_id}",
                "source_type": data_type.lower(),
                "is_public": True,  # All messages are public for Bali Love team
                "created_date": record.get("Created Date", ""),
                "modified_date": record.get("Modified Date", ""),
            }
            
            if data_type == "InboxConversation":
                # Extract subject and message
                subject = record.get("Subject", "").strip()
                last_message = record.get("Last Message", "").strip()
                status = record.get("Status", "").strip()
                
                if subject:
                    content_parts.append(f"Subject: {subject}")
                    metadata["title"] = subject
                else:
                    metadata["title"] = "Inbox Conversation"
                
                if last_message:
                    content_parts.append(f"Last Message: {last_message}")
                
                if status:
                    content_parts.append(f"Status: {status}")
                    metadata["status"] = status
                
                # Add assignee if present
                assignee = record.get("Assignee", "")
                if assignee:
                    metadata["assignee_id"] = assignee
                
                # CRITICAL: Map event_id to event_code for team searchability
                event_id = record.get("event", "")
                if event_id and event_id in self.events_cache:
                    event_info = self.events_cache[event_id]
                    event_code = event_info.get("code", "")
                    event_name = event_info.get("name", "")
                    
                    metadata["event_id"] = event_id
                    
                    if event_code:
                        metadata["event_code"] = event_code  # CRITICAL for team searches
                        metadata["event_name"] = event_name
                        metadata["source_type"] = "inbox_conversation_event"  # Mark as event-related
                        
                        # Add event info to content for better search
                        content_parts.append(f"Event Code: {event_code}")
                        if event_name:
                            content_parts.append(f"Event: {event_name}")
                            
                        logger.debug(f"Mapped inbox conversation to event {event_code}")
                    
            elif data_type == "InboxConversationUser":
                # Extract user-specific data
                user_id = record.get("User(o)", "")
                destination = record.get("Destination", "").strip()
                no_reply = record.get("noReplyNeeded?", False)
                
                if user_id:
                    metadata["user_id"] = user_id
                    metadata["title"] = f"Inbox User Record"
                
                if destination:
                    content_parts.append(f"Destination: {destination}")
                
                if no_reply:
                    content_parts.append("No reply needed")
                    metadata["no_reply_needed"] = True
                
                # Add conversation reference
                conversation_id = record.get("Conversation", "")
                if conversation_id:
                    metadata["conversation_id"] = conversation_id
            
            # Create content
            content = "\n".join(content_parts) if content_parts else f"{data_type} record"
            
            return Document(page_content=content, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Error processing {data_type} record {record.get('_id', 'unknown')}: {e}")
            return None

    async def fetch_and_process_data(self, data_type: str, limit: int = 10000) -> List[Document]:
        """Fetch and process data with pagination"""
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
                                doc = self.process_record(record, data_type)
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
    logger.info("Starting FULL inbox message ingestion with EVENT CODE mapping...")
    logger.info("This will enable team searches by event code")
    
    # Check required environment variables
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "chat-langchain")
    RECORD_MANAGER_DB_URL = os.environ.get("RECORD_MANAGER_DB_URL")
    
    if not all([PINECONE_API_KEY, RECORD_MANAGER_DB_URL]):
        logger.error("Missing required environment variables!")
        return
    
    # Initialize Bubble configuration
    config = BubbleConfig(
        app_url=os.environ.get("BUBBLE_APP_URL", ""),
        api_token=os.environ.get("BUBBLE_API_TOKEN", ""),
        batch_size=int(os.environ.get("BUBBLE_BATCH_SIZE", "100")),
        max_content_length=int(os.environ.get("BUBBLE_MAX_CONTENT_LENGTH", "10000"))
    )
    
    # Initialize sync manager and loader
    sync_manager = BubbleSyncManager(RECORD_MANAGER_DB_URL)
    loader = BubbleDataLoader(config, sync_manager)
    
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    # Initialize ingester with event code mapping
    ingester = InboxIngester(loader)
    
    # CRITICAL: Load event cache first for event code mapping
    await ingester.load_event_cache()
    
    all_docs = []
    
    # Load inbox data with event code mapping
    logger.info("\nLoading ALL InboxConversation data with event codes...")
    inbox_docs = await ingester.fetch_and_process_data("InboxConversation", limit=10000)
    all_docs.extend(inbox_docs)
    
    logger.info("\nLoading ALL InboxConversationUser data...")
    user_docs = await ingester.fetch_and_process_data("InboxConversationUser", limit=10000)
    all_docs.extend(user_docs)
    
    logger.info(f"\nTotal inbox documents loaded: {len(all_docs)}")
    
    if not all_docs:
        logger.warning("No inbox messages found to index")
        return
    
    # Initialize infrastructure
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    embeddings = get_embeddings_model()
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_obj = pc.Index(PINECONE_INDEX_NAME)
    
    vectorstore = PineconeVectorStore(
        index=index_obj,
        embedding=embeddings,
        text_key="text",
        namespace=""
    )
    
    record_manager = SQLRecordManager(
        "pinecone/bubble_inbox_data_with_codes",
        db_url=RECORD_MANAGER_DB_URL,
    )
    record_manager.create_schema()
    
    # Process documents
    logger.info("Splitting documents...")
    docs_transformed = text_splitter.split_documents(all_docs)
    logger.info(f"Split into {len(docs_transformed)} chunks")
    
    # Clean metadata
    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""
    
    # Index documents
    logger.info("Indexing inbox message documents with event codes...")
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
    
    # Summary
    type_counts = defaultdict(int)
    event_linked_count = 0
    event_codes_found = set()
    
    for doc in all_docs:
        doc_type = doc.metadata.get("source_type", "unknown")
        type_counts[doc_type] += 1
        
        event_code = doc.metadata.get("event_code")
        if event_code:
            event_linked_count += 1
            event_codes_found.add(event_code)
    
    logger.info("=" * 60)
    logger.info("INBOX MESSAGE INGESTION WITH EVENT CODES - SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total inbox documents loaded: {len(all_docs)}")
    logger.info("\nDocuments by type:")
    for doc_type, count in type_counts.items():
        logger.info(f"  - {doc_type}: {count}")
    
    logger.info(f"\nEvent-linked messages: {event_linked_count}")
    logger.info(f"Unique event codes found: {len(event_codes_found)}")
    
    if event_codes_found:
        sample_codes = list(event_codes_found)[:10]
        logger.info(f"Sample event codes: {', '.join(sample_codes)}")
    
    logger.info(f"\nTotal chunks indexed: {len(docs_transformed)}")
    logger.info(f"Indexing results: {indexing_stats}")
    logger.info("\n[SUCCESS] Team can now search inbox messages by EVENT CODE!")
    logger.info("Example: Filter by event_code='SARLEAD' to find all messages for that event")
    logger.info("=" * 60)
    
    return indexing_stats


if __name__ == "__main__":
    asyncio.run(main())