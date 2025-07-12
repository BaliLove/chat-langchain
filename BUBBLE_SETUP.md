# Bubble.io Training Data Setup Guide

## Step 1: Configure Environment Variables

Add these to your `.env` file or environment:

```bash
# Bubble.io Configuration
BUBBLE_APP_URL=https://your-app-name.bubbleapps.io/version-test/api/1.1/obj
BUBBLE_API_TOKEN=your_bubble_api_token_here
BUBBLE_BATCH_SIZE=100
BUBBLE_MAX_CONTENT_LENGTH=10000

# Database (use your existing RECORD_MANAGER_DB_URL)
RECORD_MANAGER_DB_URL=your_existing_db_url
```

## Step 2: Get Your Bubble.io API Credentials

1. Go to your Bubble.io app → Settings → API
2. Enable "Data API" 
3. Copy your API token
4. Your API URL format: `https://[your-app].bubbleapps.io/version-test/api/1.1/obj`

## Step 3: Training Data Types Expected

The system will look for these data types in your Bubble.io app:

### Core Training Data
- **training_module** - Course content and structure
- **training_session** - Scheduled training sessions
- **employee_training_plan** - Individual employee training requirements
- **training_attendance** - Session attendance records

### Assessment & Feedback
- **training_assessment** - Test scores and evaluations  
- **training_feedback** - Session feedback and ratings

## Step 4: Test Your Connection

Run this command to test your Bubble.io connection:

```bash
python -c "
from backend.bubble_loader import load_bubble_data
docs = load_bubble_data()
print(f'Successfully loaded {len(docs)} training documents')

if docs:
    # Show what data types you have
    data_types = {}
    for doc in docs:
        dt = doc.metadata.get('data_type', 'unknown')
        data_types[dt] = data_types.get(dt, 0) + 1
    
    print('\\nTraining data found:')
    for data_type, count in data_types.items():
        print(f'  {data_type}: {count} records')
        
    # Show sample content
    print('\\nSample training content:')
    for doc in docs[:2]:
        print(f'\\nType: {doc.metadata.get(\"data_type\")}')
        print(f'Content: {doc.page_content[:150]}...')
"
```

## Step 5: Common Bubble.io Field Names

The loader is flexible and looks for various field name patterns:

### Training Modules
- `title`, `name`, `module_name`
- `description`, `content`, `overview`
- `learning_objectives`, `objectives`
- `duration`, `estimated_duration`
- `category`, `training_category`

### Training Sessions  
- `session_name`, `title`, `name`
- `instructor`, `trainer`
- `scheduled_date`, `date`
- `location`, `venue`

### Employee Plans
- `employee_name`, `employee`
- `department`, `team`
- `required_modules`, `training_modules`
- `completion_deadline`, `deadline`

### Attendance
- `employee_name`, `employee`
- `training_session`, `session`
- `attendance_status`, `status`
- `completion_date`, `attended_date`

## Step 6: Next Steps

Once your connection works, you can:

1. **Create LangSmith Datasets** based on your real training data
2. **Set up Annotation Queues** for training content review
3. **Build Custom Evaluators** for training-specific queries
4. **Test Duplicate Detection** on your actual training modules

## Troubleshooting

### No Data Found
- Check your API token and URL
- Verify your Bubble.io app has the expected data types
- Ensure API permissions are enabled

### Connection Errors
- Confirm your app URL format matches Bubble.io's API structure
- Check if you need `/version-test/` or `/version-live/` in the URL
- Verify network connectivity

### Data Type Not Found (404)
- The data type doesn't exist in your Bubble.io app yet
- Create the data type in Bubble.io first, then retry
- Check data type naming matches what you've set up 