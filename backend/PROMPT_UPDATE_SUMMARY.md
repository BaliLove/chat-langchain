# Bali Love Prompt Update Summary

## What Was Updated

I've successfully updated the local prompts in `backend/retrieval_graph/custom_prompts.py` with enhanced versions specifically tailored for Bali Love's needs.

## Key Improvements

### 1. **Enhanced Router Prompt**
- Now recognizes Bali Love specific queries (event codes, messages, vendors)
- Better classification of research vs general queries
- Includes examples with event codes like "KM150726VV"

### 2. **Improved Query Generation**
- Aware of Bali Love data types (events, inbox messages, vendors, venues)
- Generates queries with proper field names (event_code, needs_reply, etc.)
- Optimized for message/communication searches

### 3. **Bali Love Context in More-Info Prompt**
- Asks for event codes when missing
- Suggests specific data types to search
- More helpful clarification requests

### 4. **Research Plan Optimization**
- Plans consider wedding-specific data
- Includes steps for message reply status
- Handles contact information retrieval

### 5. **Better Response Formatting**
- Organizes data by category (messages, tasks, issues)
- Highlights items needing attention
- Clear, actionable formatting for the team

## How to Use

### Option 1: Use Local Prompts (Currently Active)
The system is already using the updated prompts since `USE_LANGSMITH_PROMPTS=false` by default.

### Option 2: Push to LangSmith (Requires Owner Setup)
To use LangSmith prompt management:
1. Set up prompt owner in LangSmith
2. Use the manage_prompts.py script with proper authentication
3. Set `USE_LANGSMITH_PROMPTS=true` in environment

## Testing the Updated Prompts

Try these queries to see the improvements:

1. **Event-specific message query:**
   "For KM150726VV, are there any messages that aren't replied?"

2. **Vendor search:**
   "Show me all venues in Ubud"

3. **Issue tracking:**
   "What are the open issues for event SARLEAD?"

4. **General message search:**
   "Find all messages from last week that need replies"

## Router Logic Examples

The updated router will now correctly classify:
- "Hello" → `general`
- "For wedding JA070926VV, show unreplied messages" → `research`
- "Find messages" → `more-info` (needs event specification)
- "What venues do we have?" → `research`

## Benefits

1. **Better Query Understanding**: The system now understands Bali Love's business context
2. **More Accurate Routing**: Queries are classified correctly based on wedding planning needs
3. **Improved Search Results**: Generated queries target the right data fields
4. **Clearer Responses**: Results are formatted for easy team consumption

The prompts are ready to use and will significantly improve how the system handles Bali Love specific queries!