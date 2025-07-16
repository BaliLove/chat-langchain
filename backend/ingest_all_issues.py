"""
Complete Issue Data Ingestion Script
Ingests all issue-related data from Bubble.io including issues, tasks, and comments
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


class IssueDataLoader(BubbleDataLoader):
    """Enhanced loader for all issue-related data with relationship resolution"""
    
    # Issue data types to ingest (using lowercase based on API discovery)
    ISSUE_DATA_TYPES = [
        "issue",                 # Core issues/tickets
        "task",                  # Tasks (often related to issues)
        "comment",               # Comments on issues/tasks
        "commentthread",         # Comment threads linking to issues
    ]
    
    def __init__(self, config: BubbleConfig, sync_manager: BubbleSyncManager):
        super().__init__(config, sync_manager)
        # Cache for relationship lookups
        self.users_cache = {}
        self.categories_cache = {}
        self.teams_cache = {}
        self.events_cache = {}
        
    async def load_all_issue_data(self) -> List[Document]:
        """Load all issue data with relationship resolution"""
        all_documents = []
        
        logger.info("Starting comprehensive issue data ingestion...")
        
        # First, load reference data for relationships
        await self._load_reference_data()
        
        # Then load each data type
        for data_type in self.ISSUE_DATA_TYPES:
            logger.info(f"Loading {data_type} data...")
            documents = await self._load_issue_data_type(data_type)
            all_documents.extend(documents)
            logger.info(f"Loaded {len(documents)} documents from {data_type}")
        
        logger.info(f"Total issue documents loaded: {len(all_documents)}")
        return all_documents
    
    async def _load_reference_data(self):
        """Pre-load data needed for relationship resolution"""
        logger.info("Loading reference data for relationships...")
        
        # Load basic user info if available
        try:
            users = await self._fetch_all_records("user", limit=200)  # Increased limit for better coverage
            for user in users:
                self.users_cache[user.get("_id")] = {
                    "name": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or user.get("email", "Unknown User"),
                    "email": user.get("email", ""),
                    "role": user.get("role", "")
                }
            logger.info(f"Cached {len(self.users_cache)} users")
        except:
            logger.warning("Could not load user data for reference")
        
        # Try to load events for task context
        try:
            events = await self._fetch_all_records("event", limit=100)
            for event in events:
                self.events_cache[event.get("_id")] = {
                    "name": event.get("name", "Unknown Event"),
                    "status": event.get("status", ""),
                    "eventType": event.get("eventType", "")
                }
            logger.info(f"Cached {len(self.events_cache)} events")
        except:
            logger.warning("Could not load event data for reference")
    
    async def _fetch_all_records(self, data_type: str, limit: int = 1000) -> List[Dict]:
        """Fetch all records of a given type"""
        all_records = []
        cursor = 0
        
        while cursor < limit:
            records = await self.fetch_issue_data_from_bubble(
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
    
    async def _load_issue_data_type(self, data_type: str) -> List[Document]:
        """Load and process a specific issue data type"""
        documents = []
        records = await self._fetch_all_records(data_type)
        
        for record in records:
            doc = self._process_issue_record(record, data_type)
            if doc:
                documents.append(doc)
        
        return documents
    
    def _process_issue_record(self, record: Dict, data_type: str) -> Optional[Document]:
        """Process an issue record into a document with enriched content"""
        try:
            if data_type == "issue":
                return self._process_issue(record)
            elif data_type == "task":
                return self._process_task(record)
            elif data_type == "comment":
                return self._process_comment(record)
            elif data_type == "commentthread":
                return self._process_comment_thread(record)
            else:
                return None
        except Exception as e:
            logger.error(f"Error processing {data_type} record {record.get('_id')}: {e}")
            return None
    
    def _parse_editorjs_content(self, content_json: str) -> str:
        """Parse EditorJS JSON content into readable text"""
        try:
            content_data = json.loads(content_json) if isinstance(content_json, str) else content_json
            text_parts = []
            
            if content_data.get("blocks"):
                for block in content_data["blocks"]:
                    if block.get("type") == "paragraph" and block.get("data", {}).get("text"):
                        text = block["data"]["text"].strip()
                        if text:
                            text_parts.append(text)
            
            return "\n".join(text_parts)
        except:
            return ""
    
    def _clean_bbcode(self, text: str) -> str:
        """Remove BBCode formatting from text"""
        import re
        # Remove [font=...] tags
        text = re.sub(r'\[font="[^"]+"\]', '', text)
        text = re.sub(r'\[/font\]', '', text)
        # Remove other common BBCode
        text = re.sub(r'\[/?[^\]]+\]', '', text)
        return text.strip()
    
    def _process_issue(self, record: Dict) -> Document:
        """Process issue/ticket with enhanced metadata"""
        content_parts = []
        
        # Title
        name = record.get("name", "Untitled Issue")
        content_parts.append(f"# Issue: {name}")
        
        # Code
        if record.get("code"):
            content_parts.append(f"\nIssue Code: {record['code']}")
        
        # Status and Priority
        content_parts.append(f"\n## Status & Priority")
        content_parts.append(f"- Status: {record.get('status', 'Unknown')}")
        content_parts.append(f"- Priority: {record.get('priority', 'Unknown')}")
        if record.get("priorityNumber"):
            content_parts.append(f"- Priority Level: {record['priorityNumber']}")
        
        # Description
        if record.get("description"):
            content_parts.append(f"\n## Description")
            content_parts.append(record["description"])
        
        # Parse JSON description if available
        if record.get("descriptionJson"):
            parsed_desc = self._parse_editorjs_content(record["descriptionJson"])
            if parsed_desc and parsed_desc != record.get("description", ""):
                content_parts.append(f"\n## Additional Details")
                content_parts.append(parsed_desc)
        
        # Lead/Assignee
        if record.get("lead"):
            lead_info = self.users_cache.get(record["lead"], {})
            content_parts.append(f"\n## Lead")
            content_parts.append(f"- {lead_info.get('name', record['lead'])}")
        
        # Team
        if record.get("team"):
            content_parts.append(f"\n## Team Members")
            for team_member_id in record["team"]:
                member_info = self.users_cache.get(team_member_id, {})
                content_parts.append(f"- {member_info.get('name', team_member_id)}")
        
        # Estimated Done Date
        if record.get("estimatedDoneDate"):
            content_parts.append(f"\n## Estimated Completion")
            content_parts.append(f"{record['estimatedDoneDate']}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://issue/{record.get('_id')}",
            "source_type": "issue",
            "title": name,
            "record_id": record.get("_id"),
            "status": record.get("status", "Unknown"),
            "priority": record.get("priority", "Unknown"),
            "priority_number": record.get("priorityNumber"),
            "category": record.get("category"),
            "archived": record.get("archived", False),
            "lead_id": record.get("lead"),
            "lead_name": self.users_cache.get(record.get("lead"), {}).get("name") if record.get("lead") else None,
            "team_count": len(record.get("team", [])),
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
            "estimated_done_date": record.get("estimatedDoneDate"),
            "url": f"{self.config.app_url}/issue/{record.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_task(self, record: Dict) -> Document:
        """Process task with event and assignee information"""
        content_parts = []
        
        # Title
        task_name = record.get("taskName", "Untitled Task")
        content_parts.append(f"# Task: {task_name}")
        
        # Code
        if record.get("taskCode"):
            content_parts.append(f"\nTask Code: {record['taskCode']}")
        
        # Status
        content_parts.append(f"\n## Status")
        content_parts.append(f"- Current: {record.get('status', 'Unknown')}")
        if record.get("lastStatus"):
            content_parts.append(f"- Previous: {record['lastStatus']}")
        
        # Event context
        if record.get("event"):
            event_info = self.events_cache.get(record["event"], {})
            content_parts.append(f"\n## Event")
            content_parts.append(f"- {event_info.get('name', 'Unknown Event')}")
            if event_info.get("eventType"):
                content_parts.append(f"- Type: {event_info['eventType']}")
        
        # Assignee
        if record.get("assignee"):
            assignee_info = self.users_cache.get(record["assignee"], {})
            content_parts.append(f"\n## Assigned To")
            content_parts.append(f"- {assignee_info.get('name', record['assignee'])}")
        
        # Description
        if record.get("description"):
            content_parts.append(f"\n## Description")
            content_parts.append(record["description"])
        
        # Due Date
        if record.get("dueDate"):
            content_parts.append(f"\n## Due Date")
            content_parts.append(f"{record['dueDate']}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://task/{record.get('_id')}",
            "source_type": "task",
            "title": task_name,
            "record_id": record.get("_id"),
            "status": record.get("status", "Unknown"),
            "last_status": record.get("lastStatus"),
            "event_id": record.get("event"),
            "event_name": self.events_cache.get(record.get("event"), {}).get("name") if record.get("event") else None,
            "assignee_id": record.get("assignee"),
            "assignee_name": self.users_cache.get(record.get("assignee"), {}).get("name") if record.get("assignee") else None,
            "due_date": record.get("dueDate"),
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
            "archived": record.get("isArchived(outdated)", False),
            "url": f"{self.config.app_url}/task/{record.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_comment(self, record: Dict) -> Document:
        """Process comment with cleaned text"""
        content_parts = []
        
        # Clean comment text
        comment_text = self._clean_bbcode(record.get("Comment Text", ""))
        
        content_parts.append(f"# Comment")
        
        # Add comment details
        content_parts.append(f"\n## Content")
        content_parts.append(comment_text)
        
        # Created by
        if record.get("Created By"):
            creator_info = self.users_cache.get(record["Created By"], {})
            content_parts.append(f"\n## Author")
            content_parts.append(f"- {creator_info.get('name', 'Unknown Author')}")
        
        # Thread reference
        if record.get("Parent Comment Thread"):
            content_parts.append(f"\n## Part of Thread")
            content_parts.append(f"- Thread ID: {record['Parent Comment Thread']}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://comment/{record.get('_id')}",
            "source_type": "comment",
            "title": f"Comment: {comment_text[:50]}..." if len(comment_text) > 50 else f"Comment: {comment_text}",
            "record_id": record.get("_id"),
            "thread_id": record.get("Parent Comment Thread"),
            "author_id": record.get("Created By"),
            "author_name": self.users_cache.get(record.get("Created By"), {}).get("name") if record.get("Created By") else None,
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
            "url": f"{self.config.app_url}/comment/{record.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_comment_thread(self, record: Dict) -> Document:
        """Process comment thread with issue reference"""
        content_parts = []
        
        content_parts.append(f"# Comment Thread")
        
        # Item type
        if record.get("itemType "):
            content_parts.append(f"\n## Thread Type")
            content_parts.append(f"- Related to: {record['itemType ']}")
        
        # Issue reference
        if record.get("issue"):
            content_parts.append(f"\n## Related Issue")
            content_parts.append(f"- Issue ID: {record['issue']}")
        
        # Followed by
        if record.get("followedBy"):
            content_parts.append(f"\n## Followers ({len(record['followedBy'])})")
            for follower_id in record["followedBy"]:
                follower_info = self.users_cache.get(follower_id, {})
                content_parts.append(f"- {follower_info.get('name', follower_id)}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://commentthread/{record.get('_id')}",
            "source_type": "comment_thread",
            "title": f"Comment Thread on {record.get('itemType ', 'Unknown')}",
            "record_id": record.get("_id"),
            "item_type": record.get("itemType "),
            "issue_id": record.get("issue"),
            "follower_count": len(record.get("followedBy", [])),
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
            "url": f"{self.config.app_url}/commentthread/{record.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    async def fetch_issue_data_from_bubble(self, data_type: str, 
                                         limit: int = 100, 
                                         cursor: int = 0) -> List[Dict[str, Any]]:
        """Fetch issue data from Bubble API"""
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


async def ingest_all_issue_data():
    """Main function to ingest all issue data"""
    
    # Get configuration
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]
    
    logger.info("Starting comprehensive issue data ingestion...")
    
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
    
    # Initialize issue loader
    loader = IssueDataLoader(config, sync_manager)
    
    # Test connection
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    # Load all issue data
    issue_docs = await loader.load_all_issue_data()
    logger.info(f"Loaded {len(issue_docs)} issue documents")
    
    if not issue_docs:
        logger.warning("No issue documents found!")
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
    for doc in issue_docs:
        type_counts[doc.metadata.get("source_type", "unknown")] += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("COMPREHENSIVE ISSUE DATA INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total issue documents loaded: {len(issue_docs)}")
    logger.info("\nDocuments by type:")
    for doc_type, count in type_counts.items():
        logger.info(f"  - {doc_type}: {count}")
    logger.info(f"\nTotal chunks created: {len(docs_transformed)}")
    logger.info(f"Indexing results: {indexing_stats}")
    logger.info("=" * 60)
    
    # Update sync state
    sync_time = datetime.now()
    for data_type in IssueDataLoader.ISSUE_DATA_TYPES:
        sync_manager.update_sync_time(data_type, sync_time, type_counts.get(data_type, 0))
    
    return indexing_stats


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_all_issue_data())