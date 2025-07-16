"""
Complete Training Data Ingestion Script
Ingests all training-related data from Bubble.io with relationship resolution
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


class ComprehensiveTrainingLoader(BubbleDataLoader):
    """Enhanced loader for all training-related data with relationship resolution"""
    
    # Training data types to ingest (using lowercase based on API discovery)
    TRAINING_DATA_TYPES = [
        "training",              # Core training modules
        "trainingsession",       # Individual sessions
        "trainingplan",          # Employee training plans
        "trainingqualification", # Qualification definitions
    ]
    
    def __init__(self, config: BubbleConfig, sync_manager: BubbleSyncManager):
        super().__init__(config, sync_manager)
        # Cache for relationship lookups
        self.training_modules_cache = {}
        self.users_cache = {}
        self.qualifications_cache = {}
        
    async def load_all_training_data(self) -> List[Document]:
        """Load all training data with relationship resolution"""
        all_documents = []
        
        logger.info("Starting comprehensive training data ingestion...")
        
        # First, load reference data for relationships
        await self._load_reference_data()
        
        # Then load each data type
        for data_type in self.TRAINING_DATA_TYPES:
            logger.info(f"Loading {data_type} data...")
            documents = await self._load_training_data_type(data_type)
            all_documents.extend(documents)
            logger.info(f"Loaded {len(documents)} documents from {data_type}")
        
        logger.info(f"Total training documents loaded: {len(all_documents)}")
        return all_documents
    
    async def _load_reference_data(self):
        """Pre-load data needed for relationship resolution"""
        logger.info("Loading reference data for relationships...")
        
        # Load all training modules for reference
        modules = await self._fetch_all_records("training")
        for module in modules:
            self.training_modules_cache[module.get("_id")] = {
                "title": module.get("title", "Unknown Module"),
                "qualifications": module.get("qualifications", []),
                "qualifiedToTrain": module.get("qualifiedToTrain", [])
            }
        logger.info(f"Cached {len(self.training_modules_cache)} training modules")
        
        # Load qualifications
        quals = await self._fetch_all_records("trainingqualification")
        for qual in quals:
            self.qualifications_cache[qual.get("_id")] = qual.get("name", "Unknown Qualification")
        logger.info(f"Cached {len(self.qualifications_cache)} qualifications")
        
        # Load basic user info if available
        try:
            users = await self._fetch_all_records("user", limit=100)  # Limit for performance
            for user in users:
                self.users_cache[user.get("_id")] = {
                    "name": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or user.get("email", "Unknown User"),
                    "email": user.get("email", "")
                }
            logger.info(f"Cached {len(self.users_cache)} users")
        except:
            logger.warning("Could not load user data for reference")
    
    async def _fetch_all_records(self, data_type: str, limit: int = 1000) -> List[Dict]:
        """Fetch all records of a given type"""
        all_records = []
        cursor = 0
        
        while cursor < limit:
            records = await self.fetch_training_data_from_bubble(
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
    
    async def _load_training_data_type(self, data_type: str) -> List[Document]:
        """Load and process a specific training data type"""
        documents = []
        records = await self._fetch_all_records(data_type)
        
        for record in records:
            doc = self._process_training_record(record, data_type)
            if doc:
                documents.append(doc)
        
        return documents
    
    def _process_training_record(self, record: Dict, data_type: str) -> Optional[Document]:
        """Process a training record into a document with enriched content"""
        try:
            if data_type == "training":
                return self._process_training_module(record)
            elif data_type == "trainingsession":
                return self._process_training_session(record)
            elif data_type == "trainingplan":
                return self._process_training_plan(record)
            elif data_type == "trainingqualification":
                return self._process_training_qualification(record)
            else:
                return None
        except Exception as e:
            logger.error(f"Error processing {data_type} record {record.get('_id')}: {e}")
            return None
    
    def _process_training_module(self, record: Dict) -> Document:
        """Process training module with enhanced metadata"""
        # Parse content if it's JSON
        content_parts = []
        
        # Title
        title = record.get("title", "Untitled Training")
        content_parts.append(f"# {title}")
        
        # Parse structured content
        if record.get("content"):
            try:
                content_data = json.loads(record["content"]) if isinstance(record["content"], str) else record["content"]
                if content_data.get("blocks"):
                    content_parts.append("\n## Content")
                    for block in content_data["blocks"]:
                        if block.get("type") == "paragraph" and block.get("data", {}).get("text"):
                            text = block["data"]["text"].strip()
                            if text:
                                content_parts.append(text)
            except:
                # Fallback to raw content
                content_parts.append(str(record.get("content", "")))
        
        # Add qualifications
        if record.get("qualifications"):
            content_parts.append("\n## Required Qualifications")
            for qual_id in record["qualifications"]:
                qual_name = self.qualifications_cache.get(qual_id, qual_id)
                content_parts.append(f"- {qual_name}")
        
        # Add responsibilities
        if record.get("responsibilities"):
            content_parts.append("\n## Key Responsibilities")
            for resp_id in record["responsibilities"]:
                content_parts.append(f"- Responsibility ID: {resp_id}")
        
        # Add qualified trainers
        if record.get("qualifiedToTrain"):
            content_parts.append("\n## Qualified Trainers")
            for trainer_id in record["qualifiedToTrain"]:
                trainer_info = self.users_cache.get(trainer_id, {"name": trainer_id})
                content_parts.append(f"- {trainer_info.get('name', trainer_id)}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://training/{record.get('_id')}",
            "source_type": "training_module",
            "title": title,
            "record_id": record.get("_id"),
            "is_archived": record.get("isArchive", False),
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
            "has_sessions": bool(record.get("trainingSessions")),
            "session_count": len(record.get("trainingSessions", [])),
            "qualification_count": len(record.get("qualifications", [])),
            "trainer_count": len(record.get("qualifiedToTrain", [])),
            "url": f"{self.config.app_url}/training/{record.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_training_session(self, record: Dict) -> Document:
        """Process training session with trainee and module information"""
        content_parts = []
        
        # Get module information
        module_id = record.get("trainingModule")
        module_info = self.training_modules_cache.get(module_id, {})
        module_title = module_info.get("title", "Unknown Module")
        
        content_parts.append(f"# Training Session: {module_title}")
        content_parts.append(f"\nSession ID: {record.get('_id')}")
        
        # Add session details
        if record.get("calendarEvent"):
            content_parts.append(f"\n## Schedule")
            content_parts.append(f"Calendar Event: {record['calendarEvent']}")
        
        # Add trainees
        if record.get("trainees"):
            content_parts.append(f"\n## Trainees ({len(record['trainees'])})")
            for trainee_id in record["trainees"]:
                trainee_info = self.users_cache.get(trainee_id, {"name": f"User {trainee_id}"})
                content_parts.append(f"- {trainee_info.get('name')}")
        
        # Add trainers
        if record.get("trainers"):
            content_parts.append(f"\n## Trainers")
            for trainer_id in record["trainers"]:
                trainer_info = self.users_cache.get(trainer_id, {"name": f"Trainer {trainer_id}"})
                content_parts.append(f"- {trainer_info.get('name')}")
        
        # Add observers
        if record.get("observers"):
            content_parts.append(f"\n## Observers")
            for observer_id in record["observers"]:
                observer_info = self.users_cache.get(observer_id, {"name": f"Observer {observer_id}"})
                content_parts.append(f"- {observer_info.get('name')}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://trainingsession/{record.get('_id')}",
            "source_type": "training_session",
            "title": f"Session: {module_title}",
            "record_id": record.get("_id"),
            "module_id": module_id,
            "module_title": module_title,
            "trainee_count": len(record.get("trainees", [])),
            "trainer_count": len(record.get("trainers", [])),
            "observer_count": len(record.get("observers", [])),
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
            "url": f"{self.config.app_url}/trainingsession/{record.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_training_plan(self, record: Dict) -> Document:
        """Process training plan with trainee information"""
        content_parts = []
        
        # Get trainee information
        trainee_id = record.get("trainee")
        trainee_info = self.users_cache.get(trainee_id, {"name": f"Trainee {trainee_id}"})
        trainee_name = trainee_info.get("name")
        
        content_parts.append(f"# Training Plan for {trainee_name}")
        
        # Add plan details
        if record.get("goalCompletionDate"):
            content_parts.append(f"\n## Goal Completion Date")
            content_parts.append(f"{record['goalCompletionDate']}")
        
        # Add creation info
        content_parts.append(f"\n## Plan Details")
        content_parts.append(f"- Created: {record.get('Created Date', 'Unknown')}")
        content_parts.append(f"- Last Modified: {record.get('Modified Date', 'Unknown')}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://trainingplan/{record.get('_id')}",
            "source_type": "training_plan",
            "title": f"Training Plan: {trainee_name}",
            "record_id": record.get("_id"),
            "trainee_id": trainee_id,
            "trainee_name": trainee_name,
            "goal_completion_date": record.get("goalCompletionDate"),
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
            "url": f"{self.config.app_url}/trainingplan/{record.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_training_qualification(self, record: Dict) -> Document:
        """Process training qualification"""
        content_parts = []
        
        name = record.get("name", "Unnamed Qualification")
        content_parts.append(f"# Training Qualification: {name}")
        
        if record.get("order") is not None:
            content_parts.append(f"\n## Order/Priority: {record['order']}")
        
        # Find modules that require this qualification
        modules_requiring = []
        for module_id, module_info in self.training_modules_cache.items():
            if record.get("_id") in module_info.get("qualifications", []):
                modules_requiring.append(module_info.get("title"))
        
        if modules_requiring:
            content_parts.append(f"\n## Required For Training Modules")
            for module_title in modules_requiring:
                content_parts.append(f"- {module_title}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://trainingqualification/{record.get('_id')}",
            "source_type": "training_qualification",
            "title": name,
            "record_id": record.get("_id"),
            "order": record.get("order"),
            "required_by_modules": len(modules_requiring),
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
            "url": f"{self.config.app_url}/trainingqualification/{record.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    async def fetch_training_data_from_bubble(self, data_type: str, 
                                            limit: int = 100, 
                                            cursor: int = 0) -> List[Dict[str, Any]]:
        """Fetch training data from Bubble API"""
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


async def ingest_all_training_data():
    """Main function to ingest all training data"""
    
    # Get configuration
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]
    
    logger.info("Starting comprehensive training data ingestion...")
    
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
    
    # Initialize comprehensive loader
    loader = ComprehensiveTrainingLoader(config, sync_manager)
    
    # Test connection
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    # Load all training data
    training_docs = await loader.load_all_training_data()
    logger.info(f"Loaded {len(training_docs)} training documents")
    
    if not training_docs:
        logger.warning("No training documents found!")
        return
    
    # Split documents if needed
    logger.info("Splitting documents...")
    docs_transformed = text_splitter.split_documents(training_docs)
    logger.info(f"Split into {len(docs_transformed)} chunks")
    
    # Ensure metadata is clean
    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""
    
    # Index documents
    logger.info("Indexing training documents...")
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
    for doc in training_docs:
        type_counts[doc.metadata.get("source_type", "unknown")] += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("COMPREHENSIVE TRAINING DATA INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total training documents loaded: {len(training_docs)}")
    logger.info("\nDocuments by type:")
    for doc_type, count in type_counts.items():
        logger.info(f"  - {doc_type}: {count}")
    logger.info(f"\nTotal chunks created: {len(docs_transformed)}")
    logger.info(f"Indexing results: {indexing_stats}")
    logger.info("=" * 60)
    
    # Update sync state
    sync_time = datetime.now()
    for data_type in ComprehensiveTrainingLoader.TRAINING_DATA_TYPES:
        sync_manager.update_sync_time(data_type, sync_time, type_counts.get(data_type, 0))
    
    return indexing_stats


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_all_training_data())