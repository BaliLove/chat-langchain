"""Custom data ingestion script for your knowledge base."""

import asyncio
import os
from typing import List, Dict, Any
from datetime import datetime
import logging

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomDataIngester:
    """Ingest custom data into the vector store."""
    
    def __init__(self):
        """Initialize the ingester with necessary connections."""
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        )
        
        # Initialize vector store
        self.vector_store = PineconeVectorStore(
            index_name=os.getenv("PINECONE_INDEX_NAME", "chat-langchain"),
            embedding=self.embeddings,
            namespace=os.getenv("PINECONE_NAMESPACE", "custom-data")
        )
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # PostgreSQL connection for tracking
        self.pg_conn = self._get_postgres_connection()
    
    def _get_postgres_connection(self):
        """Get PostgreSQL connection."""
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "chat_langchain"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
    
    def create_documents_from_data(self, data: List[Dict[str, Any]]) -> List[Document]:
        """Create LangChain documents from custom data.
        
        Args:
            data: List of dictionaries containing your data
                  Expected format: {
                      "id": "unique-id",
                      "title": "Document Title",
                      "content": "Main content...",
                      "metadata": {
                          "category": "venue",
                          "location": "Uluwatu",
                          "tags": ["restaurant", "beach-view"],
                          ...
                      }
                  }
        
        Returns:
            List of Document objects ready for embedding
        """
        documents = []
        
        for item in data:
            # Combine title and content for better search
            full_content = f"{item.get('title', '')}\n\n{item.get('content', '')}"
            
            # Create metadata
            metadata = {
                "source_id": item.get("id"),
                "title": item.get("title", ""),
                "timestamp": datetime.now().isoformat(),
                **item.get("metadata", {})
            }
            
            # Create document
            doc = Document(
                page_content=full_content,
                metadata=metadata
            )
            documents.append(doc)
        
        return documents
    
    async def ingest_documents(self, documents: List[Document], batch_size: int = 100):
        """Ingest documents into the vector store.
        
        Args:
            documents: List of documents to ingest
            batch_size: Number of documents to process at once
        """
        # Split documents into chunks
        all_chunks = []
        for doc in documents:
            chunks = self.text_splitter.split_documents([doc])
            all_chunks.extend(chunks)
        
        logger.info(f"Split {len(documents)} documents into {len(all_chunks)} chunks")
        
        # Process in batches
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            
            try:
                # Add to vector store
                await self.vector_store.aadd_documents(batch)
                logger.info(f"Ingested batch {i//batch_size + 1} ({len(batch)} chunks)")
                
                # Track in PostgreSQL
                self._track_ingestion(batch)
                
            except Exception as e:
                logger.error(f"Error ingesting batch: {e}")
                continue
    
    def _track_ingestion(self, documents: List[Document]):
        """Track document ingestion in PostgreSQL."""
        try:
            with self.pg_conn.cursor() as cursor:
                for doc in documents:
                    cursor.execute("""
                        INSERT INTO document_tracking (
                            source_id,
                            title,
                            metadata,
                            ingested_at
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (source_id) DO UPDATE
                        SET metadata = %s, ingested_at = %s
                    """, (
                        doc.metadata.get("source_id"),
                        doc.metadata.get("title"),
                        str(doc.metadata),
                        datetime.now(),
                        str(doc.metadata),
                        datetime.now()
                    ))
                self.pg_conn.commit()
        except Exception as e:
            logger.error(f"Error tracking ingestion: {e}")
            self.pg_conn.rollback()
    
    def create_tracking_table(self):
        """Create the tracking table if it doesn't exist."""
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_tracking (
                        source_id VARCHAR(255) PRIMARY KEY,
                        title TEXT,
                        metadata TEXT,
                        ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                self.pg_conn.commit()
                logger.info("Created document tracking table")
        except Exception as e:
            logger.error(f"Error creating tracking table: {e}")
            self.pg_conn.rollback()


# Example usage
async def main():
    """Example of how to use the ingester."""
    
    # Initialize ingester
    ingester = CustomDataIngester()
    ingester.create_tracking_table()
    
    # Example data - replace with your actual data
    sample_data = [
        {
            "id": "venue-001",
            "title": "Sunset Beach Club Uluwatu",
            "content": """
            Located on the stunning cliffs of Uluwatu, Sunset Beach Club offers 
            breathtaking ocean views and world-class dining. The venue features:
            - Mediterranean and Asian fusion cuisine
            - Infinity pool overlooking the Indian Ocean
            - Private beach access via inclinator
            - Live DJ sessions during sunset
            - Capacity for 200 guests
            """,
            "metadata": {
                "category": "venue",
                "location": "Uluwatu",
                "type": "beach-club",
                "price_range": "high",
                "tags": ["restaurant", "beach", "sunset-view", "pool", "events"]
            }
        },
        {
            "id": "venue-002",
            "title": "The Edge Bali",
            "content": """
            The Edge Bali is a luxury cliff-top resort in Uluwatu featuring:
            - Award-winning architecture
            - Glass-bottom sky pool
            - Multiple dining venues including OneEighty° bar
            - Private villas with ocean views
            - Wedding and event facilities for up to 300 guests
            """,
            "metadata": {
                "category": "venue",
                "location": "Uluwatu",
                "type": "resort",
                "price_range": "luxury",
                "tags": ["hotel", "restaurant", "events", "wedding", "pool"]
            }
        }
    ]
    
    # Create documents
    documents = ingester.create_documents_from_data(sample_data)
    
    # Ingest documents
    await ingester.ingest_documents(documents)
    
    logger.info("Ingestion complete!")


if __name__ == "__main__":
    asyncio.run(main())