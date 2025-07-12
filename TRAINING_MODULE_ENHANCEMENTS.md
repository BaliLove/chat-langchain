# Training Module Enhancements for Chat LangChain

## Overview
This document outlines enhancements to better support training module queries and improve the system's ability to answer questions about employee training progress, module effectiveness, and improvement recommendations.

## 1. Enhanced Prompt Templates

Since your prompts are loaded from LangSmith hub, you'll need to update them there. Here are the recommended modifications:

### Router Prompt Enhancement
Add training-specific routing logic to classify queries about:
- Training progress and completion status
- Module recommendations and improvements
- Compliance and certification tracking
- Training effectiveness analysis

### Response Prompt Enhancement
Include context about training data structure when generating responses:
```
When answering questions about training:
- Consider employee progress across multiple modules
- Look for patterns in assessment scores and feedback
- Identify gaps in training completion
- Suggest improvements based on feedback data
```

## 2. Custom Training Query Handler

Create a new file `backend/retrieval_graph/training_handler.py`:

```python
from typing import Dict, List, Optional
from langchain_core.documents import Document
from datetime import datetime, timedelta

class TrainingQueryHandler:
    """Specialized handler for training-related queries"""
    
    def analyze_employee_progress(self, employee_name: str, documents: List[Document]) -> Dict:
        """Analyze training progress for a specific employee"""
        progress_data = {
            "completed_modules": [],
            "pending_modules": [],
            "overdue_modules": [],
            "recent_assessments": [],
            "average_score": 0
        }
        
        for doc in documents:
            if doc.metadata.get("source_type") == "employee_training_plan":
                # Extract progress information
                if employee_name.lower() in doc.page_content.lower():
                    # Parse module completion status
                    pass
                    
        return progress_data
    
    def identify_training_gaps(self, documents: List[Document]) -> List[Dict]:
        """Identify gaps in training coverage across the organization"""
        gaps = []
        
        # Analyze training plans vs completions
        # Identify modules with low completion rates
        # Find employees missing critical training
        
        return gaps
    
    def suggest_module_improvements(self, module_name: str, documents: List[Document]) -> Dict:
        """Suggest improvements based on feedback and assessment data"""
        suggestions = {
            "content_updates": [],
            "delivery_improvements": [],
            "assessment_changes": [],
            "scheduling_recommendations": []
        }
        
        # Analyze feedback for the module
        # Look at assessment scores
        # Consider attendance patterns
        
        return suggestions
```

## 3. Enhanced Metadata Extraction

Update `backend/bubble_loader.py` to include more training-specific metadata:

```python
def _extract_metadata(self, record: Dict, data_type: str) -> Dict:
    """Extract metadata from record"""
    # ... existing code ...
    
    # Add training-specific metadata
    if data_type.startswith("training_"):
        metadata.update({
            "completion_status": record.get("completion_status"),
            "due_date": record.get("due_date") or record.get("deadline"),
            "department": record.get("department"),
            "role": record.get("role") or record.get("position"),
            "manager": record.get("manager") or record.get("supervisor"),
            "certification_required": record.get("certification_required", False)
        })
        
        # Calculate urgency for training items
        if metadata.get("due_date"):
            due_date = parse_date(metadata["due_date"])
            days_until_due = (due_date - datetime.now()).days
            metadata["urgency"] = "overdue" if days_until_due < 0 else "urgent" if days_until_due < 7 else "normal"
    
    return metadata
```

## 4. Training-Specific Search Queries

Add specialized query generation for training contexts:

```python
class TrainingQueryGenerator:
    """Generate optimized search queries for training data"""
    
    def generate_progress_queries(self, employee_name: str) -> List[str]:
        return [
            f'employee:"{employee_name}" AND source_type:employee_training_plan',
            f'employee:"{employee_name}" AND source_type:training_attendance',
            f'employee:"{employee_name}" AND source_type:training_assessment'
        ]
    
    def generate_module_analysis_queries(self, module_name: str) -> List[str]:
        return [
            f'module:"{module_name}" AND source_type:training_feedback',
            f'module:"{module_name}" AND source_type:training_assessment',
            f'training_module:"{module_name}" AND rating:<3'  # Low-rated sessions
        ]
```

## 5. Integration with Main Graph

Modify `backend/retrieval_graph/graph.py` to use the training handler:

```python
# Add to imports
from backend.retrieval_graph.training_handler import TrainingQueryHandler

# Add training-specific routing
def route_query(state: AgentState) -> Literal["create_research_plan", "ask_for_more_info", "respond_to_general_query", "handle_training_query"]:
    """Determine the next step based on the query classification."""
    _type = state.router["type"]
    
    # Check if query is training-related
    training_keywords = ["training", "module", "compliance", "certification", "progress", "assessment"]
    if any(keyword in state.messages[-1].content.lower() for keyword in training_keywords):
        return "handle_training_query"
    
    # ... existing routing logic ...
```

## 6. Sample Training Queries to Support

Your system should be able to answer:

1. **Progress Tracking**
   - "Show me John Smith's training progress"
   - "Which employees are behind on compliance training?"
   - "List all overdue training modules by department"

2. **Module Analysis**
   - "Which training modules have the lowest satisfaction scores?"
   - "What feedback have we received on the Safety Training module?"
   - "Identify duplicate or overlapping training content"

3. **Improvement Suggestions**
   - "How can we improve our onboarding training based on feedback?"
   - "Which modules need content updates based on assessment scores?"
   - "Suggest a training schedule for new sales employees"

4. **Compliance Reporting**
   - "Generate a compliance report for Q3"
   - "Which certifications expire this month?"
   - "Show employees who need to retake failed assessments"

## 7. Testing Your Implementation

Use the existing `test_training_data.py` script to verify:
- Data is being ingested correctly
- Queries return relevant results
- Duplicate detection works
- Progress tracking is accurate

## Next Steps

1. Update LangSmith prompts with training-specific instructions
2. Run ingestion to populate training data
3. Test with sample queries
4. Monitor and refine based on user feedback
5. Consider adding a training dashboard UI component