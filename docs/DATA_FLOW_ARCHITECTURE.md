# Data Flow Architecture - Bali Love Agent Chat

## Overview
This document clarifies the data flow architecture to prevent conflicting implementations. There are **two separate pipelines** serving different purposes:

## 1. Direct Vector Store Pipeline (For Search/RAG)
**Purpose**: Load data directly into Pinecone for semantic search and RAG functionality

### Flow:
```
Bubble.io API → Python Processing → Pinecone Vector Store
```

### Components:
- `backend/bubble_loader.py` - Generic Bubble.io data loader
- `backend/training_loader.py` - Enhanced training data loader with quality validation
- `backend/ingest.py` - Main ingestion script that combines all data sources
- **Target**: Pinecone vector database
- **Use Case**: Semantic search, question answering, RAG

### Current Status:
- ✅ Training data (119 documents) loaded into Pinecone
- ✅ Enhanced extraction with metadata enrichment
- ✅ Quality validation and filtering

## 2. Staged Supabase Pipeline (For Structured Storage)
**Purpose**: Stage data in Supabase for structured queries, then optionally sync to vector store

### Flow:
```
Bubble.io API → Supabase Staging → Processing → Supabase Tables → (Optional) Vector Store
```

### Tables:
1. **raw_data_staging**
   - Stores raw data from Bubble.io
   - Fields: id, source_id, source_type, data_type, raw_data, processed_data, status
   - Currently has 5 rows (as you mentioned)

2. **vector_sync_status**
   - Tracks which staged data has been synced to vector store
   - Links staging records to vector store entries

3. **api_fetch_history**
   - Tracks what data has been fetched from APIs
   - Prevents duplicate fetches

### Components:
- `backend/staged_ingestion_pipeline.py` - Base pipeline class
- `backend/training_data_pipeline.py` - Training-specific implementation
- **Target**: Supabase PostgreSQL database
- **Use Case**: Structured queries, data management, audit trail

### Current Status:
- ⚠️ Only 5 rows in raw_data_staging
- ❌ Training data types misconfigured (looking for wrong Bubble.io types)

## Key Differences

| Aspect | Direct Pipeline | Staged Pipeline |
|--------|----------------|-----------------|
| **Target** | Pinecone (Vector DB) | Supabase (PostgreSQL) |
| **Purpose** | Semantic search | Structured storage |
| **Data Flow** | Direct transformation | Multi-stage with approval |
| **Use Cases** | RAG, Q&A, Search | Reporting, CRUD, Audit |
| **Current Status** | ✅ Working (119 docs) | ⚠️ Partial (5 rows) |

## Recommended Approach

### For Training Data Search (Current Need):
Use the **Direct Pipeline** which is already working:
```bash
python -m backend.ingest_training_only
```

### For Structured Data Management (Future):
Fix and use the **Staged Pipeline**:
1. Update `TRAINING_DATA_TYPES` in `training_data_pipeline.py` to use `["training"]`
2. Run the staged pipeline to populate Supabase
3. Use Supabase for structured queries and management

## Avoiding Conflicts

1. **Don't mix pipelines** - Each serves a different purpose
2. **Direct Pipeline** = Search and RAG only
3. **Staged Pipeline** = Data management and structured queries
4. **No "upserted_record" table** - This doesn't exist in the current schema

## Next Steps

If you need training data in Supabase for structured queries:
1. Fix the data type in `training_data_pipeline.py` (line 18-27)
2. Change from `["TrainingModule", "trainingsession", ...]` to `["training"]`
3. Run the staged pipeline to populate Supabase

For now, your training data is successfully loaded in Pinecone for search functionality.