"""
Public Issue Data Ingestion Script
Ingests only public/non-private issues and tasks from Bubble.io
Excludes items with restricted readStatus to avoid privacy concerns
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

class PublicIssueLoader(BubbleDataLoader):
    """Loader for public issue data only - excludes private/restricted content"""
    
    ISSUE_DATA_TYPES = [
        "issue",     # Core issues/tickets
        "task",      # Tasks
    ]
    
    def __init__(self, config: BubbleConfig, sync_manager: BubbleSyncManager):
        super().__init__(config, sync_manager)
        self.users_cache = {}
        self.events_cache = {}
        self.privacy_stats = {
            "total_fetched": 0,
            "public_kept": 0,
            "private_filtered": 0
        }
    
    async def load_public_issue_data(self, limit_per_type: int = 200) -> List[Document]:
        """Load only public issue data with privacy filtering"""
        all_documents = []
        
        logger.info("Starting public issue data ingestion...")
        logger.info("Privacy filtering: Excluding items with restricted readStatus")
        
        # Load basic reference data
        await self._load_reference_data()
        
        # Load each data type with privacy filtering
        for data_type in self.ISSUE_DATA_TYPES:
            logger.info(f"Loading {data_type} data (public only)...")
            documents = await self._load_public_data_type(data_type, limit_per_type)
            all_documents.extend(documents)
            logger.info(f"Loaded {len(documents)} public {data_type} documents")
        
        # Log privacy statistics
        logger.info("=" * 50)
        logger.info("PRIVACY FILTERING STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total records fetched: {self.privacy_stats['total_fetched']}")
        logger.info(f"Public records kept: {self.privacy_stats['public_kept']}")
        logger.info(f"Private records filtered out: {self.privacy_stats['private_filtered']}")
        logger.info(f"Public ratio: {(self.privacy_stats['public_kept']/max(self.privacy_stats['total_fetched'], 1))*100:.1f}%")
        logger.info("=" * 50)
        
        logger.info(f"Total public issue documents loaded: {len(all_documents)}")
        return all_documents
    
    async def _load_reference_data(self):
        """Load minimal reference data for context"""
        logger.info("Loading reference data...")
        
        try:
            # Load some users for name resolution
            users = await self._fetch_records("user", limit=100)
            for user in users:
                self.users_cache[user.get("_id")] = {
                    "name": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or user.get("email", "Unknown User"),
                    "email": user.get("email", "")
                }
            logger.info(f"Cached {len(self.users_cache)} users")
        except:
            logger.warning("Could not load user data")
        
        try:
            # Load some events for task context
            events = await self._fetch_records("event", limit=50)
            for event in events:
                self.events_cache[event.get("_id")] = {
                    "name": event.get("name", "Unknown Event"),
                    "status": event.get("status", "")
                }
            logger.info(f"Cached {len(self.events_cache)} events")
        except:
            logger.warning("Could not load event data")
    
    async def _load_public_data_type(self, data_type: str, limit: int) -> List[Document]:
        """Load and filter data type for public content only"""
        documents = []
        records = await self._fetch_records(data_type, limit)
        
        self.privacy_stats["total_fetched"] += len(records)
        
        for record in records:
            if self._is_public_record(record, data_type):
                doc = self._process_public_record(record, data_type)
                if doc:
                    documents.append(doc)
                    self.privacy_stats["public_kept"] += 1
            else:
                self.privacy_stats["private_filtered"] += 1
                logger.debug(f"Filtered private {data_type}: {record.get('name', record.get('taskName', record.get('_id')))}")
        
        return documents
    
    def _is_public_record(self, record: Dict, data_type: str) -> bool:
        """
        Determine if a record should be considered public
        
        Privacy rules:
        1. If readStatus is empty/null -> Consider public
        2. If readStatus has many users (>5) -> Likely public
        3. If readStatus has few users (<=5) -> Likely private/restricted
        4. If archived -> Include (historical data)
        5. If status is 'Draft' or 'Private' -> Exclude
        """
        
        # Check for explicit privacy indicators in status
        status = record.get("status", "").lower()
        if any(word in status for word in ["private", "confidential", "draft", "internal"]):
            return False
        
        # Check readStatus field
        read_status = record.get("readStatus")
        
        if not read_status:
            # No readStatus means no restrictions
            return True
        
        if isinstance(read_status, list):
            # If many people can read it, it's likely public
            return len(read_status) > 5
        else:
            # Single person read status suggests private
            return False
    
    def _process_public_record(self, record: Dict, data_type: str) -> Optional[Document]:
        """Process a public record into a document"""
        try:
            if data_type == "issue":
                return self._process_public_issue(record)
            elif data_type == "task":
                return self._process_public_task(record)
            else:
                return None
        except Exception as e:
            logger.error(f"Error processing {data_type} record {record.get('_id')}: {e}")
            return None
    
    def _process_public_issue(self, record: Dict) -> Document:
        """Process public issue with sanitized content"""
        content_parts = []
        
        # Title
        name = record.get("name", "Untitled Issue")
        content_parts.append(f"# Issue: {name}")
        
        # Code (if not sensitive)
        code = record.get("code", "")
        if code and not any(word in code.lower() for word in ["confidential", "private", "internal"]):
            content_parts.append(f"\\nIssue Code: {code}")
        
        # Status and Priority
        content_parts.append(f"\\n## Status & Priority")
        content_parts.append(f"- Status: {record.get('status', 'Unknown')}")
        content_parts.append(f"- Priority: {record.get('priority', 'Unknown')}")
        
        # Description (sanitized)
        description = record.get("description", "")
        if description:
            # Basic sanitization - remove potentially sensitive info
            sanitized_desc = self._sanitize_content(description)
            if sanitized_desc:
                content_parts.append(f"\\n## Description")
                content_parts.append(sanitized_desc)
        
        # Lead (if public)
        if record.get("lead"):
            lead_info = self.users_cache.get(record["lead"], {})
            content_parts.append(f"\\n## Lead")
            content_parts.append(f"- {lead_info.get('name', 'Team Member')}")
        
        # Category
        if record.get("category"):
            content_parts.append(f"\\n## Category")
            content_parts.append(f"Category ID: {record['category']}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://issue/{record.get('_id')}",
            "source_type": "public_issue",
            "title": name,
            "record_id": record.get("_id"),
            "status": record.get("status", "Unknown"),
            "priority": record.get("priority", "Unknown"),
            "category": record.get("category"),
            "is_public": True,
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
        }
        
        return Document(
            page_content="\\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_public_task(self, record: Dict) -> Document:
        """Process public task with sanitized content"""
        content_parts = []
        
        # Title
        task_name = record.get("taskName", "Untitled Task")
        content_parts.append(f"# Task: {task_name}")
        
        # Code
        task_code = record.get("taskCode", "")
        if task_code and not any(word in task_code.lower() for word in ["confidential", "private", "internal"]):
            content_parts.append(f"\\nTask Code: {task_code}")
        
        # Status
        content_parts.append(f"\\n## Status")
        content_parts.append(f"- Current: {record.get('status', 'Unknown')}")
        if record.get("lastStatus"):
            content_parts.append(f"- Previous: {record['lastStatus']}")
        
        # Event context (if available and public)
        if record.get("event"):
            event_info = self.events_cache.get(record["event"], {})
            event_name = event_info.get("name", "")
            # Only include if event name doesn't seem private
            if event_name and not any(word in event_name.lower() for word in ["confidential", "private", "internal"]):
                content_parts.append(f"\\n## Event")
                content_parts.append(f"- {event_name}")
        
        # Description (sanitized)
        description = record.get("description", "")
        if description:
            sanitized_desc = self._sanitize_content(description)
            if sanitized_desc:
                content_parts.append(f"\\n## Description")
                content_parts.append(sanitized_desc)
        
        # Due Date
        if record.get("dueDate"):
            content_parts.append(f"\\n## Due Date")
            content_parts.append(f"{record['dueDate']}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://task/{record.get('_id')}",
            "source_type": "public_task",
            "title": task_name,
            "record_id": record.get("_id"),
            "status": record.get("status", "Unknown"),
            "event_id": record.get("event"),
            "is_public": True,
            "due_date": record.get("dueDate"),
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
        }
        
        return Document(
            page_content="\\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _sanitize_content(self, content: str) -> str:
        """
        Basic content sanitization to remove potentially sensitive information
        """
        if not content:
            return ""
        
        # Remove content that might be sensitive
        sensitive_patterns = [
            "password", "secret", "confidential", "private", 
            "internal only", "do not share", "restricted"
        ]
        
        content_lower = content.lower()
        if any(pattern in content_lower for pattern in sensitive_patterns):
            return "[Content filtered for privacy]"
        
        # Remove email addresses and phone numbers for privacy
        import re
        content = re.sub(r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b', '[email]', content)
        content = re.sub(r'\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b', '[phone]', content)
        
        return content.strip()
    
    async def _fetch_records(self, data_type: str, limit: int) -> List[Dict]:
        """Fetch records from Bubble API"""
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.config.api_token}"
        }
        
        url = f"{self.base_url}/{data_type}"
        
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


async def ingest_public_issues_only():
    """Main function to ingest public issue data only"""
    
    # Get configuration
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]
    
    logger.info("Starting PUBLIC-ONLY issue data ingestion...")
    logger.info("This will exclude private/restricted issues based on readStatus")
    
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
    
    # Initialize public issue loader
    loader = PublicIssueLoader(config, sync_manager)
    
    # Test connection
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    # Load public issue data (limit for initial testing)
    issue_docs = await loader.load_public_issue_data(limit_per_type=100)
    logger.info(f"Loaded {len(issue_docs)} public issue documents")
    
    if not issue_docs:
        logger.warning("No public issue documents found!")
        return
    
    # Split documents if needed
    logger.info("Splitting documents...")
    docs_transformed = text_splitter.split_documents(issue_docs)
    logger.info(f"Split into {len(docs_transformed)} chunks")
    
    # Ensure metadata is clean
    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""
    
    # Index documents
    logger.info("Indexing public issue documents...")
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
    for doc in issue_docs:
        type_counts[doc.metadata.get("source_type", "unknown")] += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("PUBLIC ISSUE DATA INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total public documents loaded: {len(issue_docs)}")
    logger.info("\\nDocuments by type:")
    for doc_type, count in type_counts.items():
        logger.info(f"  - {doc_type}: {count}")
    logger.info(f"\\nTotal chunks created: {len(docs_transformed)}")
    logger.info(f"Indexing results: {indexing_stats}")
    logger.info("\\nPrivacy: Only public issues included, private issues filtered out")
    logger.info("=" * 60)
    
    return indexing_stats


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_public_issues_only())