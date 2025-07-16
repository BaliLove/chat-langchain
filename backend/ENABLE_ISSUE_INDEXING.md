# How to Enable Issue Indexing

Currently, issues from Bubble are NOT being indexed into the vector database. To enable the Issue Review feature to work with real data, follow these steps:

## Quick Enable (Recommended)

1. **Add "issue" to the priority data types** in `backend/bubble_loader.py`:
```python
priority_data_types = [
    "training",
    "event", 
    "product",
    "venue",
    "comment",
    "eventreview",
    "booking",
    "user",
    "issue"  # Add this line
]
```

2. **Run the ingestion**:
```bash
cd backend
python -m backend.ingest
```

## Alternative: Use Dedicated Issue Scripts

There are pre-built issue ingestion scripts available:

- `backend/ingest_all_issues.py` - Comprehensive issue ingestion with relationships
- `backend/ingest_issues_with_categories.py` - Issues with proper category mapping
- `backend/ingest_issues_public_only.py` - Only public issues
- `backend/ingest_issues_limited.py` - Limited subset for testing

Run any of these directly:
```bash
python backend/ingest_all_issues.py
```

## Verify Issues are Indexed

After ingestion, verify by checking the vector database for documents with:
- `metadata.source_type = "issue"`
- `metadata.category` containing Bubble category IDs

## Note on Performance

- Issue ingestion includes related data (team members, comments)
- Initial ingestion may take 10-15 minutes for all issues
- Consider using `ingest_issues_limited.py` for testing first