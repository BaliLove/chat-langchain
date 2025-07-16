# Bubble.io Integration - Current Implementation

**Status**: ✅ Working - 119 training documents successfully loaded into Pinecone

## Quick Start

The integration is already working! Training data has been loaded into Pinecone for semantic search.

### To Re-ingest Training Data:
```bash
# From project root
python -m backend.ingest_training_only
```

### To Ingest All Data Sources:
```bash
# This includes LangChain docs + Bubble data
python -m backend.ingest
```

## Architecture

We have **two separate pipelines** serving different purposes:

### 1. Direct Pipeline (WORKING) 
**Flow**: Bubble → Python → Pinecone  
**Purpose**: Semantic search and RAG  
**Status**: ✅ 119 training docs loaded  
**Files**: 
- `backend/bubble_loader.py` - Generic loader
- `backend/training_loader.py` - Enhanced training loader
- `backend/ingest.py` - Main ingestion

### 2. Staged Pipeline (PARTIAL)
**Flow**: Bubble → Supabase → Processing → Pinecone  
**Purpose**: Structured queries, data management  
**Status**: ⚠️ Only 5 test rows  
**Files**: 
- `backend/staged_ingestion_pipeline.py`
- `backend/training_data_pipeline.py`

## Available Bubble.io Data Types

Based on actual API testing (see BUBBLE_API_REALITY.md):

| Data Type | Records | Purpose |
|-----------|---------|---------|
| `training` | 130 | Training modules and content |
| `event` | Many | Event descriptions and details |
| `venue` | Many | Venue information |
| `product` | Many | Products and services |
| `user` | Many | User profiles |
| `comment` | Many | User-generated content |
| `booking` | Many | Booking records |

**Important**: Use exact case! `training` not `TrainingModule`

## Environment Variables

```bash
# In your .env file
BUBBLE_APP_URL=https://app.bali.love
BUBBLE_API_TOKEN=your_api_token_here
BUBBLE_BATCH_SIZE=100
BUBBLE_MAX_CONTENT_LENGTH=10000

# Optional for enhanced training loader
USE_ENHANCED_TRAINING_LOADER=true
```

## Common Commands

### Check Training Data Quality:
```bash
python -m backend.training_quality_report
```

### Test Bubble API Connection:
```python
from backend.bubble_loader import load_bubble_data
docs = load_bubble_data()
print(f"Loaded {len(docs)} documents")
```

## Troubleshooting

### Issue: No data returned
- Check API token permissions
- Verify data types are exposed in Bubble API settings
- Use exact case for data types

### Issue: Wrong data types
- The docs reference `TrainingModule` but the actual type is `training`
- Always check BUBBLE_API_REALITY.md for correct names

### Issue: Duplicate data
- The enhanced training loader filters out generic training docs
- Use either direct loader OR enhanced loader, not both

## Next Steps

1. **For Search/RAG**: Current implementation is working well
2. **For Structured Queries**: Fix the staged pipeline data types:
   ```python
   # In backend/training_data_pipeline.py
   TRAINING_DATA_TYPES = ["training"]  # Not "TrainingModule"
   ```
3. **For Other Data Types**: Add them to bubble_loader.py priority list

## Related Documentation

- `BUBBLE_API_REALITY.md` - Actual API structure and data types
- `DATA_FLOW_ARCHITECTURE.md` - Explains the two pipelines
- `backend/training_loader.py` - See code comments for implementation details