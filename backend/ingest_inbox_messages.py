"""
Ingest inbox messages (InboxConversation and InboxConversationUser) into the vector database.
Messages are communications between clients, vendors, and internal team members.
All messages are public for the Bali Love team.
"""

import os
import logging
from typing import List, Dict, Any
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

# Configuration
RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]

def create_inbox_documents(loader: BubbleDataLoader) -> List[Document]:
    """Create documents from inbox messages."""
    documents = []
    
    # Load reference data for relationships
    logger.info("Loading reference data for relationships...")
    
    # Cache users
    users = {}
    try:
        user_data = loader.load_data("user", limit=1000, fields=["_id", "Name", "email"])
        for user in user_data:
            users[user.get("_id")] = {
                "name": user.get("Name", ""),
                "email": user.get("email", "")
            }
        logger.info(f"Cached {len(users)} users")
    except Exception as e:
        logger.warning(f"Could not load user data: {e}")
    
    # Cache events
    events = {}
    try:
        event_data = loader.load_data("event", limit=1000, fields=["_id", "Event Code", "Event Name"])
        for event in event_data:
            events[event.get("_id")] = {
                "code": event.get("Event Code", ""),
                "name": event.get("Event Name", "")
            }
        logger.info(f"Cached {len(events)} events")
    except Exception as e:
        logger.warning(f"Could not load event data: {e}")
    
    # Load InboxConversation data
    logger.info("Loading InboxConversation data...")
    try:
        conversations = loader.load_data("InboxConversation", limit=1000)
        logger.info(f"Loaded {len(conversations)} conversations")
        
        for conv in conversations:
            conv_id = conv.get("_id", "")
            
            # Extract user information
            assignee_id = conv.get("Assignee", "")
            assignee_info = users.get(assignee_id, {})
            assignee_name = assignee_info.get("name", "Unknown")
            
            created_by_id = conv.get("Created By", "")
            creator_info = users.get(created_by_id, {})
            creator_name = creator_info.get("name", "Unknown")
            
            # Extract event information
            event_id = conv.get("event", "")
            event_info = events.get(event_id, {})
            event_code = event_info.get("code", "")
            event_name = event_info.get("name", "")
            
            # Build content
            content_parts = []
            
            subject = conv.get("Subject", "").strip()
            if subject:
                content_parts.append(f"Subject: {subject}")
            
            last_message = conv.get("Last Message", "").strip()
            if last_message:
                content_parts.append(f"Last Message: {last_message}")
            
            status = conv.get("Status", "").strip()
            if status:
                content_parts.append(f"Status: {status}")
            
            if assignee_name and assignee_name != "Unknown":
                content_parts.append(f"Assignee: {assignee_name}")
            
            if creator_name and creator_name != "Unknown":
                content_parts.append(f"Created By: {creator_name}")
            
            if event_code:
                content_parts.append(f"Event Code: {event_code}")
            if event_name:
                content_parts.append(f"Event: {event_name}")
            
            # Create document
            content = "\n".join(content_parts) if content_parts else "Inbox conversation"
            
            metadata = {
                "source": f"bubble://InboxConversation/{conv_id}",
                "source_type": "inbox_conversation",
                "title": subject if subject else "Inbox Conversation",
                "is_public": True,  # All messages are public for Bali Love team
                "status": status if status else "active",
                "created_date": conv.get("Created Date", ""),
                "modified_date": conv.get("Modified Date", "")
            }
            
            # Add event code if available
            if event_code:
                metadata["event_code"] = event_code
                metadata["event_name"] = event_name
            
            # Add user info
            if assignee_name != "Unknown":
                metadata["assignee"] = assignee_name
            if creator_name != "Unknown":
                metadata["creator"] = creator_name
            
            documents.append(Document(page_content=content, metadata=metadata))
            
    except Exception as e:
        logger.error(f"Error loading InboxConversation data: {e}")
    
    # Load InboxConversationUser data
    logger.info("Loading InboxConversationUser data...")
    try:
        conv_users = loader.load_data("InboxConversationUser", limit=1000)
        logger.info(f"Loaded {len(conv_users)} conversation user records")
        
        for conv_user in conv_users:
            conv_user_id = conv_user.get("_id", "")
            
            # Extract user information
            user_id = conv_user.get("User(o)", "")
            user_info = users.get(user_id, {})
            user_name = user_info.get("name", "Unknown")
            user_email = user_info.get("email", "")
            
            # Extract conversation reference
            conversation_id = conv_user.get("Conversation", "")
            
            # Build content
            content_parts = []
            
            destination = conv_user.get("Destination", "").strip()
            if destination:
                content_parts.append(f"Destination: {destination}")
            
            if user_name and user_name != "Unknown":
                content_parts.append(f"User: {user_name}")
            
            if user_email:
                content_parts.append(f"Email: {user_email}")
            
            no_reply_needed = conv_user.get("noReplyNeeded?", False)
            if no_reply_needed:
                content_parts.append("No reply needed")
            
            last_message_date = conv_user.get("lastMessageDate", "")
            if last_message_date:
                content_parts.append(f"Last message: {last_message_date}")
            
            # Create document
            content = "\n".join(content_parts) if content_parts else "Inbox user record"
            
            metadata = {
                "source": f"bubble://InboxConversationUser/{conv_user_id}",
                "source_type": "inbox_conversation_user",
                "title": f"Inbox User: {user_name}" if user_name != "Unknown" else "Inbox User Record",
                "is_public": True,  # All messages are public for Bali Love team
                "no_reply_needed": no_reply_needed,
                "created_date": conv_user.get("Created Date", ""),
                "modified_date": conv_user.get("Modified Date", "")
            }
            
            # Add user info
            if user_name != "Unknown":
                metadata["user_name"] = user_name
            if user_email:
                metadata["user_email"] = user_email
            if conversation_id:
                metadata["conversation_id"] = conversation_id
            
            documents.append(Document(page_content=content, metadata=metadata))
            
    except Exception as e:
        logger.error(f"Error loading InboxConversationUser data: {e}")
    
    return documents


def main():
    """Main ingestion function."""
    logger.info("Starting inbox message ingestion...")
    logger.info("This will index client, vendor, and team communications")
    
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
    
    # Create documents
    logger.info("Loading inbox messages...")
    documents = create_inbox_documents(loader)
    logger.info(f"Loaded {len(documents)} inbox message documents")
    
    if not documents:
        logger.warning("No inbox messages found to index")
        return
    
    # Get infrastructure
    embeddings = get_embeddings_model()
    
    # Initialize Pinecone
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index_name = os.environ.get("PINECONE_INDEX_NAME", "chat-langchain")
    
    # Get vector store
    vector_store = PineconeVectorStore(
        index=pc.Index(index_name),
        embedding=embeddings,
        text_key="text",
        namespace=""
    )
    
    # Get record manager
    record_manager = SQLRecordManager(
        "pinecone/bubble_data",
        db_url=os.environ["RECORD_MANAGER_DB_URL"],
    )
    record_manager.create_schema()
    
    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(documents)
    logger.info(f"Split into {len(split_docs)} chunks")
    
    # Index documents
    logger.info("Indexing inbox message documents...")
    result = index(split_docs, record_manager, vector_store, cleanup="incremental", source_id_key="source")
    logger.info(f"Indexing complete! Stats: {result}")
    
    # Verify
    stats = pc.Index(index_name).describe_index_stats()
    logger.info(f"Pinecone index stats: {stats}")
    
    # Summary
    logger.info("=" * 60)
    logger.info("INBOX MESSAGE INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total inbox documents loaded: {len(documents)}")
    
    # Count by type
    type_counts = {}
    for doc in documents:
        doc_type = doc.metadata.get("source_type", "unknown")
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
    
    logger.info("\nDocuments by type:")
    for doc_type, count in sorted(type_counts.items()):
        logger.info(f"  - {doc_type}: {count}")
    
    logger.info(f"\nTotal chunks created: {len(split_docs)}")
    logger.info(f"Indexing results: {result}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()