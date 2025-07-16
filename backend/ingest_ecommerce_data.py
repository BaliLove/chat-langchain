"""
E-commerce Data Ingestion Script
Ingests products, vendors, and venues from Bubble.io for the wedding/event platform
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


class EcommerceDataLoader(BubbleDataLoader):
    """Loader for e-commerce data - products, vendors, and venues"""
    
    # Core e-commerce data types (using lowercase based on API pattern)
    ECOMMERCE_DATA_TYPES = [
        "product",      # Products/services
        "vendor",       # Service providers
        "venue",        # Event venues
    ]
    
    # Related data types for enrichment
    RELATED_DATA_TYPES = [
        "productimage",
        "vendorimage",
        "venueimage",
        "productsatellite",
    ]
    
    def __init__(self, config: BubbleConfig, sync_manager: BubbleSyncManager):
        super().__init__(config, sync_manager)
        # Caches for relationship resolution
        self.vendors_cache = {}
        self.venues_cache = {}
        self.categories_cache = {}
        self.event_types_cache = {}
        self.images_cache = {}
        
    async def load_all_ecommerce_data(self, limit_per_type: int = 500) -> List[Document]:
        """Load all e-commerce data with relationship resolution"""
        all_documents = []
        
        logger.info("Starting e-commerce data ingestion...")
        logger.info("Loading products, vendors, and venues...")
        
        # First, load reference data for relationships
        await self._load_reference_data()
        
        # Then load each data type
        for data_type in self.ECOMMERCE_DATA_TYPES:
            logger.info(f"Loading {data_type} data...")
            documents = await self._load_ecommerce_data_type(data_type, limit_per_type)
            all_documents.extend(documents)
            logger.info(f"Loaded {len(documents)} {data_type} documents")
        
        logger.info(f"Total e-commerce documents loaded: {len(all_documents)}")
        return all_documents
    
    async def _load_reference_data(self):
        """Pre-load data needed for relationship resolution"""
        logger.info("Loading reference data for relationships...")
        
        # Load vendors for product references
        try:
            vendors = await self._fetch_all_records("vendor", limit=200)
            for vendor in vendors:
                self.vendors_cache[vendor.get("_id")] = {
                    "companyName": vendor.get("companyName", "Unknown Vendor"),
                    "tradingName": vendor.get("tradingName", ""),
                    "email": vendor.get("email", ""),
                    "categories": vendor.get("categories", [])
                }
            logger.info(f"Cached {len(self.vendors_cache)} vendors")
        except Exception as e:
            logger.warning(f"Could not load vendor data: {e}")
        
        # Load venues for product/vendor references
        try:
            venues = await self._fetch_all_records("venue", limit=100)
            for venue in venues:
                self.venues_cache[venue.get("_id")] = {
                    "name": venue.get("name", "Unknown Venue"),
                    "area": venue.get("area", ""),
                    "type": venue.get("type", ""),
                    "seats": venue.get("seats")
                }
            logger.info(f"Cached {len(self.venues_cache)} venues")
        except Exception as e:
            logger.warning(f"Could not load venue data: {e}")
        
        # Load images for products/vendors/venues
        try:
            for image_type in ["productimage", "vendorimage", "venueimage"]:
                images = await self._fetch_all_records(image_type, limit=200)
                for img in images:
                    self.images_cache[img.get("_id")] = img
                logger.info(f"Cached {len(images)} {image_type} records")
        except Exception as e:
            logger.warning(f"Could not load image data: {e}")
    
    async def _fetch_all_records(self, data_type: str, limit: int = 1000) -> List[Dict]:
        """Fetch all records of a given type"""
        all_records = []
        cursor = 0
        
        while cursor < limit:
            records = await self.fetch_ecommerce_data_from_bubble(
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
    
    async def _load_ecommerce_data_type(self, data_type: str, limit: int) -> List[Document]:
        """Load and process a specific e-commerce data type"""
        documents = []
        records = await self._fetch_all_records(data_type, limit)
        
        for record in records:
            doc = self._process_ecommerce_record(record, data_type)
            if doc:
                documents.append(doc)
        
        return documents
    
    def _process_ecommerce_record(self, record: Dict, data_type: str) -> Optional[Document]:
        """Process an e-commerce record into a document with enriched content"""
        try:
            if data_type == "product":
                return self._process_product(record)
            elif data_type == "vendor":
                return self._process_vendor(record)
            elif data_type == "venue":
                return self._process_venue(record)
            else:
                return None
        except Exception as e:
            logger.error(f"Error processing {data_type} record {record.get('_id')}: {e}")
            return None
    
    def _process_product(self, record: Dict) -> Document:
        """Process product/service with vendor and venue information"""
        content_parts = []
        
        # Product name
        name = record.get("name", "Unnamed Product")
        content_parts.append(f"# Product: {name}")
        
        # Vendor information
        vendor_id = record.get("vendor")
        if vendor_id and vendor_id in self.vendors_cache:
            vendor_info = self.vendors_cache[vendor_id]
            vendor_name = vendor_info.get("tradingName") or vendor_info.get("companyName")
            content_parts.append(f"\n## Vendor: {vendor_name}")
        elif record.get("vendorTradingName"):
            content_parts.append(f"\n## Vendor: {record['vendorTradingName']}")
        
        # Status and availability
        content_parts.append(f"\n## Status & Availability")
        content_parts.append(f"- Status: {record.get('status', 'Unknown')}")
        content_parts.append(f"- Published: {'Yes' if record.get('isPublished?', False) else 'No'}")
        if record.get("availability"):
            content_parts.append(f"- Availability: {record['availability']}")
        
        # Pricing
        if record.get("priceModel") or record.get("constantPrice"):
            content_parts.append(f"\n## Pricing")
            if record.get("priceModel"):
                content_parts.append(f"- Model: {record['priceModel']}")
            if record.get("constantPrice"):
                content_parts.append(f"- Price: {record['constantPrice']}")
        
        # Event types
        if record.get("eventTypes"):
            content_parts.append(f"\n## Suitable For")
            content_parts.append(f"- {len(record['eventTypes'])} event types")
        
        # Venues where available
        if record.get("venues"):
            content_parts.append(f"\n## Available at Venues")
            venue_count = len(record["venues"])
            content_parts.append(f"- Available at {venue_count} venues")
            # List first few venue names if available
            for venue_id in record["venues"][:5]:
                if venue_id in self.venues_cache:
                    venue_name = self.venues_cache[venue_id].get("name")
                    content_parts.append(f"  • {venue_name}")
            if venue_count > 5:
                content_parts.append(f"  • ... and {venue_count - 5} more venues")
        
        # Categories
        if record.get("categories"):
            content_parts.append(f"\n## Categories")
            content_parts.append(f"- {len(record['categories'])} categories")
        
        # Additional details from satellite data
        satellite_id = record.get("satellite")
        if satellite_id and satellite_id in self.images_cache:
            satellite_data = self.images_cache.get(satellite_id, {})
            if satellite_data.get("description"):
                content_parts.append(f"\n## Description")
                content_parts.append(satellite_data["description"])
        
        # Create metadata
        metadata = {
            "source": f"bubble://product/{record.get('_id')}",
            "source_type": "product",
            "title": name,
            "record_id": record.get("_id"),
            "vendor_id": vendor_id,
            "vendor_name": self.vendors_cache.get(vendor_id, {}).get("companyName") if vendor_id else record.get("vendorTradingName"),
            "status": record.get("status", "Unknown"),
            "is_published": record.get("isPublished?", False),
            "price_model": record.get("priceModel"),
            "constant_price": record.get("constantPrice"),
            "venue_count": len(record.get("venues", [])),
            "event_type_count": len(record.get("eventTypes", [])),
            "category_count": len(record.get("categories", [])),
            "created_date": record.get("Created Date") or record.get("creationDate"),
            "modified_date": record.get("Modified Date"),
            "has_images": bool(record.get("images")),
            "url": f"{self.config.app_url}/product/{record.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_vendor(self, record: Dict) -> Document:
        """Process vendor/service provider"""
        content_parts = []
        
        # Company name
        company_name = record.get("companyName", "Unnamed Vendor")
        trading_name = record.get("tradingName", "")
        
        display_name = trading_name if trading_name else company_name
        content_parts.append(f"# Vendor: {display_name}")
        
        if trading_name and trading_name != company_name:
            content_parts.append(f"\nCompany: {company_name}")
        
        # Contact
        if record.get("email"):
            content_parts.append(f"\n## Contact")
            content_parts.append(f"- Email: {record['email']}")
        
        # Preference status
        if record.get("IsPreferred?") or record.get("preferenceIndex"):
            content_parts.append(f"\n## Status")
            if record.get("IsPreferred?"):
                content_parts.append(f"- Preferred Vendor: Yes")
            if record.get("preferenceIndex"):
                content_parts.append(f"- Preference Level: {record['preferenceIndex']}")
        
        # Event types
        if record.get("eventTypes"):
            content_parts.append(f"\n## Services For")
            content_parts.append(f"- {len(record['eventTypes'])} event types")
        
        # Categories
        if record.get("categories"):
            content_parts.append(f"\n## Service Categories")
            content_parts.append(f"- {len(record['categories'])} categories")
        
        # Client count
        if record.get("clients"):
            content_parts.append(f"\n## Experience")
            content_parts.append(f"- Served {len(record['clients'])} clients")
        
        # Create metadata
        metadata = {
            "source": f"bubble://vendor/{record.get('_id')}",
            "source_type": "vendor",
            "title": display_name,
            "record_id": record.get("_id"),
            "company_name": company_name,
            "trading_name": trading_name,
            "email": record.get("email"),
            "is_preferred": record.get("IsPreferred?", False),
            "preference_index": record.get("preferenceIndex"),
            "event_type_count": len(record.get("eventTypes", [])),
            "category_count": len(record.get("categories", [])),
            "client_count": len(record.get("clients", [])),
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
            "url": f"{self.config.app_url}/vendor/{record.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    def _process_venue(self, record: Dict) -> Document:
        """Process venue/location"""
        content_parts = []
        
        # Venue name
        name = record.get("name", "Unnamed Venue")
        content_parts.append(f"# Venue: {name}")
        
        # Area and type
        if record.get("area") or record.get("type"):
            content_parts.append(f"\n## Location & Type")
            if record.get("area"):
                content_parts.append(f"- Area: {record['area']}")
            if record.get("type"):
                content_parts.append(f"- Type: {record['type']}")
        
        # Capacity
        if record.get("seats"):
            content_parts.append(f"\n## Capacity")
            content_parts.append(f"- Seats: {record['seats']}")
        
        # Status
        content_parts.append(f"\n## Status")
        is_published = record.get("isPublish?", False)
        content_parts.append(f"- Published: {'Yes' if is_published else 'No'}")
        
        # Event types
        if record.get("eventTypes"):
            content_parts.append(f"\n## Suitable For")
            content_parts.append(f"- {len(record['eventTypes'])} event types")
        
        # Order/priority
        if record.get("order") is not None:
            content_parts.append(f"\n## Display Order")
            content_parts.append(f"- Priority: {record['order']}")
        
        # Short code
        if record.get("shortCode"):
            content_parts.append(f"\n## Reference")
            content_parts.append(f"- Code: {record['shortCode']}")
        
        # Create metadata
        metadata = {
            "source": f"bubble://venue/{record.get('_id')}",
            "source_type": "venue",
            "title": name,
            "record_id": record.get("_id"),
            "area": record.get("area"),
            "venue_type": record.get("type"),
            "seats": record.get("seats"),
            "is_published": is_published,
            "short_code": record.get("shortCode"),
            "order": record.get("order"),
            "event_type_count": len(record.get("eventTypes", [])),
            "created_date": record.get("Created Date"),
            "modified_date": record.get("Modified Date"),
            "url": f"{self.config.app_url}/venue/{record.get('_id')}"
        }
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={k: v for k, v in metadata.items() if v is not None}
        )
    
    async def fetch_ecommerce_data_from_bubble(self, data_type: str, 
                                             limit: int = 100, 
                                             cursor: int = 0) -> List[Dict[str, Any]]:
        """Fetch e-commerce data from Bubble API"""
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


async def ingest_all_ecommerce_data():
    """Main function to ingest all e-commerce data"""
    
    # Get configuration
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]
    
    logger.info("Starting comprehensive e-commerce data ingestion...")
    
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
    
    # Initialize e-commerce loader
    loader = EcommerceDataLoader(config, sync_manager)
    
    # Test connection
    if not loader.test_connection():
        logger.error("Bubble.io API connection failed")
        return
    
    # Load all e-commerce data
    ecommerce_docs = await loader.load_all_ecommerce_data(limit_per_type=300)
    logger.info(f"Loaded {len(ecommerce_docs)} e-commerce documents")
    
    if not ecommerce_docs:
        logger.warning("No e-commerce documents found!")
        return
    
    # Split documents if needed
    logger.info("Splitting documents...")
    docs_transformed = text_splitter.split_documents(ecommerce_docs)
    logger.info(f"Split into {len(docs_transformed)} chunks")
    
    # Ensure metadata is clean
    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""
    
    # Index documents
    logger.info("Indexing e-commerce documents...")
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
    for doc in ecommerce_docs:
        type_counts[doc.metadata.get("source_type", "unknown")] += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("E-COMMERCE DATA INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total e-commerce documents loaded: {len(ecommerce_docs)}")
    logger.info("\nDocuments by type:")
    for doc_type, count in type_counts.items():
        logger.info(f"  - {doc_type}: {count}")
    logger.info(f"\nTotal chunks created: {len(docs_transformed)}")
    logger.info(f"Indexing results: {indexing_stats}")
    logger.info("=" * 60)
    
    # Update sync state
    sync_time = datetime.now()
    for data_type in EcommerceDataLoader.ECOMMERCE_DATA_TYPES:
        sync_manager.update_sync_time(data_type, sync_time, type_counts.get(data_type, 0))
    
    return indexing_stats


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_all_ecommerce_data())