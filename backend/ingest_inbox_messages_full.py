"""
Full inbox message ingestion.
Ingests ALL inbox conversations and user records.
Based on the pattern from ingest_issues_limited.py
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

# Inbox data types to ingest
INBOX_DATA_TYPES = [
    "InboxConversation",       # Main messaging system
    "InboxConversationUser",   # User-specific inbox data
]

def process_record(record: Dict[str, Any], data_type: str) -> Optional[Document]:
    """Process a single record into a Document"""
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
            
            # Add event reference if present
            event = record.get("event", "")
            if event:
                metadata["event_id"] = event
                
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


async def fetch_and_process_data(loader, data_type: str, limit: int = 1000) -> List[Document]:
    """Fetch and process data with pagination"""
    import aiohttp
    
    headers = {
        "Authorization": f"Bearer {loader.config.api_token}"
    }
    
    all_documents = []
    cursor = 0
    batch_size = min(limit, 100)  # API typically limits to 100 per request
    
    try:
        async with aiohttp.ClientSession() as session:
            while cursor < limit:
                url = f"{loader.base_url}/{data_type}"
                params = {
                    "limit": batch_size,
                    "cursor": cursor
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("response", {}).get("results", [])
                        
                        if not records:
                            break
                        
                        for record in records:
                            doc = process_record(record, data_type)
                            if doc:
                                all_documents.append(doc)
                        
                        cursor += len(records)
                        
                        # Stop if we got fewer records than requested
                        if len(records) < batch_size:
                            break
                            
                        # Log progress
                        if cursor % 500 == 0:
                            logger.info(f"  Processed {cursor} {data_type} records...")
                            
                    else:
                        logger.error(f"Failed to fetch {data_type}: {response.status}")
                        break
        
        logger.info(f"Loaded {len(all_documents)} {data_type} documents")
        
        # Show sample records
        if all_documents and data_type == "InboxConversation":
            logger.info(f"\nSample {data_type} records:")
            for i, doc in enumerate(all_documents[:5]):
                title = doc.metadata.get("title", "No title")
                status = doc.metadata.get("status", "Unknown")
                logger.info(f"  {i+1}. {title} (Status: {status})")
        
        return all_documents
                    
    except Exception as e:
        logger.error(f"Error fetching {data_type}: {e}")
        return all_documents


async def main():
    """Main ingestion function"""
    logger.info("Starting FULL inbox message ingestion...")
    logger.info("This will index ALL client, vendor, and team communications")
    
    # Check required environment variables
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "chat-langchain")
    RECORD_MANAGER_DB_URL = os.environ.get("RECORD_MANAGER_DB_URL")
    
    if not all([PINECONE_API_KEY, RECORD_MANAGER_DB_URL]):
        logger.error("Missing required environment variables!")
        logger.error("Please ensure PINECONE_API_KEY and RECORD_MANAGER_DB_URL are set.")
        return
    
    # Initialize Bubble configuration
    config = BubbleConfig(
        app_url=os.environ.get("BUBBLE_APP_URL", ""),
        api_token=os.environ.get("BUBBLE_API_TOKEN", ""),
        batch_size=int(os.environ.get("BUBBLE_BATCH_SIZE", "100")),
        max_content_length=int(os.environ.get("BUBBLE_MAX_CONTENT_LENGTH", "10000"))
    )
    
    # Initialize sync manager
    sync_manager = BubbleSyncManager(RECORD_MANAGER_DB_URL)
    
    # Initialize loader
    loader = BubbleDataLoader(config, sync_manager)
    
    # Test connection
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    all_docs = []
    
    # Load InboxConversation data (no limit - get all)
    logger.info("\nLoading ALL InboxConversation data...")
    inbox_docs = await fetch_and_process_data(loader, "InboxConversation", limit=10000)
    all_docs.extend(inbox_docs)
    
    # Load InboxConversationUser data (no limit - get all)
    logger.info("\nLoading ALL InboxConversationUser data...")
    user_docs = await fetch_and_process_data(loader, "InboxConversationUser", limit=10000)
    all_docs.extend(user_docs)
    
    logger.info(f"\nTotal inbox documents loaded: {len(all_docs)}")
    
    if not all_docs:
        logger.warning("No inbox messages found to index")
        return
    
    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    # Initialize embeddings
    embeddings = get_embeddings_model()
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_obj = pc.Index(PINECONE_INDEX_NAME)
    
    # Create vector store
    vectorstore = PineconeVectorStore(
        index=index_obj,
        embedding=embeddings,
        text_key="text",
        namespace=""
    )
    
    # Create record manager
    record_manager = SQLRecordManager(
        "pinecone/bubble_inbox_data",
        db_url=RECORD_MANAGER_DB_URL,
    )
    record_manager.create_schema()
    
    # Split documents if needed
    logger.info("Splitting documents...")
    docs_transformed = text_splitter.split_documents(all_docs)
    logger.info(f"Split into {len(docs_transformed)} chunks")
    
    # Ensure metadata is clean
    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""
    
    # Index documents
    logger.info("Indexing inbox message documents...")
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
    
    # Summary by type
    type_counts = defaultdict(int)
    event_count = 0
    status_counts = defaultdict(int)
    
    for doc in all_docs:
        doc_type = doc.metadata.get("source_type", "unknown")
        type_counts[doc_type] += 1
        
        # Track event references
        if doc.metadata.get("event_id"):
            event_count += 1
        
        # Track status for conversations
        if doc_type == "inboxconversation":
            status = doc.metadata.get("status", "Unknown")
            status_counts[status] += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("FULL INBOX MESSAGE INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total inbox documents loaded: {len(all_docs)}")
    logger.info("\nDocuments by type:")
    for doc_type, count in type_counts.items():
        logger.info(f"  - {doc_type}: {count}")
    
    if event_count > 0:
        logger.info(f"\nEvent-linked messages: {event_count}")
    
    if status_counts:
        logger.info("\nConversation status breakdown:")
        for status, count in sorted(status_counts.items()):
            logger.info(f"  - {status}: {count}")
    
    logger.info(f"\nTotal chunks created: {len(docs_transformed)}")
    logger.info(f"Indexing results: {indexing_stats}")
    logger.info("\n[SUCCESS] Inbox messages are now searchable in the vector database!")
    logger.info("=" * 60)
    
    # Update sync state
    if indexing_stats.get("num_added", 0) > 0 or indexing_stats.get("num_updated", 0) > 0:
        for data_type in ["InboxConversation", "InboxConversationUser"]:
            sync_manager.update_sync_state(
                data_type,
                type_counts.get(data_type.lower(), 0)
            )
            logger.info(f"Updated sync state for {data_type}: {type_counts.get(data_type.lower(), 0)} records")
    
    return indexing_stats


if __name__ == "__main__":
    asyncio.run(main())