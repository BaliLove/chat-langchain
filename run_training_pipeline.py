"""Run the complete training data pipeline: Bubble → Supabase → Pinecone"""

import asyncio
import os
import logging
from backend.training_data_pipeline import TrainingDataPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_full_pipeline():
    """Run the complete training data ingestion pipeline."""
    
    # Check required environment variables
    required_vars = [
        "BUBBLE_API_TOKEN",
        "NEXT_PUBLIC_SUPABASE_URL", 
        "SUPABASE_SERVICE_ROLE_KEY",
        "OPENAI_API_KEY",
        "PINECONE_API_KEY",
        "PINECONE_INDEX_NAME"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return
    
    # Create pipeline instance
    pipeline = TrainingDataPipeline()
    
    try:
        logger.info("=" * 80)
        logger.info("Starting Training Data Pipeline: Bubble → Supabase → Pinecone")
        logger.info("=" * 80)
        
        # Run ingestion for all training data types
        await pipeline.ingest_all_training_data()
        
        logger.info("=" * 80)
        logger.info("Pipeline completed successfully!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)


async def run_test_pipeline():
    """Run a test with limited data."""
    
    pipeline = TrainingDataPipeline()
    
    try:
        logger.info("Running test pipeline with limited data...")
        
        # Test with just one data type and small batch
        data_type = "TrainingModule"
        
        # Fetch small batch from Bubble
        records = await pipeline.fetch_training_data_from_bubble(
            data_type, 
            limit=5,  # Just 5 records
            cursor=0
        )
        
        if not records:
            logger.warning(f"No {data_type} records found in Bubble")
            return
            
        logger.info(f"Fetched {len(records)} {data_type} records")
        
        # Process records
        processed_records = []
        for record in records:
            processed = pipeline.process_training_module(record)
            processed_records.append(processed)
            logger.info(f"Processed: {processed['title']}")
        
        # Stage in Supabase
        staging_ids = await pipeline.stage_api_data(
            processed_records,
            source_type="bubble",
            data_type=data_type
        )
        logger.info(f"Staged {len(staging_ids)} records in Supabase")
        
        # Process staged data
        await pipeline.process_staged_data(data_type=data_type)
        logger.info("Processed staged data")
        
        # Sync to Pinecone
        await pipeline.sync_to_vector_store(batch_size=5)
        logger.info("Synced to Pinecone vector store")
        
        logger.info("Test pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Test pipeline failed: {e}", exc_info=True)


async def check_pipeline_status():
    """Check the current status of the pipeline."""
    
    from backend.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    
    try:
        # Check ingestion status
        result = supabase.table("raw_data_staging").select(
            "data_type, status, COUNT(*)"
        ).execute()
        
        if result.data:
            logger.info("\nCurrent Pipeline Status:")
            logger.info("-" * 40)
            for row in result.data:
                logger.info(f"{row['data_type']}: {row['COUNT']} records ({row['status']})")
        
        # Check vector sync status
        sync_result = supabase.table("vector_sync_status").select(
            "sync_status, COUNT(*)"
        ).execute()
        
        if sync_result.data:
            logger.info("\nVector Sync Status:")
            logger.info("-" * 40)
            for row in sync_result.data:
                logger.info(f"{row['sync_status']}: {row['COUNT']} records")
                
    except Exception as e:
        logger.error(f"Error checking status: {e}")


async def main():
    """Main entry point."""
    
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            await run_test_pipeline()
        elif command == "status":
            await check_pipeline_status()
        elif command == "full":
            await run_full_pipeline()
        else:
            print("Usage: python run_training_pipeline.py [test|status|full]")
            print("  test   - Run with limited test data")
            print("  status - Check current pipeline status")
            print("  full   - Run full pipeline for all training data")
    else:
        # Default to test mode
        await run_test_pipeline()


if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())