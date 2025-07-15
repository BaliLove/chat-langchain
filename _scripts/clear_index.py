"""Clear Pinecone index."""
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from pinecone import Pinecone
from langchain.indexes import SQLRecordManager, index
from langchain_pinecone import PineconeVectorStore
from backend.embeddings import get_embeddings_model

logger = logging.getLogger(__name__)

PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]


def clear():
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_obj = pc.Index(PINECONE_INDEX_NAME)
    
    # Create vector store
    embedding = get_embeddings_model()
    vectorstore = PineconeVectorStore(index=index_obj, embedding=embedding)

    # Initialize record manager
    record_manager = SQLRecordManager(
        f"pinecone/{PINECONE_INDEX_NAME}", db_url=RECORD_MANAGER_DB_URL
    )
    record_manager.create_schema()

    # Clear the index by indexing empty list with full cleanup
    indexing_stats = index(
        [],
        record_manager,
        vectorstore,
        cleanup="full",
        source_id_key="source",
    )

    logger.info(f"Indexing stats: {indexing_stats}")
    
    # Get index stats
    stats = index_obj.describe_index_stats()
    logger.info(f"Pinecone index '{PINECONE_INDEX_NAME}' stats after clearing: {stats}")


if __name__ == "__main__":
    clear()