# Venue Chatbot Setup Summary

## Current Status

Your chatbot has Bali venue/event data in Pinecone but is still using LangChain-specific prompts in production. Here's how to fix it:

## Quick Fix Process

### Step 1: Create Prompts in LangSmith (5 minutes)

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Create 6 new prompts using the templates in `LANGSMITH_PROMPTS_COPY_PASTE.md`
3. Name them exactly as specified:
   - `bali-love-router-prompt`
   - `bali-love-generate-queries-prompt`
   - `bali-love-more-info-prompt`
   - `bali-love-research-plan-prompt`
   - `bali-love-general-prompt`
   - `bali-love-response-prompt`

### Step 2: Update Your Code (2 minutes)

Replace `backend/retrieval_graph/prompts.py` with the contents of `prompts_updated.py`:

```bash
cp backend/retrieval_graph/prompts_updated.py backend/retrieval_graph/prompts.py
```

### Step 3: Commit and Deploy (5 minutes)

```bash
git add backend/retrieval_graph/prompts.py
git commit -m "Update prompts to use Bali venue-specific LangSmith prompts"
git push
```

Your LangGraph Cloud deployment will automatically update.

## What This Fixes

**Before:** 
- Query: "What wedding venues are available in Uluwatu?"
- Response: "I only help with LangChain questions..."

**After:**
- Query: "What wedding venues are available in Uluwatu?"
- Response: "I found several beautiful wedding venues in Uluwatu including Alila Uluwatu and Stone Villa Uluwatu..."

## How It Works

1. **Router** now recognizes venue/event queries as "research" (not "general")
2. **Query Generator** creates venue-specific search terms
3. **Response** formats results with venue details and Bali context

## Testing

Once deployed, test these queries:
- "Tell me about wedding venues in Uluwatu"
- "Show me Alila Uluwatu"
- "What event services do you offer?"
- "I need a venue for 200 guests"

## Already Completed

✅ Discovered 31 Bubble data types  
✅ Ingested thousands of venue/event records into Pinecone  
✅ Created venue-specific prompt templates  
✅ Data is searchable and ready

## Alternative: Skip LangSmith

If you prefer not to use LangSmith, set this environment variable in your deployment:

```
USE_LANGSMITH_PROMPTS=false
```

This will use the custom prompts from `custom_prompts.py` instead.

## Next Steps

After fixing the prompts:
1. Add more Bubble data types (Bookings, Guests, Vendors)
2. Schedule regular data updates
3. Add location-based filtering
4. Create a venue showcase UI component

Your venue data is ready - you just need to update the prompts to access it!