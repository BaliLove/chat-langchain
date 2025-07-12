# Bubble.io Integration Setup Guide

## Overview
This guide walks you through setting up the Bubble.io data integration with your LangChain chat system. The integration allows your chat system to search and answer questions about data from your Bubble.io application.

## Prerequisites

### 1. Bubble.io API Access
- Your Bubble.io app must be on a plan that supports the Data API
- Admin access to your Bubble.io application
- API endpoints enabled for the data types you want to integrate

### 2. System Requirements
- Python 3.8+
- PostgreSQL database (for sync state management)
- Pinecone vector database
- Required Python packages (see requirements.txt)

## Step 1: Enable Bubble.io Data API

### 1.1 Access API Settings
1. Go to your Bubble.io app dashboard
2. Navigate to **Settings** → **API**
3. Check **"Enable Data API"**

### 1.2 Configure Data Types
Enable the data types you want to integrate:
- ✅ **Event** (recommended - rich content)
- ✅ **Product** (recommended - descriptions, specs)
- ✅ **Venue** (recommended - detailed info)
- ✅ **Comment** (recommended - user content)
- ✅ **EventReview** (recommended - reviews, feedback)
- ⚠️ **Booking** (optional - less rich content)
- ⚠️ **Guest** (optional - privacy considerations)

### 1.3 Generate API Token
1. In the API settings, generate a **Private API Key**
2. Copy and securely store this token
3. **Important**: This key provides admin-level access to your database

## Step 2: Environment Configuration

### 2.1 Required Environment Variables
Add these to your environment (`.env` file or deployment environment):

```bash
# Existing variables (should already be set)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_index_name
RECORD_MANAGER_DB_URL=postgresql://user:password@host:port/database

# NEW: Bubble.io Integration
BUBBLE_APP_URL=https://app.bali.love
BUBBLE_API_TOKEN=your_bubble_private_api_key

# OPTIONAL: Bubble.io Configuration
BUBBLE_BATCH_SIZE=100                    # Records per API call (default: 100)
BUBBLE_MAX_CONTENT_LENGTH=10000          # Max content length (default: 10000)
BUBBLE_SYNC_INTERVAL=3600               # Sync interval in seconds (default: 1 hour)
```

### 2.2 Example .env File
```bash
# Vector Database
PINECONE_API_KEY=12345678-1234-1234-1234-123456789abc
PINECONE_INDEX_NAME=langchain-chat
RECORD_MANAGER_DB_URL=postgresql://username:password@localhost:5432/langchain_db

# Bubble.io Integration
BUBBLE_APP_URL=https://app.bali.love
BUBBLE_API_TOKEN=abcd1234efgh5678ijkl9012mnop3456

# Optional: Fine-tuning
BUBBLE_BATCH_SIZE=50
BUBBLE_MAX_CONTENT_LENGTH=8000
```

## Step 3: Database Setup

### 3.1 Sync State Table
The integration automatically creates the required table, but you can create it manually if needed:

```sql
-- Create Bubble.io sync tracking table
CREATE TABLE IF NOT EXISTS bubble_sync_state (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(50) NOT NULL UNIQUE,
    last_sync_timestamp TIMESTAMP WITH TIME ZONE,
    last_successful_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_bubble_sync_data_type 
ON bubble_sync_state(data_type);
```

### 3.2 Database Permissions
Ensure your database user has permissions to:
- CREATE tables
- INSERT, UPDATE, SELECT on bubble_sync_state table
- Access to the existing record manager tables

## Step 4: Installation & Testing

### 4.1 Install Dependencies
```bash
# Install additional dependencies (if not already installed)
pip install sqlalchemy requests

# Or add to requirements.txt:
echo "sqlalchemy>=2.0.0" >> requirements.txt
echo "requests>=2.28.0" >> requirements.txt
```

### 4.2 Test Bubble.io Connection
Create a test script to verify the connection:

```python
# test_bubble_connection.py
import os
from backend.bubble_loader import load_bubble_data

# Set environment variables (or load from .env)
os.environ["BUBBLE_APP_URL"] = "https://app.bali.love"
os.environ["BUBBLE_API_TOKEN"] = "your_api_token"
os.environ["RECORD_MANAGER_DB_URL"] = "your_db_url"

# Test the connection
print("Testing Bubble.io integration...")
docs = load_bubble_data()

if docs:
    print(f"✅ Success! Loaded {len(docs)} documents")
    print(f"📄 Sample document:")
    print(f"   Content: {docs[0].page_content[:100]}...")
    print(f"   Source: {docs[0].metadata.get('source')}")
    print(f"   Type: {docs[0].metadata.get('source_type')}")
else:
    print("❌ No documents loaded. Check configuration.")
```

Run the test:
```bash
python test_bubble_connection.py
```

### 4.3 Test Full Integration
Test the complete ingestion pipeline:

```bash
# Run the full ingestion (this will include Bubble.io data)
python backend/ingest.py
```

Expected output should include:
```
INFO:backend.bubble_loader:Bubble.io API connection successful (tested with event)
INFO:backend.ingest:Loaded 15 docs from Bubble.io
INFO:backend.ingest:Successfully integrated 45 Bubble.io documents out of 1250 total documents (3.6%)
```

## Step 5: Production Deployment

### 5.1 GitHub Actions Integration
Update your GitHub Actions workflow to include Bubble.io environment variables:

```yaml
# .github/workflows/update-index.yml
name: Update index

on:
  workflow_dispatch:
    inputs:
      force_update:
        description: 'Whether to overwrite documents found in the record manager'
        required: false
        default: false
        type: boolean
  schedule:
    - cron: '0 13 * * *'

jobs:
  build:
    runs-on: ubuntu-latest
    environment: Indexing
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Poetry
        uses: snok/install-poetry@v1
      - name: Install dependencies
        run: poetry install
      - name: Ingest docs
        run: poetry run python backend/ingest.py
        env:
          # Existing variables
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
          PINECONE_INDEX_NAME: ${{ secrets.PINECONE_INDEX_NAME }}
          RECORD_MANAGER_DB_URL: ${{ secrets.RECORD_MANAGER_DB_URL }}
          VOYAGE_AI_MODEL: ${{ secrets.VOYAGE_AI_MODEL }}
          VOYAGE_AI_URL: ${{ secrets.VOYAGE_AI_URL }}
          VOYAGE_API_KEY: ${{ secrets.VOYAGE_API_KEY }}
          FORCE_UPDATE: ${{ github.event.inputs.force_update }}
          
          # NEW: Bubble.io Integration
          BUBBLE_APP_URL: ${{ secrets.BUBBLE_APP_URL }}
          BUBBLE_API_TOKEN: ${{ secrets.BUBBLE_API_TOKEN }}
```

### 5.2 Add GitHub Secrets
In your GitHub repository settings, add these secrets:
- `BUBBLE_APP_URL`: Your Bubble.io app URL
- `BUBBLE_API_TOKEN`: Your Bubble.io private API key

### 5.3 Docker Integration (if using Docker)
Update your Dockerfile/docker-compose.yml to include Bubble.io environment variables:

```yaml
# docker-compose.yml
version: '3.8'
services:
  ingestion:
    build: .
    environment:
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
      - RECORD_MANAGER_DB_URL=${RECORD_MANAGER_DB_URL}
      # Add Bubble.io variables
      - BUBBLE_APP_URL=${BUBBLE_APP_URL}
      - BUBBLE_API_TOKEN=${BUBBLE_API_TOKEN}
```

## Step 6: Monitoring & Maintenance

### 6.1 Monitor Sync Status
Query sync state to monitor performance:

```sql
-- Check sync status
SELECT 
    data_type,
    last_sync_timestamp,
    last_successful_count,
    error_count,
    EXTRACT(EPOCH FROM (NOW() - last_sync_timestamp)) / 3600 as hours_since_sync
FROM bubble_sync_state
ORDER BY last_sync_timestamp DESC;
```

### 6.2 Check Ingestion Logs
Monitor your ingestion logs for:
- ✅ Successful connections: `"Bubble.io API connection successful"`
- 📊 Document counts: `"Loaded X docs from Bubble.io"`
- ❌ Errors: `"Failed to load Bubble.io data"`
- 🔄 Sync updates: `"Updated sync state for event: 25 records"`

### 6.3 Content Quality Monitoring
Check the quality of ingested content:

```python
# Monitor content quality script
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
import os

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(os.environ["PINECONE_INDEX_NAME"])
vectorstore = PineconeVectorStore(index=index, embedding=embedding)

# Search for Bubble.io content
bubble_docs = vectorstore.similarity_search(
    "event venue product", 
    filter={"source_system": "bubble.io"},
    k=10
)

print(f"Found {len(bubble_docs)} Bubble.io documents")
for doc in bubble_docs[:3]:
    print(f"Type: {doc.metadata.get('source_type')}")
    print(f"Content: {doc.page_content[:100]}...")
    print("---")
```

## Troubleshooting

### Common Issues

#### 1. "No documents loaded from Bubble.io"
**Possible Causes:**
- ❌ API token is incorrect
- ❌ Data API not enabled in Bubble.io
- ❌ No data types are enabled
- ❌ Data types are empty

**Solutions:**
```bash
# Test API connection
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
     "https://app.bali.love/api/1.1/obj/event?limit=1"

# Should return JSON with results, not 401/404
```

#### 2. "Authentication failed"
**Solutions:**
- Verify API token is correct
- Ensure token has admin permissions
- Check that API hasn't been disabled

#### 3. "No content quality passed"
**Possible Causes:**
- Content is too short (< 20 characters)
- Content contains system-generated text
- All content is duplicate

**Solutions:**
- Check your Bubble.io data has substantial content
- Verify description fields are populated
- Check BUBBLE_MAX_CONTENT_LENGTH setting

#### 4. Database Connection Issues
**Solutions:**
```bash
# Test database connection
python -c "
from sqlalchemy import create_engine
engine = create_engine('$RECORD_MANAGER_DB_URL')
with engine.connect() as conn:
    print('✅ Database connection successful')
"
```

### Performance Optimization

#### 1. Adjust Batch Size
For large datasets, adjust batch size:
```bash
# Smaller batches for stability
BUBBLE_BATCH_SIZE=25

# Larger batches for speed (if stable)
BUBBLE_BATCH_SIZE=200
```

#### 2. Content Length Optimization
Balance content quality vs. processing speed:
```bash
# Shorter content for faster processing
BUBBLE_MAX_CONTENT_LENGTH=5000

# Longer content for richer context
BUBBLE_MAX_CONTENT_LENGTH=15000
```

#### 3. Sync Frequency
Adjust based on your data update frequency:
```bash
# Hourly updates for active data
BUBBLE_SYNC_INTERVAL=3600

# Daily updates for stable data  
BUBBLE_SYNC_INTERVAL=86400
```

## Security Considerations

### 1. API Token Security
- ✅ Store API tokens in secure environment variables
- ✅ Use GitHub Secrets for CI/CD
- ✅ Rotate tokens periodically
- ❌ Never commit tokens to version control

### 2. Data Privacy
- Review which data types contain sensitive information
- Consider excluding user data (Guest, BookingGuests)
- Use privacy rules in Bubble.io to limit API access

### 3. Access Controls
- Limit database permissions to minimum required
- Monitor API usage for unusual patterns
- Set up alerting for ingestion failures

## Next Steps

After successful setup:

1. **Monitor Performance**: Check ingestion logs and sync status regularly
2. **Content Quality**: Review search results to ensure quality content integration
3. **Optimize Queries**: Test chat responses with Bubble.io content
4. **Scale Up**: Consider adding more data types as needed
5. **Automation**: Set up automated monitoring and alerting

## Support

For additional help:
- Check the ingestion logs for specific error messages
- Review Bubble.io API documentation
- Test individual components (API connection, database, etc.)
- Monitor the vector store for successful document ingestion

The integration is designed to fail gracefully - if Bubble.io is unavailable, the system will continue with other data sources. 