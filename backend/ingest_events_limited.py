"""
Limited Event Ecosystem Ingestion for Testing
Focuses on core event data with key relationships
"""
import os
import logging
from datetime import datetime
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

# Limited data types for initial testing
CORE_EVENT_TYPES = ["event"]
KEY_RELATED_TYPES = ["task", "comment", "guest"]  # Most important related data

async def ingest_events_limited():
    """Limited event ingestion focusing on core functionality"""
    
    # Get configuration
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]
    
    logger.info("Starting LIMITED EVENT ingestion (for testing)...")
    logger.info("This will demonstrate event code filtering with key data types")
    
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
    
    # Initialize basic loader
    loader = BubbleDataLoader(config, BubbleSyncManager(RECORD_MANAGER_DB_URL))
    
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    all_docs = []
    event_code_map = {}  # event_id -> event_code
    event_documents = defaultdict(list)  # event_code -> [documents]
    
    # Load events first
    logger.info("\nLoading events to build code mapping...")
    events = await fetch_records(loader, "event", 50)
    
    for event in events:
        event_id = event.get("_id")
        event_code = event.get("code", "")
        
        if event_code:
            event_code_map[event_id] = event_code
        
        # Process event
        doc = process_event(event, config.app_url)
        if doc:
            all_docs.append(doc)
            if event_code:
                event_documents[event_code].append(doc)
    
    logger.info(f"Loaded {len(events)} events with {len(event_code_map)} having codes")
    
    # Load related data
    for data_type in KEY_RELATED_TYPES:
        logger.info(f"\nLoading {data_type} data...")
        records = await fetch_records(loader, data_type, 50)
        
        for record in records:
            # Find event connection
            event_id = record.get("event")
            event_code = event_code_map.get(event_id) if event_id else None
            
            # Process record
            doc = process_related_record(record, data_type, event_code, config.app_url)
            if doc:
                all_docs.append(doc)
                if event_code:
                    event_documents[event_code].append(doc)
        
        logger.info(f"Loaded {len(records)} {data_type} records")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("EVENT DATA SUMMARY:")
    logger.info("=" * 60)
    logger.info(f"Total documents: {len(all_docs)}")
    logger.info(f"Events with codes: {len(event_code_map)}")
    logger.info(f"\nDocuments by event code (top 10):")
    for code, docs in sorted(event_documents.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        logger.info(f"  {code}: {len(docs)} documents")
    logger.info("=" * 60)
    
    if not all_docs:
        logger.warning("No documents to index!")
        return
    
    # Split and index
    logger.info("\nSplitting documents...")
    docs_transformed = text_splitter.split_documents(all_docs)
    logger.info(f"Split into {len(docs_transformed)} chunks")
    
    # Clean metadata
    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""
        if "event_code" not in doc.metadata:
            doc.metadata["event_code"] = ""
    
    # Index
    logger.info("Indexing event documents...")
    indexing_stats = index(
        docs_transformed,
        record_manager,
        vectorstore,
        cleanup="incremental",
        source_id_key="source",
        force_update=(os.environ.get("FORCE_UPDATE") or "false").lower() == "true",
    )
    
    logger.info(f"Indexing complete! Stats: {indexing_stats}")
    
    # Final summary
    type_counts = defaultdict(int)
    for doc in all_docs:
        type_counts[doc.metadata.get("source_type", "unknown")] += 1
    
    logger.info("\n" + "=" * 60)
    logger.info("LIMITED EVENT INGESTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total documents: {len(all_docs)}")
    logger.info("\nDocuments by type:")
    for doc_type, count in type_counts.items():
        logger.info(f"  - {doc_type}: {count}")
    logger.info(f"\nTotal chunks indexed: {len(docs_transformed)}")
    logger.info("\n[READY] Event code filtering is now enabled!")
    logger.info("Example: Filter by event_code='SARLEAD' to find all data for that event")
    logger.info("=" * 60)
    
    return indexing_stats

async def fetch_records(loader, data_type: str, limit: int) -> List[Dict]:
    """Fetch records from Bubble"""
    import aiohttp
    
    headers = {
        "Authorization": f"Bearer {loader.config.api_token}"
    }
    
    url = f"{loader.base_url}/{data_type}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params={"limit": limit}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", {}).get("results", [])
                else:
                    logger.error(f"Error fetching {data_type}: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Error fetching {data_type}: {e}")
        return []

def process_event(event: Dict, app_url: str) -> Document:
    """Process event record"""
    content_parts = []
    
    name = event.get("name", "Unnamed Event")
    code = event.get("code", "")
    
    content_parts.append(f"# Event: {name}")
    if code:
        content_parts.append(f"## Event Code: {code}")
        content_parts.append(f"*Use code '{code}' to find all related data*")
    
    content_parts.append(f"\n## Status: {event.get('status', 'Unknown')}")
    
    if event.get("contactName"):
        content_parts.append(f"\n## Contact: {event['contactName']}")
    
    if event.get("bookingCount"):
        content_parts.append(f"\n## Bookings: {event['bookingCount']}")
    
    metadata = {
        "source": f"bubble://event/{event.get('_id')}",
        "source_type": "event",
        "event_code": code,
        "title": f"{name} ({code})" if code else name,
        "record_id": event.get("_id"),
        "status": event.get("status"),
        "created_date": event.get("Created Date"),
        "url": f"{app_url}/event/{event.get('_id')}"
    }
    
    return Document(
        page_content="\n".join(content_parts),
        metadata={k: v for k, v in metadata.items() if v is not None}
    )

def process_related_record(record: Dict, data_type: str, event_code: Optional[str], app_url: str) -> Document:
    """Process related records"""
    content_parts = []
    
    if data_type == "task":
        title = record.get("taskName", "Untitled Task")
        content_parts.append(f"# Task: {title}")
        if event_code:
            content_parts.append(f"\n## Event: {event_code}")
        content_parts.append(f"\n## Status: {record.get('status', 'Unknown')}")
        if record.get("description"):
            content_parts.append(f"\n## Description: {record['description']}")
            
    elif data_type == "comment":
        comment_text = record.get("Comment Text", "")[:200]
        content_parts.append(f"# Comment")
        if event_code:
            content_parts.append(f"\n## Event: {event_code}")
        content_parts.append(f"\n## Text: {comment_text}")
        
    elif data_type == "guest":
        name = f"{record.get('firstName', '')} {record.get('lastName', '')}".strip()
        content_parts.append(f"# Guest: {name}")
        if record.get("guestEvents"):
            content_parts.append(f"\n## Attending {len(record['guestEvents'])} events")
    
    else:
        content_parts.append(f"# {data_type.title()}")
        if event_code:
            content_parts.append(f"\n## Event: {event_code}")
    
    metadata = {
        "source": f"bubble://{data_type}/{record.get('_id')}",
        "source_type": f"{data_type}_event" if event_code else data_type,
        "event_code": event_code or "",
        "title": content_parts[0].replace("# ", ""),
        "record_id": record.get("_id"),
        "created_date": record.get("Created Date"),
        "url": f"{app_url}/{data_type}/{record.get('_id')}"
    }
    
    return Document(
        page_content="\n".join(content_parts),
        metadata={k: v for k, v in metadata.items() if v is not None}
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_events_limited())