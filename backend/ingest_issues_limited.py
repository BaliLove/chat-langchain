"""
Limited Issue Data Ingestion Script for Testing
Ingests a subset of issue data to test the pipeline
"""
import os
import logging
import json
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

# Limited version with smaller data volumes for testing
ISSUE_DATA_TYPES = [
    "issue",     # Core issues/tickets (limit to 50)
    "task",      # Tasks (limit to 50)
]

async def ingest_limited_issue_data():
    """Main function to ingest limited issue data for testing"""
    
    # Get configuration
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]
    
    logger.info("Starting limited issue data ingestion (testing)...")
    
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
    
    # Initialize basic loader
    loader = BubbleDataLoader(config, sync_manager)
    
    # Test connection
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    all_docs = []
    
    # Load issues (limited)
    logger.info("Loading issues (limited to 50)...")
    issue_docs = await fetch_and_process_data(loader, "issue", 50)
    all_docs.extend(issue_docs)
    logger.info(f"Loaded {len(issue_docs)} issue documents")
    
    # Load tasks (limited)
    logger.info("Loading tasks (limited to 50)...")
    task_docs = await fetch_and_process_data(loader, "task", 50)
    all_docs.extend(task_docs)
    logger.info(f"Loaded {len(task_docs)} task documents")
    
    logger.info(f"Total documents loaded: {len(all_docs)}")
    
    if not all_docs:
        logger.warning("No documents found!")
        return
    
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
    logger.info("Indexing issue documents...")
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
    for doc in all_docs:
        type_counts[doc.metadata.get("source_type", "unknown")] += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("LIMITED ISSUE DATA INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total issue documents loaded: {len(all_docs)}")
    logger.info("\\nDocuments by type:")
    for doc_type, count in type_counts.items():
        logger.info(f"  - {doc_type}: {count}")
    logger.info(f"\\nTotal chunks created: {len(docs_transformed)}")
    logger.info(f"Indexing results: {indexing_stats}")
    logger.info("=" * 60)
    
    return indexing_stats

async def fetch_and_process_data(loader, data_type: str, limit: int) -> List[Document]:
    """Fetch and process a limited amount of data"""
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
                    records = data.get("response", {}).get("results", [])
                    
                    documents = []
                    for record in records:
                        doc = process_record(record, data_type)
                        if doc:
                            documents.append(doc)
                    
                    return documents
                else:
                    logger.error(f"Error fetching {data_type}: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Error fetching {data_type}: {e}")
        return []

def process_record(record: Dict, data_type: str) -> Optional[Document]:
    """Process a record into a document"""
    try:
        if data_type == "issue":
            return process_issue(record)
        elif data_type == "task":
            return process_task(record)
        else:
            return None
    except Exception as e:
        logger.error(f"Error processing {data_type} record {record.get('_id')}: {e}")
        return None

def process_issue(record: Dict) -> Document:
    """Process issue/ticket"""
    content_parts = []
    
    # Title
    name = record.get("name", "Untitled Issue")
    content_parts.append(f"# Issue: {name}")
    
    # Code
    if record.get("code"):
        content_parts.append(f"\\nIssue Code: {record['code']}")
    
    # Status and Priority
    content_parts.append(f"\\n## Status & Priority")
    content_parts.append(f"- Status: {record.get('status', 'Unknown')}")
    content_parts.append(f"- Priority: {record.get('priority', 'Unknown')}")
    
    # Description
    if record.get("description"):
        content_parts.append(f"\\n## Description")
        content_parts.append(record["description"])
    
    # Create metadata
    metadata = {
        "source": f"bubble://issue/{record.get('_id')}",
        "source_type": "issue",
        "title": name,
        "record_id": record.get("_id"),
        "status": record.get("status", "Unknown"),
        "priority": record.get("priority", "Unknown"),
        "created_date": record.get("Created Date"),
        "modified_date": record.get("Modified Date"),
    }
    
    return Document(
        page_content="\\n".join(content_parts),
        metadata={k: v for k, v in metadata.items() if v is not None}
    )

def process_task(record: Dict) -> Document:
    """Process task"""
    content_parts = []
    
    # Title
    task_name = record.get("taskName", "Untitled Task")
    content_parts.append(f"# Task: {task_name}")
    
    # Code
    if record.get("taskCode"):
        content_parts.append(f"\\nTask Code: {record['taskCode']}")
    
    # Status
    content_parts.append(f"\\n## Status")
    content_parts.append(f"- Current: {record.get('status', 'Unknown')}")
    
    # Description
    if record.get("description"):
        content_parts.append(f"\\n## Description")
        content_parts.append(record["description"])
    
    # Due Date
    if record.get("dueDate"):
        content_parts.append(f"\\n## Due Date")
        content_parts.append(f"{record['dueDate']}")
    
    # Create metadata
    metadata = {
        "source": f"bubble://task/{record.get('_id')}",
        "source_type": "task",
        "title": task_name,
        "record_id": record.get("_id"),
        "status": record.get("status", "Unknown"),
        "due_date": record.get("dueDate"),
        "created_date": record.get("Created Date"),
        "modified_date": record.get("Modified Date"),
    }
    
    return Document(
        page_content="\\n".join(content_parts),
        metadata={k: v for k, v in metadata.items() if v is not None}
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_limited_issue_data())