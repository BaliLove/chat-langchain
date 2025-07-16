# Instructions to Fetch Issue Categories from Bubble

## Step 1: Find the IssuesCategory Table

Run this script to find and fetch the categories:

```bash
cd backend
python fetch_issues_category_table.py
```

This script will:
- Try multiple naming conventions for the category table
- Display all categories with their Bubble IDs
- Save the data to `bubble_categories_actual.json`
- Generate the exact text to update the prompt

## Step 2: If Categories are Found

The script will output something like:
```
=== Found 19 Categories in 'IssuesCategory' ===

1. Client Exp
   ID: 1234567890x123456789012345
   
2. Weddings  
   ID: 2345678901x234567890123456
   
... (and so on for all 19 categories)
```

## Step 3: Update the Files

Once you have the real IDs, update these files:

### 1. Update `backend/retrieval_graph/issue_category_review_prompt.py`

Replace lines 29-47 with the actual categories and IDs from the script output.

### 2. Update `backend/issue_category_lookup.json`

Replace the content with all 19 mappings:
```json
{
  "actual_bubble_id_1": "client_exp",
  "actual_bubble_id_2": "weddings",
  ... (all 19 mappings)
}
```

### 3. Run the sync script

```bash
cd backend
python sync_issue_prompts.py
```

## Step 4: Import to Supabase (Optional but Recommended)

To make categories manageable from Supabase:

1. Run the import script:
```bash
python import_issue_categories_to_supabase.py
```

2. This will:
   - Create a SQL script for the Supabase table
   - Fetch categories from Bubble
   - Import them to Supabase
   - Create mapping files

## Alternative: Manual Approach

If the IssuesCategory table doesn't exist in Bubble:

1. Go to your Bubble.io app
2. Navigate to Data > Data Types
3. Look for where issue categories are defined
4. Copy the ID for each category
5. Update the files manually

## Troubleshooting

If the script can't find the categories table:
1. Check the exact name in Bubble (case-sensitive)
2. Add it to the `possible_names` list in the script
3. Make sure your BUBBLE_API_TOKEN has read access to that data type