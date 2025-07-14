"""Direct ingestion of Bubble venue/event data to Pinecone"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
import json

# Load environment
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BubbleVenueIngestion:
    """Ingest venue and event data from Bubble to Pinecone"""
    
    def __init__(self):
        self.api_token = os.getenv("BUBBLE_API_TOKEN")
        self.base_url = "https://app.bali.love/api/1.1/obj/"
        
        # Initialize embeddings with correct dimensions
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            dimensions=1024,
            chunk_size=200
        )
        
        self.vector_store = PineconeVectorStore(
            index_name=os.getenv("PINECONE_INDEX_NAME"),
            embedding=self.embeddings
        )
        
    async def fetch_bubble_data(self, datatype: str, limit: int = 100, cursor: int = 0) -> Dict[str, Any]:
        """Fetch data from Bubble API"""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        params = {"limit": limit, "cursor": cursor}
        
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.base_url}{datatype}"
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error fetching {datatype}: {response.status}")
                        return {}
            except Exception as e:
                logger.error(f"Error fetching {datatype}: {e}")
                return {}
    
    def process_event(self, event: Dict[str, Any]) -> Optional[Document]:
        """Process event data into document"""
        # Extract meaningful content
        content_parts = []
        
        # Basic info
        name = event.get("name", "")
        if name:
            content_parts.append(f"Event: {name}")
        
        # Event type and status
        event_type = event.get("eventType", "")
        if event_type:
            content_parts.append(f"Type: {event_type}")
            
        status = event.get("status", "")
        if status:
            content_parts.append(f"Status: {status}")
        
        # Contact info
        contact = event.get("contactName", "")
        if contact:
            content_parts.append(f"Contact: {contact}")
        
        # Wedding flag
        if event.get("isWedding"):
            content_parts.append("This is a wedding event")
        
        # Date
        creation_date = event.get("creationDate", "")
        if creation_date:
            content_parts.append(f"Created: {creation_date}")
        
        # Code for reference
        code = event.get("code", "")
        if code:
            content_parts.append(f"Reference Code: {code}")
        
        if not content_parts:
            return None
        
        content = "\n\n".join(content_parts)
        
        metadata = {
            "source": event.get("_id", ""),
            "source_type": "event",
            "name": name,
            "event_type": event_type,
            "status": status,
            "is_wedding": event.get("isWedding", False),
            "code": code,
            "created_date": creation_date,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return Document(page_content=content, metadata=metadata)
    
    def process_venue(self, venue: Dict[str, Any]) -> Optional[Document]:
        """Process venue data into document"""
        content_parts = []
        
        # Venue name
        name = venue.get("name", "")
        if name:
            content_parts.append(f"Venue: {name}")
        
        # Area/location
        area = venue.get("area", "")
        if area:
            content_parts.append(f"Area: {area}")
        
        # Capacity
        seats = venue.get("seats")
        if seats:
            content_parts.append(f"Capacity: {seats} seats")
        
        # Event types supported
        event_types = venue.get("eventTypes", [])
        if event_types:
            if isinstance(event_types, list):
                content_parts.append(f"Event Types: {', '.join(event_types)}")
            else:
                content_parts.append(f"Event Types: {event_types}")
        
        # Type of venue
        venue_type = venue.get("type", "")
        if venue_type:
            content_parts.append(f"Venue Type: {venue_type}")
        
        # Published status
        if venue.get("isPublish"):
            content_parts.append("Status: Published")
        
        # Short code
        short_code = venue.get("shortCode", "")
        if short_code:
            content_parts.append(f"Code: {short_code}")
        
        if not content_parts:
            return None
        
        content = "\n\n".join(content_parts)
        
        metadata = {
            "source": venue.get("_id", ""),
            "source_type": "venue",
            "name": name,
            "area": area,
            "capacity": seats,
            "venue_type": venue_type,
            "short_code": short_code,
            "is_published": venue.get("isPublish", False),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return Document(page_content=content, metadata=metadata)
    
    def process_product(self, product: Dict[str, Any]) -> Optional[Document]:
        """Process product/service data into document"""
        content_parts = []
        
        # Product name (might be in different fields)
        name = product.get("name") or product.get("creatorName") or ""
        if name:
            content_parts.append(f"Product/Service: {name}")
        
        # Description
        desc = product.get("description", "")
        if desc:
            content_parts.append(f"Description: {desc}")
        
        # Categories
        categories = product.get("categories", [])
        if categories:
            if isinstance(categories, list):
                content_parts.append(f"Categories: {', '.join(categories)}")
            else:
                content_parts.append(f"Categories: {categories}")
        
        # Event types
        event_types = product.get("eventTypes", [])
        if event_types:
            if isinstance(event_types, list):
                content_parts.append(f"Suitable for: {', '.join(event_types)}")
            else:
                content_parts.append(f"Suitable for: {event_types}")
        
        # Price model
        price_model = product.get("priceModel", "")
        if price_model:
            content_parts.append(f"Pricing: {price_model}")
        
        # Availability
        availability = product.get("availability", "")
        if availability:
            content_parts.append(f"Availability: {availability}")
        
        # Vendor info
        vendor_name = product.get("vendorTradingName", "")
        if vendor_name:
            content_parts.append(f"Vendor: {vendor_name}")
        
        if not content_parts:
            return None
        
        content = "\n\n".join(content_parts)
        
        metadata = {
            "source": product.get("_id", ""),
            "source_type": "product",
            "name": name,
            "price_model": price_model,
            "vendor": vendor_name,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return Document(page_content=content, metadata=metadata)
    
    def process_vendor(self, vendor: Dict[str, Any]) -> Optional[Document]:
        """Process vendor data into document"""
        content_parts = []
        
        # Company name
        name = vendor.get("companyName", "")
        if name:
            content_parts.append(f"Vendor: {name}")
        
        # Categories
        categories = vendor.get("categories", [])
        if categories:
            if isinstance(categories, list):
                content_parts.append(f"Services: {', '.join(categories)}")
            else:
                content_parts.append(f"Services: {categories}")
        
        # Event types
        event_types = vendor.get("eventTypes", [])
        if event_types:
            if isinstance(event_types, list):
                content_parts.append(f"Event Types: {', '.join(event_types)}")
            else:
                content_parts.append(f"Event Types: {event_types}")
        
        # Preferred vendor
        if vendor.get("IsPreferred"):
            content_parts.append("Preferred Vendor")
        
        # Preference index
        pref_index = vendor.get("preferenceIndex")
        if pref_index:
            content_parts.append(f"Preference Level: {pref_index}")
        
        if not content_parts:
            return None
        
        content = "\n\n".join(content_parts)
        
        metadata = {
            "source": vendor.get("_id", ""),
            "source_type": "vendor",
            "name": name,
            "is_preferred": vendor.get("IsPreferred", False),
            "preference_index": pref_index,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        return Document(page_content=content, metadata=metadata)
    
    async def ingest_data_type(self, datatype: str, processor_func) -> int:
        """Ingest a specific data type"""
        logger.info(f"Ingesting {datatype}...")
        
        cursor = 0
        total_processed = 0
        documents = []
        
        while True:
            data = await self.fetch_bubble_data(datatype, limit=100, cursor=cursor)
            
            if not data or "response" not in data:
                break
            
            response = data["response"]
            results = response.get("results", [])
            
            if not results:
                break
            
            # Process each record
            for record in results:
                doc = processor_func(record)
                if doc:
                    documents.append(doc)
            
            # Add to vector store in batches
            if len(documents) >= 50:
                try:
                    self.vector_store.add_documents(documents)
                    logger.info(f"  Added {len(documents)} {datatype} documents")
                    total_processed += len(documents)
                    documents = []
                except Exception as e:
                    logger.error(f"  Error adding documents: {e}")
            
            # Check if more records exist
            remaining = response.get("remaining", 0)
            if remaining == 0:
                break
            
            cursor += len(results)
        
        # Add remaining documents
        if documents:
            try:
                self.vector_store.add_documents(documents)
                total_processed += len(documents)
            except Exception as e:
                logger.error(f"  Error adding final documents: {e}")
        
        logger.info(f"  Total {datatype} processed: {total_processed}")
        return total_processed
    
    async def ingest_all(self):
        """Ingest all venue/event related data"""
        logger.info("=== Starting Bubble Data Ingestion ===")
        
        # Map data types to their processor functions
        ingestion_map = {
            "Event": self.process_event,
            "event": self.process_event,
            "Venue": self.process_venue,
            "venue": self.process_venue,
            "Product": self.process_product,
            "product": self.process_product,
            "Vendor": self.process_vendor
        }
        
        total_ingested = 0
        
        for datatype, processor in ingestion_map.items():
            count = await self.ingest_data_type(datatype, processor)
            total_ingested += count
        
        logger.info(f"\n=== Ingestion Complete ===")
        logger.info(f"Total documents ingested: {total_ingested}")
        
        return total_ingested
    
    async def test_queries(self):
        """Test some queries against the ingested data"""
        logger.info("\n=== Testing Queries ===")
        
        test_queries = [
            "Tell me about wedding venues",
            "What events are available?",
            "Show me venue options in Uluwatu",
            "What services do preferred vendors offer?",
            "Find venues with large capacity"
        ]
        
        for query in test_queries:
            logger.info(f"\nQuery: {query}")
            
            try:
                results = self.vector_store.similarity_search(
                    query,
                    k=3,
                    filter={"source_type": {"$in": ["venue", "event", "product", "vendor"]}}
                )
                
                if results:
                    for i, doc in enumerate(results, 1):
                        logger.info(f"  Result {i}:")
                        logger.info(f"    Type: {doc.metadata.get('source_type')}")
                        logger.info(f"    Name: {doc.metadata.get('name', 'N/A')}")
                        preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                        logger.info(f"    Content: {preview}")
                else:
                    logger.info("  No results found")
                    
            except Exception as e:
                logger.error(f"  Query error: {e}")


async def main():
    """Main function"""
    ingestion = BubbleVenueIngestion()
    
    # Ingest all data
    await ingestion.ingest_all()
    
    # Test with queries
    await ingestion.test_queries()


if __name__ == "__main__":
    asyncio.run(main())