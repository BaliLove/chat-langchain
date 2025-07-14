"""Debug metadata format issue"""

import asyncio
import os
from dotenv import load_dotenv
from backend.training_data_pipeline import TrainingDataPipeline
from backend.supabase_client import get_supabase_client

load_dotenv()

async def debug_metadata():
    # Get processed data from Supabase
    supabase = get_supabase_client()
    
    result = supabase.table("raw_data_staging").select("*").eq("status", "processed").limit(1).execute()
    
    if result.data:
        record = result.data[0]
        print("Raw data keys:", list(record['raw_data'].keys()))
        print("\nProcessed data:")
        import json
        print(json.dumps(record['processed_data'], indent=2))
        
        # Check metadata structure
        metadata = record['processed_data'].get('metadata', {})
        print("\nMetadata structure:")
        for key, value in metadata.items():
            print(f"  {key}: {type(value).__name__} = {repr(value)[:100]}")

if __name__ == "__main__":
    asyncio.run(debug_metadata())