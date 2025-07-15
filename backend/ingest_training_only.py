"""
Quick script to ingest only training data from Bubble.io
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use the modern pinecone package
from pinecone import Pinecone
from langchain.indexes import SQLRecordManager, index
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore

from backend.embeddings import get_embeddings_model
from backend.training_loader import load_enhanced_training_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_training_data():
    """Ingest only training data from Bubble.io"""
    
    # Get configuration
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]
    
    logger.info("Starting training data ingestion...")
    
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
    
    # Load training data
    logger.info("Loading enhanced training data...")
    training_docs = load_enhanced_training_data()
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
        cleanup="incremental",  # Use incremental to avoid deleting other data
        source_id_key="source",
        force_update=(os.environ.get("FORCE_UPDATE") or "false").lower() == "true",
    )
    
    logger.info(f"Indexing complete! Stats: {indexing_stats}")
    
    # Get index stats
    stats = index_obj.describe_index_stats()
    logger.info(f"Pinecone index stats: {stats}")
    
    # Summary
    logger.info("=" * 60)
    logger.info("TRAINING DATA INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Training documents loaded: {len(training_docs)}")
    logger.info(f"Chunks created: {len(docs_transformed)}")
    logger.info(f"Indexing results: {indexing_stats}")
    logger.info("=" * 60)
    
    return indexing_stats


if __name__ == "__main__":
    ingest_training_data()