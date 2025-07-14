"""Staged ingestion pipeline: API → Supabase → Vector DB"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import hashlib

from langchain_core.documents import Document
from backend.supabase_client import get_supabase_client
from backend.ingest_custom_data import CustomDataIngester

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StagedIngestionPipeline:
    """Pipeline that stages data in Supabase before vectorizing."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.ingester = CustomDataIngester()
        
    def create_staging_tables(self):
        """Create tables for staging raw data and tracking ingestion."""
        # This would typically be done via Supabase migrations
        # Here's the SQL for reference:
        """
        -- Raw data staging table
        CREATE TABLE IF NOT EXISTS raw_data_staging (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            source_id VARCHAR(255) UNIQUE NOT NULL,
            source_type VARCHAR(50) NOT NULL, -- 'api', 'manual', 'csv', etc.
            data_type VARCHAR(50) NOT NULL, -- 'venue', 'event', 'product', etc.
            raw_data JSONB NOT NULL,
            processed_data JSONB,
            content_hash VARCHAR(64),
            status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processed', 'failed'
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            processed_at TIMESTAMP WITH TIME ZONE
        );
        
        -- Vectorization tracking
        CREATE TABLE IF NOT EXISTS vector_sync_status (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            staging_id UUID REFERENCES raw_data_staging(id),
            vector_store_id VARCHAR(255),
            sync_status VARCHAR(20) DEFAULT 'pending',
            sync_error TEXT,
            synced_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create indexes
        CREATE INDEX idx_staging_source_id ON raw_data_staging(source_id);
        CREATE INDEX idx_staging_status ON raw_data_staging(status);
        CREATE INDEX idx_staging_data_type ON raw_data_staging(data_type);
        """
        logger.info("Staging tables should be created via Supabase migrations")
    
    async def stage_api_data(self, api_data: List[Dict[str, Any]], 
                            source_type: str = "api",
                            data_type: str = "venue") -> List[str]:
        """Stage raw API data in Supabase.
        
        Args:
            api_data: Raw data from API
            source_type: Where the data came from
            data_type: Type of data (venue, event, etc.)
            
        Returns:
            List of staging IDs
        """
        staging_ids = []
        
        for item in api_data:
            try:
                # Generate content hash to detect changes
                content_hash = self._generate_content_hash(item)
                
                # Check if already exists
                existing = self.supabase.table("raw_data_staging").select("*").eq(
                    "source_id", item.get("id", "")
                ).execute()
                
                if existing.data and len(existing.data) > 0:
                    # Update if content changed
                    if existing.data[0].get("content_hash") != content_hash:
                        result = self.supabase.table("raw_data_staging").update({
                            "raw_data": item,
                            "content_hash": content_hash,
                            "status": "pending",
                            "updated_at": datetime.now().isoformat()
                        }).eq("source_id", item.get("id")).execute()
                        
                        staging_ids.append(existing.data[0]["id"])
                        logger.info(f"Updated staging data for {item.get('id')}")
                else:
                    # Insert new
                    result = self.supabase.table("raw_data_staging").insert({
                        "source_id": item.get("id", ""),
                        "source_type": source_type,
                        "data_type": data_type,
                        "raw_data": item,
                        "content_hash": content_hash,
                        "status": "pending"
                    }).execute()
                    
                    if result.data:
                        staging_ids.append(result.data[0]["id"])
                        logger.info(f"Staged new data for {item.get('id')}")
                        
            except Exception as e:
                logger.error(f"Error staging item {item.get('id')}: {e}")
                continue
        
        return staging_ids
    
    async def process_staged_data(self, data_type: str = None, 
                                 status: str = "pending",
                                 limit: int = 100):
        """Process staged data and prepare for vectorization.
        
        Args:
            data_type: Filter by data type
            status: Filter by status
            limit: Maximum records to process
        """
        # Query staged data
        query = self.supabase.table("raw_data_staging").select("*").eq("status", status)
        
        if data_type:
            query = query.eq("data_type", data_type)
            
        result = query.limit(limit).execute()
        
        if not result.data:
            logger.info("No pending data to process")
            return
        
        for record in result.data:
            try:
                # Process based on data type
                processed = self._process_record(record)
                
                # Update with processed data
                self.supabase.table("raw_data_staging").update({
                    "processed_data": processed,
                    "status": "processed",
                    "processed_at": datetime.now().isoformat()
                }).eq("id", record["id"]).execute()
                
                logger.info(f"Processed staging record {record['id']}")
                
            except Exception as e:
                # Mark as failed
                self.supabase.table("raw_data_staging").update({
                    "status": "failed",
                    "error_message": str(e)
                }).eq("id", record["id"]).execute()
                
                logger.error(f"Failed to process {record['id']}: {e}")
    
    async def sync_to_vector_store(self, batch_size: int = 50):
        """Sync processed data to vector store."""
        # Get processed records not yet synced
        result = self.supabase.table("raw_data_staging").select(
            "*, vector_sync_status!left(sync_status)"
        ).eq("status", "processed").is_("vector_sync_status.sync_status", "null").limit(batch_size).execute()
        
        if not result.data:
            logger.info("No data to sync to vector store")
            return
        
        # Convert to documents
        documents = []
        staging_map = {}  # Map documents to staging IDs
        
        for record in result.data:
            doc = self._create_document(record)
            documents.append(doc)
            staging_map[doc.metadata["source_id"]] = record["id"]
        
        # Ingest to vector store
        try:
            await self.ingester.ingest_documents(documents, batch_size=batch_size)
            
            # Track successful sync
            for doc in documents:
                self.supabase.table("vector_sync_status").insert({
                    "staging_id": staging_map[doc.metadata["source_id"]],
                    "vector_store_id": doc.metadata["source_id"],
                    "sync_status": "success",
                    "synced_at": datetime.now().isoformat()
                }).execute()
                
            logger.info(f"Synced {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error syncing to vector store: {e}")
            # Track failed sync
            for doc in documents:
                self.supabase.table("vector_sync_status").insert({
                    "staging_id": staging_map[doc.metadata["source_id"]],
                    "sync_status": "failed",
                    "sync_error": str(e)
                }).execute()
    
    def _generate_content_hash(self, data: Dict[str, Any]) -> str:
        """Generate hash of content to detect changes."""
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw data based on type."""
        raw_data = record["raw_data"]
        data_type = record["data_type"]
        
        if data_type == "venue":
            return self._process_venue(raw_data)
        elif data_type == "event":
            return self._process_event(raw_data)
        else:
            # Check if processed_data already exists (from custom processors)
            if "processed_data" in record and record["processed_data"]:
                return record["processed_data"]
            
            # Default processing
            return {
                "title": raw_data.get("name", raw_data.get("title", "")),
                "content": raw_data.get("description", ""),
                "metadata": {k: v for k, v in raw_data.items() 
                           if k not in ["name", "title", "description"]}
            }
    
    def _process_venue(self, venue: Dict[str, Any]) -> Dict[str, Any]:
        """Process venue-specific data."""
        # Build rich content from venue data
        content_parts = [
            venue.get("description", ""),
            f"Location: {venue.get('location', '')}",
            f"Category: {venue.get('category', '')}",
        ]
        
        if venue.get("amenities"):
            content_parts.append(f"Amenities: {', '.join(venue['amenities'])}")
        
        if venue.get("capacity"):
            content_parts.append(f"Capacity: {venue['capacity']} guests")
            
        return {
            "title": venue.get("name", ""),
            "content": "\n\n".join(filter(None, content_parts)),
            "metadata": {
                "category": venue.get("category"),
                "location": venue.get("location"),
                "price_range": venue.get("price_range"),
                "capacity": venue.get("capacity"),
                "amenities": venue.get("amenities", []),
                "tags": venue.get("tags", [])
            }
        }
    
    def _process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process event-specific data."""
        # Similar processing for events
        pass
    
    def _create_document(self, record: Dict[str, Any]) -> Document:
        """Create a LangChain document from processed record."""
        processed = record.get("processed_data", {})
        
        return Document(
            page_content=f"{processed.get('title', '')}\n\n{processed.get('content', '')}",
            metadata={
                "source_id": record["source_id"],
                "data_type": record["data_type"],
                "ingested_at": datetime.now().isoformat(),
                **processed.get("metadata", {})
            }
        )
    
    async def run_full_pipeline(self, api_data: List[Dict[str, Any]]):
        """Run the complete pipeline: API → Supabase → Vector DB."""
        logger.info("Starting full ingestion pipeline")
        
        # Stage 1: Store in Supabase
        staging_ids = await self.stage_api_data(api_data)
        logger.info(f"Staged {len(staging_ids)} records")
        
        # Stage 2: Process data
        await self.process_staged_data()
        
        # Stage 3: Sync to vector store
        await self.sync_to_vector_store()
        
        logger.info("Pipeline complete!")


# Example usage
async def main():
    pipeline = StagedIngestionPipeline()
    
    # Example API data
    api_data = [
        {
            "id": "venue-001",
            "name": "Sunset Beach Club",
            "description": "Beautiful beachfront venue",
            "location": "Uluwatu",
            "category": "beach-club",
            "amenities": ["pool", "restaurant", "bar"],
            "capacity": 200
        }
    ]
    
    await pipeline.run_full_pipeline(api_data)


if __name__ == "__main__":
    asyncio.run(main())