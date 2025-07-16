# Debug Guide: Threads Not Showing in Sidebar

## Quick Checks:

1. **Open Browser Console** (F12) and look for:
   - Network errors when loading the page
   - Console errors related to threads or authentication
   - Check the Network tab for failed API calls to `/api/threads/search`

2. **Check Authentication**:
   ```javascript
   // In browser console, check if user is authenticated:
   localStorage.getItem('supabase.auth.token')
   ```

3. **Check API Connection**:
   - Verify backend is running: `langgraph up`
   - Check `.env.local` has correct `API_BASE_URL`
   - Ensure `LANGSMITH_API_KEY` is set

4. **Thread Requirements**:
   - Thread must have `user_id` in metadata
   - Thread must have at least one message/value
   - User must be authenticated with matching user_id

## Common Fixes:

1. **Clear Browser Data**: 
   - Clear localStorage and cookies for localhost:3000
   - Refresh the page and re-authenticate

2. **Restart Services**:
   ```bash
   # Backend
   cd backend
   langgraph up

   # Frontend
   cd frontend
   yarn dev
   ```

3. **Check Environment Variables**:
   ```bash
   # frontend/.env.local should have:
   API_BASE_URL=http://localhost:57187  # or your LangGraph port
   ```

4. **Verify Thread Creation**:
   - When creating a new chat, check Network tab for POST to `/api/threads`
   - Ensure it returns a valid thread_id
   - Check that subsequent messages are sent with this thread_id