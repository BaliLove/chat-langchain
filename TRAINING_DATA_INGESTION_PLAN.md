# Training Data Ingestion Plan

## Current Status
✅ **Completed**: 119 training module documents ingested from `training` data type

## Discovered Training Data Structure

### Data Types Found (4 unique types, 8 total with case variants)
1. **training/TrainingModule** (130 records total, 119 ingested)
   - Core training content and modules
   - ✅ Already ingested with enhanced extraction

2. **trainingsession/TrainingSession** (unknown total, 0 ingested)
   - Individual training session records
   - Links trainees to modules
   - Tracks attendance and completion

3. **trainingplan/TrainingPlan** (unknown total, 0 ingested)
   - Employee-specific training plans
   - Goal completion dates
   - Progress tracking

4. **trainingqualification/TrainingQualification** (unknown total, 0 ingested)
   - Qualification definitions
   - Ordered list of available qualifications

## Relationships
```
TrainingModule (1) ──> (N) TrainingSession
     │                          │
     │                          ├──> trainees (users)
     │                          ├──> trainers (users)
     │                          └──> calendarEvent
     │
     └──> qualifications (TrainingQualification)
     └──> qualifiedToTrain (users)

TrainingPlan ──> trainee (user)
             └──> goalCompletionDate
```

## Ingestion Strategy

### Phase 1: Complete Core Training Data ✅
- Training modules with content
- Status: COMPLETE (119 docs)

### Phase 2: Training Sessions (NEXT PRIORITY)
**Why Important**: Shows who completed what training and when
```python
# Key data to extract:
- Session date/time from calendarEvent
- Trainee names and IDs
- Trainer names  
- Associated module title
- Completion status
```

### Phase 3: Training Plans
**Why Important**: Shows individual learning paths and progress
```python
# Key data to extract:
- Employee/trainee name
- Goal completion date
- Associated modules (if linked)
- Progress status
```

### Phase 4: Training Qualifications
**Why Important**: Defines what qualifications exist
```python
# Key data to extract:
- Qualification name
- Order/hierarchy
- Related modules
```

## Implementation Steps

### 1. Extend bubble_loader.py
```python
# Add to priority_data_types:
"trainingsession",    # Use lowercase based on API
"trainingplan",
"trainingqualification"
```

### 2. Create Content Extractors
Add specialized extractors for each type in bubble_loader.py:
- `_extract_training_session_content()`
- `_extract_training_plan_content()`
- `_extract_training_qualification_content()`

### 3. Handle Relationships
When ingesting sessions:
- Resolve trainingModule references to get module titles
- Extract trainee/trainer names for searchability
- Parse calendarEvent for dates

### 4. Run Full Training Ingestion
```bash
# Create a script to ingest all training data
python -m backend.ingest_all_training_data
```

## Expected Outcomes

After complete ingestion:
- ~119 training module documents (current)
- ~200-500 training session documents (estimated)
- ~50-100 training plan documents (estimated)
- ~10-20 qualification documents (estimated)

Total: **400-700+ searchable training documents**

## Benefits of Complete Ingestion

1. **Session Search**: "Who attended Perfect Planning Calls training?"
2. **Progress Tracking**: "What trainings has John completed?"
3. **Trainer Info**: "Which sessions did Sarah train?"
4. **Timeline Queries**: "What trainings happened in December?"
5. **Qualification Lookup**: "What qualifications are required for X?"

## Quick Start

To begin ingesting the missing training data:

```bash
# 1. Update bubble_loader.py with new data types
# 2. Run the enhanced ingestion
python -m backend.ingest_all_training

# Or modify existing script to include all types
python -m backend.ingest
```

## Note on Data Volume
With only 5 records showing in the API test, the actual volume might be:
- Limited by API permissions
- Actually low volume
- Paginated (need to fetch with cursor)

Recommend checking with full API access to see true data volume.