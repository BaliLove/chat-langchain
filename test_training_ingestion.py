"""Test script for training data ingestion"""

import asyncio
import os
from backend.training_data_pipeline import TrainingDataPipeline
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_single_data_type():
    """Test ingesting a single training data type."""
    pipeline = TrainingDataPipeline()
    
    # Test with just training modules first
    logger.info("Testing training module ingestion...")
    
    # Fetch a small sample
    try:
        records = await pipeline.fetch_training_data_from_bubble(
            "training_module", 
            limit=5,  # Just 5 records for testing
            cursor=0
        )
        
        if records:
            logger.info(f"Fetched {len(records)} training modules")
            
            # Process the records
            processed = []
            for record in records:
                processed_record = pipeline.process_training_module(record)
                processed.append(processed_record)
                logger.info(f"Processed: {processed_record['title']}")
            
            # Stage in Supabase
            staging_ids = await pipeline.stage_api_data(
                processed,
                source_type="bubble",
                data_type="training_module"
            )
            
            logger.info(f"Staged {len(staging_ids)} records in Supabase")
            
            # Process staged data
            await pipeline.process_staged_data(
                data_type="training_module",
                limit=5
            )
            
            # Sync to vector store
            await pipeline.sync_to_vector_store(batch_size=5)
            
            logger.info("Test completed successfully!")
        else:
            logger.warning("No training modules found in Bubble")
            
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


async def test_sample_data():
    """Test with sample data if no Bubble connection."""
    pipeline = TrainingDataPipeline()
    
    # Sample training data
    sample_data = [
        {
            "_id": "test-module-001",
            "title": "Introduction to Customer Service",
            "description": "Learn the fundamentals of excellent customer service, including communication skills, problem-solving, and conflict resolution.",
            "category": "Customer Service",
            "duration": "2 hours",
            "prerequisites": "None",
            "learning_objectives": "Understand customer needs, Handle difficult situations, Communicate effectively"
        },
        {
            "_id": "test-module-002",
            "title": "Health and Safety Training",
            "description": "Essential health and safety procedures for all staff members, covering workplace hazards, emergency procedures, and safety equipment.",
            "category": "Compliance",
            "duration": "3 hours",
            "prerequisites": "Employee Orientation",
            "learning_objectives": "Identify workplace hazards, Follow safety procedures, Use safety equipment properly"
        }
    ]
    
    # Process sample data
    processed = []
    for record in sample_data:
        processed_record = pipeline.process_training_module(record)
        processed.append(processed_record)
        logger.info(f"Processed: {processed_record['title']}")
    
    # Stage in Supabase
    try:
        staging_ids = await pipeline.stage_api_data(
            processed,
            source_type="manual",
            data_type="training_module"
        )
        
        logger.info(f"Staged {len(staging_ids)} sample records")
        
        # Process and sync
        await pipeline.process_staged_data(data_type="training_module")
        await pipeline.sync_to_vector_store()
        
        logger.info("Sample data test completed!")
        
    except Exception as e:
        logger.error(f"Sample data test failed: {e}", exc_info=True)


async def main():
    """Run tests based on environment."""
    
    # Check if we have Bubble credentials
    if os.getenv("BUBBLE_API_TOKEN"):
        logger.info("Bubble API token found, testing with real data...")
        await test_single_data_type()
    else:
        logger.info("No Bubble API token, testing with sample data...")
        await test_sample_data()


if __name__ == "__main__":
    # Set required environment variables for testing
    # os.environ["BUBBLE_API_TOKEN"] = "your-token-here"
    # os.environ["SUPABASE_URL"] = "your-supabase-url"
    # os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "your-service-key"
    # os.environ["OPENAI_API_KEY"] = "your-openai-key"
    # os.environ["PINECONE_API_KEY"] = "your-pinecone-key"
    # os.environ["PINECONE_INDEX_NAME"] = "your-index-name"
    
    asyncio.run(main())