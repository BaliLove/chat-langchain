# Update Category IDs Instructions

The Issue Review prompt needs the actual Bubble category IDs for all 19 categories. 

## Current Categories Needing Real IDs:

Based on the prompt-starters.tsx file, these are the 19 categories that need real Bubble IDs:

1. **Client Exp** - Currently: 1683764063723x899495422051483600 (might be customer_service)
2. **Weddings** - Currently: 1683764078523x515115226215481340 (might be venue) 
3. **Guests & Accom** - Currently: 1698451776177x772559502883684400 (might be technology)
4. **Event Requests** - Currently: 1683764027028x314003986352177150 (might be operations)
5. **Vendor & Product Requests** - Currently: 1683764033628x667123255737843700 (might be marketing)
6. **Catalog** - Currently: 1683764048683x626863668112916500 (might be finance)
7. **Accounts** - Needs real ID (placeholder: 1698451776177x772559502883684401)
8. **Metabase** - Needs real ID (placeholder: 1698451776177x772559502883684402)
9. **App Requests** - Needs real ID (placeholder: 1698451776177x772559502883684403)
10. **App Updates** - Needs real ID (placeholder: 1698451776177x772559502883684404)
11. **Digital** - Needs real ID (placeholder: 1698451776177x772559502883684405)
12. **Revenue** - Needs real ID (placeholder: 1698451776177x772559502883684406)
13. **People** - Needs real ID (placeholder: 1698451776177x772559502883684407)
14. **Leaders** - Needs real ID (placeholder: 1698451776177x772559502883684408)
15. **AI Workflows** - Needs real ID (placeholder: 1698451776177x772559502883684409)
16. **Venues** - Needs real ID (placeholder: 1698451776177x772559502883684410)
17. **Content** - Needs real ID (placeholder: 1698451776177x772559502883684411)
18. **Styling** - Needs real ID (placeholder: 1698451776177x772559502883684412)
19. **Vehicles** - Needs real ID (placeholder: 1698451776177x772559502883684413)

## How to Get the Real IDs:

1. **Option A: Query Bubble Directly**
   - Go to your Bubble app data tab
   - Look at the Issue data type
   - Find the Category field options
   - Copy each category's unique ID

2. **Option B: Run the Discovery Script**
   ```bash
   cd backend
   # Make sure BUBBLE_API_TOKEN is set in .env
   python fetch_issue_categories.py
   ```

3. **Option C: Check Existing Issues**
   - Look at a few issues from each category in Bubble
   - Note their category field values

## Files to Update:

Once you have the real IDs, update these files:

1. `backend/retrieval_graph/issue_category_review_prompt.py` (lines 29-47)
2. `backend/issue_category_lookup.json` (add all 19 mappings)
3. `frontend/app/components/chat-interface/prompt-starters.tsx` (already updated with placeholders)

## Important Notes:

- The first 6 IDs in the list above are the ones we found in the existing mapping files
- They might not correspond to the category names I've assigned - you'll need to verify
- Categories 7-19 are using placeholder IDs that need to be replaced
- The IDs follow Bubble's format: long number + 'x' + long number