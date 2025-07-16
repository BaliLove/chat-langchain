# Issue Category Mapping Documentation

## Overview

This document explains how issue categories are mapped between the Bubble.io backend and the frontend application.

## Category System

### Frontend Categories

The frontend uses the following category values:

1. **operations** - Operations (Workflow, processes, and efficiency)
2. **venue** - Venue (Partner venues and locations)
3. **marketing** - Marketing (Campaigns and brand)
4. **finance** - Finance (Payments and budgets)
5. **technology** - Technology (Systems and tools)
6. **customer_service** - Customer Service (Guest experience)
7. **team** - Team (People and culture)

### Bubble.io Category IDs

In Bubble.io, categories are stored as unique IDs. The following mapping is used:

| Bubble ID | Frontend Category | Label |
|-----------|------------------|-------|
| 1683764078523x515115226215481340 | venue | Venue |
| 1683764027028x314003986352177150 | operations | Operations |
| 1683764033628x667123255737843700 | marketing | Marketing |
| 1683764048683x626863668112916500 | finance | Finance |
| 1698451776177x772559502883684400 | technology | Technology |
| 1683764063723x899495422051483600 | customer_service | Customer Service |

## Files and Utilities

### Mapping Files

1. **`backend/issue_category_lookup.json`** - Simple ID to category mapping
2. **`backend/issue_category_complete_mapping.json`** - Complete mapping with metadata

### Utility Class

**`backend/utils/issue_category_mapper.py`** - Python utility for category mapping

```python
from utils.issue_category_mapper import IssueCategoryMapper

# Initialize mapper
mapper = IssueCategoryMapper()

# Map a Bubble category ID to frontend category
category = mapper.map_category("1683764078523x515115226215481340")  # Returns: "venue"

# Get display label
label = mapper.get_category_label("venue")  # Returns: "Venue"

# Add new mapping
mapper.add_mapping("new_bubble_id", "team")
```

## Usage in Ingestion

When ingesting issues from Bubble.io:

1. Fetch the issue data including the `category` field
2. Use the `IssueCategoryMapper` to convert the Bubble ID to frontend category
3. Store both the original ID and mapped category for reference

Example:
```python
# From backend/ingest_issues_with_categories.py
bubble_category_id = issue.get("category")
category = mapper.map_category(bubble_category_id)
category_label = mapper.get_category_label(category)

processed_issue = {
    "bubble_category_id": bubble_category_id,
    "category": category,  # Frontend value used for filtering
    "category_label": category_label  # Display name
}
```

## Frontend Usage

The frontend components use the mapped category values:

```tsx
// From frontend/app/components/IssueCategorySelector.tsx
const ISSUE_CATEGORIES = [
  { value: 'operations', label: 'Operations', ... },
  { value: 'venue', label: 'Venue', ... },
  // etc.
]
```

## Adding New Categories

To add a new category:

1. Add the category to the frontend `ISSUE_CATEGORIES` array
2. Find the Bubble ID for the new category
3. Update the mapping files using:
   ```python
   mapper.add_mapping("bubble_id", "new_category")
   ```

## Troubleshooting

### Unmapped Categories

If you encounter unmapped category IDs during ingestion:

1. The mapper will return "unknown" for unmapped IDs
2. Check the ingestion logs for warnings about unmapped categories
3. Use the discovery script to analyze issues and identify category patterns:
   ```bash
   python backend/discover_issue_categories.py
   ```

### Category Discovery

To discover all category IDs in use:

```bash
python backend/discover_issue_categories.py
```

This will analyze your Bubble data and suggest mappings based on issue content.