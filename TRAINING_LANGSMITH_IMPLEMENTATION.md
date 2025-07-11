# Training Data LangSmith Implementation Guide

## Overview: Training Management AI System

Perfect choice! Training data is ideal for LangSmith testing because it has:
- ✅ **Clear business rules** (who needs what training when)
- ✅ **Structured data** (modules, sessions, attendance records)
- ✅ **Measurable outcomes** (compliance, efficiency)
- ✅ **Easy validation** (scheduling logic, duplicate detection)

---

## 1. Training Data Structure Design

### Bubble.io Training Data Schema

First, let's design your Bubble.io training data structure:

```json
// Training Modules
{
  "training_modules": [
    {
      "id": "tm_001",
      "title": "Fire Safety Training",
      "description": "Basic fire safety procedures and evacuation protocols",
      "duration_hours": 2,
      "category": "safety",
      "prerequisites": [],
      "validity_months": 12,
      "mandatory": true,
      "content_tags": ["fire", "safety", "evacuation", "procedures"]
    },
    {
      "id": "tm_002", 
      "title": "Emergency Response Procedures",
      "description": "How to respond to various emergency situations",
      "duration_hours": 3,
      "category": "safety",
      "prerequisites": ["tm_001"],
      "validity_months": 12,
      "mandatory": true,
      "content_tags": ["emergency", "response", "safety", "procedures"]
    }
  ]
}

// Training Sessions
{
  "training_sessions": [
    {
      "id": "ts_001",
      "module_id": "tm_001",
      "instructor": "Sarah Johnson",
      "date": "2024-01-15",
      "time": "09:00",
      "duration_hours": 2,
      "location": "Conference Room A",
      "max_attendees": 20,
      "status": "scheduled"
    }
  ]
}

// Employee Training Plans
{
  "employee_training_plans": [
    {
      "employee_id": "emp_001",
      "employee_name": "John Smith",
      "department": "Operations",
      "role": "Venue Manager",
      "required_modules": ["tm_001", "tm_002", "tm_003"],
      "completed_sessions": [
        {
          "module_id": "tm_001",
          "session_id": "ts_001", 
          "completion_date": "2024-01-15",
          "status": "completed",
          "score": 85
        }
      ],
      "next_due_date": "2024-02-15"
    }
  ]
}

// Training Attendance
{
  "training_attendance": [
    {
      "session_id": "ts_001",
      "employee_id": "emp_001",
      "attendance_status": "attended",
      "completion_status": "passed",
      "score": 85,
      "feedback": "Engaged participant, good understanding"
    }
  ]
}
```

---

## 2. Training-Specific Prompts

### Custom Router Prompt for Training Queries

```python
# Create in LangSmith: "training-management-router-prompt"
TRAINING_ROUTER_PROMPT = """
You are an AI assistant for employee training management.
Analyze user queries and classify them:

DUPLICATE_ANALYSIS: Questions about content overlap or redundancy
- "Review training modules for duplicate content"
- "Are there overlapping topics between modules?"
- "Which modules cover similar material?"

SCHEDULING_INQUIRY: Questions about who needs training when
- "Who needs training this week?"
- "Which employees are overdue for training?"
- "When should John Smith complete fire safety training?"

COMPLIANCE_CHECK: Questions about training requirements and status
- "Is everyone compliant with safety training?"
- "Which departments need mandatory training?"
- "Who hasn't completed required modules?"

CONTENT_REVIEW: Questions about training module content and quality
- "What topics are covered in fire safety training?"
- "How long is the emergency response module?"
- "What are the prerequisites for advanced training?"

GENERAL: General questions about training system or policies
- "How does the training system work?"
- "What happens if someone misses training?"

For all inquiries except GENERAL, set needs_research=true to search training data.

Respond in JSON format:
{
  "classification": "DUPLICATE_ANALYSIS|SCHEDULING_INQUIRY|COMPLIANCE_CHECK|CONTENT_REVIEW|GENERAL",
  "needs_research": true|false,
  "reasoning": "Brief explanation of classification"
}
"""
```

### Training Response Prompt

```python
# Create in LangSmith: "training-management-response-prompt"
TRAINING_RESPONSE_PROMPT = """
You are an expert training coordinator and compliance manager.

Training Data Context:
{context}

User Question: {question}

Guidelines for responses:

For DUPLICATE_ANALYSIS:
- Compare module content systematically
- Identify specific overlapping topics
- Suggest consolidation opportunities
- Provide actionable recommendations

For SCHEDULING_INQUIRY:
- List specific employees and due dates
- Consider prerequisite requirements
- Check instructor and room availability
- Provide concrete scheduling suggestions

For COMPLIANCE_CHECK:
- Give clear status updates
- Highlight any compliance risks
- Identify priority actions needed
- Include relevant deadlines

For CONTENT_REVIEW:
- Provide detailed module information
- Explain learning objectives
- Mention prerequisites and duration
- Suggest related or follow-up modules

Always include:
- Specific names, dates, and details when available
- Clear action items or next steps
- Compliance implications if relevant
- Contact information for booking/scheduling

Maintain a professional, helpful tone focused on training efficiency and compliance.
"""
```

---

## 3. Training-Specific Datasets

### Dataset 1: Duplicate Content Analysis

```json
// In LangSmith: "training-duplicate-analysis-dataset"
[
  {
    "inputs": {
      "question": "Review our fire safety and emergency response modules for duplicate content"
    },
    "outputs": {
      "answer": "After reviewing both modules, I found 30% content overlap in evacuation procedures and emergency contact protocols. I recommend consolidating the evacuation content into the fire safety module and focusing emergency response on incident-specific procedures.",
      "duplicates_found": true,
      "overlap_percentage": 30,
      "affected_modules": ["tm_001", "tm_002"],
      "recommendation": "consolidate_evacuation_content"
    }
  },
  {
    "inputs": {
      "question": "Are there overlapping topics between customer service and communication training?"
    },
    "outputs": {
      "answer": "Yes, both modules cover active listening (15 minutes each) and conflict resolution basics (20 minutes each). Consider creating a foundational communication module that both can reference.",
      "duplicates_found": true,
      "overlap_percentage": 25,
      "affected_modules": ["tm_005", "tm_006"],
      "recommendation": "create_foundation_module"
    }
  }
]
```

### Dataset 2: Training Scheduling

```json
// In LangSmith: "training-scheduling-dataset"
[
  {
    "inputs": {
      "question": "Who needs fire safety training this week?"
    },
    "outputs": {
      "answer": "3 employees need fire safety training this week: John Smith (due Jan 20), Maria Garcia (due Jan 22), and David Chen (overdue since Jan 18). I recommend scheduling them for the Thursday 2PM session in Conference Room A.",
      "employees_due": [
        {"name": "John Smith", "due_date": "2024-01-20", "status": "upcoming"},
        {"name": "Maria Garcia", "due_date": "2024-01-22", "status": "upcoming"},
        {"name": "David Chen", "due_date": "2024-01-18", "status": "overdue"}
      ],
      "recommended_session": "Thursday 2PM, Conference Room A",
      "urgency": "high"
    }
  },
  {
    "inputs": {
      "question": "When should new hire Sarah Wilson complete her mandatory training?"
    },
    "outputs": {
      "answer": "Sarah Wilson should complete her mandatory training within 30 days of her start date (Feb 1). Recommended schedule: Fire Safety (Feb 5), Customer Service (Feb 8), and Emergency Response (Feb 12). This ensures compliance and proper prerequisite order.",
      "employee": "Sarah Wilson",
      "start_date": "2024-02-01",
      "compliance_deadline": "2024-03-02",
      "recommended_schedule": [
        {"module": "Fire Safety", "date": "2024-02-05"},
        {"module": "Customer Service", "date": "2024-02-08"}, 
        {"module": "Emergency Response", "date": "2024-02-12"}
      ]
    }
  }
]
```

### Dataset 3: Compliance Checking

```json
// In LangSmith: "training-compliance-dataset"
[
  {
    "inputs": {
      "question": "Which employees in Operations department are not compliant with mandatory training?"
    },
    "outputs": {
      "answer": "2 Operations employees are non-compliant: Mike Johnson (missing Emergency Response, due 2 weeks ago) and Lisa Chen (Fire Safety expired, needs renewal). Both should be scheduled for training immediately to maintain compliance.",
      "non_compliant_employees": [
        {"name": "Mike Johnson", "missing": "Emergency Response", "days_overdue": 14},
        {"name": "Lisa Chen", "missing": "Fire Safety", "status": "expired"}
      ],
      "department": "Operations",
      "compliance_rate": "85%",
      "action_required": "immediate_scheduling"
    }
  }
]
```

---

## 4. Custom Evaluators for Training Data

### Duplicate Detection Accuracy Evaluator

```python
def duplicate_detection_evaluator(run, example):
    """Evaluate accuracy of duplicate content detection."""
    response = run.outputs["messages"][-1]["content"].lower()
    expected_duplicates = example.outputs.get("duplicates_found", False)
    expected_modules = set(example.outputs.get("affected_modules", []))
    
    # Check if AI correctly identified duplicates
    found_duplicates = any(word in response for word in ["duplicate", "overlap", "similar", "redundant"])
    
    # Check if correct modules were mentioned
    mentioned_modules = set()
    for module in expected_modules:
        if module.lower() in response:
            mentioned_modules.add(module)
    
    # Calculate accuracy
    duplicate_accuracy = 1.0 if found_duplicates == expected_duplicates else 0.0
    module_accuracy = len(mentioned_modules & expected_modules) / len(expected_modules) if expected_modules else 1.0
    
    overall_score = (duplicate_accuracy + module_accuracy) / 2
    return {"key": "duplicate_detection_accuracy", "score": overall_score}

def scheduling_accuracy_evaluator(run, example):
    """Evaluate accuracy of training scheduling recommendations."""
    response = run.outputs["messages"][-1]["content"]
    expected_employees = {emp["name"] for emp in example.outputs.get("employees_due", [])}
    
    # Check if correct employees were mentioned
    mentioned_employees = set()
    for emp in expected_employees:
        if emp.lower() in response.lower():
            mentioned_employees.add(emp)
    
    # Check if urgency was appropriately communicated
    expected_urgency = example.outputs.get("urgency", "normal")
    urgency_words = {"high": ["urgent", "immediate", "overdue"], "normal": ["schedule", "plan"]}
    urgency_communicated = any(word in response.lower() for word in urgency_words.get(expected_urgency, []))
    
    employee_accuracy = len(mentioned_employees) / len(expected_employees) if expected_employees else 1.0
    urgency_accuracy = 1.0 if urgency_communicated else 0.0
    
    overall_score = (employee_accuracy + urgency_accuracy) / 2
    return {"key": "scheduling_accuracy", "score": overall_score}

def compliance_reporting_evaluator(run, example):
    """Evaluate accuracy of compliance status reporting."""
    response = run.outputs["messages"][-1]["content"]
    expected_non_compliant = example.outputs.get("non_compliant_employees", [])
    expected_rate = example.outputs.get("compliance_rate", "")
    
    # Check if non-compliant employees were identified
    identified_employees = 0
    for emp in expected_non_compliant:
        if emp["name"].lower() in response.lower():
            identified_employees += 1
    
    # Check if compliance rate was mentioned
    rate_mentioned = expected_rate.replace("%", "") in response if expected_rate else False
    
    employee_score = identified_employees / len(expected_non_compliant) if expected_non_compliant else 1.0
    rate_score = 1.0 if rate_mentioned else 0.0
    
    overall_score = (employee_score + rate_score) / 2
    return {"key": "compliance_reporting_accuracy", "score": overall_score}

def actionability_evaluator(run, example):
    """Evaluate if response provides clear, actionable next steps."""
    response = run.outputs["messages"][-1]["content"].lower()
    
    action_words = [
        "schedule", "book", "contact", "complete", "register",
        "recommend", "should", "need to", "must", "immediately"
    ]
    
    action_score = sum(1 for word in action_words if word in response) / len(action_words)
    return {"key": "actionability", "score": min(action_score, 1.0)}
```

---

## 5. Training Data Loader for Bubble.io

### Enhanced Bubble.io Loader for Training Data

```python
# backend/training_loader.py
import os
import requests
from typing import List, Dict, Any
from langchain_core.documents import Document
from datetime import datetime, timedelta

class BubbleTrainingLoader:
    """Load training data from Bubble.io for AI analysis."""
    
    def __init__(self):
        self.base_url = os.getenv("BUBBLE_APP_URL")
        self.api_token = os.getenv("BUBBLE_API_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def load_training_modules(self) -> List[Document]:
        """Load training module data."""
        response = requests.get(f"{self.base_url}/api/1.1/obj/training_modules", headers=self.headers)
        modules = response.json().get("response", {}).get("results", [])
        
        documents = []
        for module in modules:
            content = f"""
            Training Module: {module.get('title', 'Unknown')}
            Category: {module.get('category', 'Unknown')}
            Duration: {module.get('duration_hours', 0)} hours
            Description: {module.get('description', 'No description')}
            Prerequisites: {', '.join(module.get('prerequisites', []))}
            Mandatory: {'Yes' if module.get('mandatory') else 'No'}
            Validity: {module.get('validity_months', 0)} months
            Content Tags: {', '.join(module.get('content_tags', []))}
            """
            
            doc = Document(
                page_content=content,
                metadata={
                    "type": "training_module",
                    "module_id": module.get("id"),
                    "title": module.get("title"),
                    "category": module.get("category"),
                    "duration_hours": module.get("duration_hours"),
                    "mandatory": module.get("mandatory"),
                    "content_tags": module.get("content_tags", [])
                }
            )
            documents.append(doc)
        
        return documents
    
    def load_training_sessions(self) -> List[Document]:
        """Load training session schedules."""
        response = requests.get(f"{self.base_url}/api/1.1/obj/training_sessions", headers=self.headers)
        sessions = response.json().get("response", {}).get("results", [])
        
        documents = []
        for session in sessions:
            content = f"""
            Training Session: {session.get('module_id', 'Unknown Module')}
            Date: {session.get('date', 'TBD')}
            Time: {session.get('time', 'TBD')}
            Instructor: {session.get('instructor', 'TBD')}
            Location: {session.get('location', 'TBD')}
            Max Attendees: {session.get('max_attendees', 0)}
            Status: {session.get('status', 'Unknown')}
            """
            
            doc = Document(
                page_content=content,
                metadata={
                    "type": "training_session",
                    "session_id": session.get("id"),
                    "module_id": session.get("module_id"),
                    "date": session.get("date"),
                    "instructor": session.get("instructor"),
                    "status": session.get("status")
                }
            )
            documents.append(doc)
        
        return documents
    
    def load_employee_training_plans(self) -> List[Document]:
        """Load employee training plans and compliance status."""
        response = requests.get(f"{self.base_url}/api/1.1/obj/employee_training_plans", headers=self.headers)
        plans = response.json().get("response", {}).get("results", [])
        
        documents = []
        for plan in plans:
            completed_modules = [comp.get("module_id") for comp in plan.get("completed_sessions", [])]
            required_modules = plan.get("required_modules", [])
            missing_modules = [mod for mod in required_modules if mod not in completed_modules]
            
            content = f"""
            Employee: {plan.get('employee_name', 'Unknown')}
            Department: {plan.get('department', 'Unknown')}
            Role: {plan.get('role', 'Unknown')}
            Required Modules: {', '.join(required_modules)}
            Completed Modules: {', '.join(completed_modules)}
            Missing Modules: {', '.join(missing_modules)}
            Next Due Date: {plan.get('next_due_date', 'Not set')}
            Compliance Status: {'Compliant' if not missing_modules else 'Non-compliant'}
            """
            
            doc = Document(
                page_content=content,
                metadata={
                    "type": "employee_training_plan",
                    "employee_id": plan.get("employee_id"),
                    "employee_name": plan.get("employee_name"),
                    "department": plan.get("department"),
                    "missing_modules": missing_modules,
                    "compliance_status": "compliant" if not missing_modules else "non_compliant",
                    "next_due_date": plan.get("next_due_date")
                }
            )
            documents.append(doc)
        
        return documents
    
    def load_all_training_data(self) -> List[Document]:
        """Load all training-related data."""
        all_docs = []
        all_docs.extend(self.load_training_modules())
        all_docs.extend(self.load_training_sessions())
        all_docs.extend(self.load_employee_training_plans())
        return all_docs

# Integration with existing ingest.py
def load_training_data() -> List[Document]:
    """Load training data from Bubble.io."""
    try:
        loader = BubbleTrainingLoader()
        return loader.load_all_training_data()
    except Exception as e:
        print(f"Error loading training data: {e}")
        return []

# Add to backend/ingest.py
def ingest_docs():
    # ... existing code ...
    
    # Add training data
    docs_from_training = load_training_data()
    logger.info(f"Loaded {len(docs_from_training)} docs from training data")
    
    # Include in document list
    all_docs = docs_from_documentation + docs_from_api + docs_from_langsmith + docs_from_langgraph + docs_from_bubble + docs_from_training
```

---

## 6. Training Annotation Queues

### Setting Up Training-Specific Annotation Queues

```python
# scripts/setup_training_annotation_queues.py
from langsmith import Client

def create_training_annotation_queues():
    """Create annotation queues for training management."""
    client = Client()
    
    # Queue 1: Duplicate Content Analysis
    duplicate_queue = client.create_annotation_queue(
        name="training-duplicate-analysis",
        description="Review AI analysis of duplicate training content",
        instruction="""
        Review this AI analysis of training content duplication:
        
        Rate on scale 1-5:
        1. Duplicate Detection Accuracy: Did AI correctly identify duplicates?
        2. Analysis Quality: How thorough was the content comparison?
        3. Recommendations: Are suggested consolidations practical?
        4. Business Value: Will this analysis save time/resources?
        
        Specifically check:
        - Are identified duplicates actually duplicates?
        - Did AI miss any obvious overlaps?
        - Are recommendations feasible to implement?
        - Is the business impact clearly explained?
        """
    )
    
    # Queue 2: Training Scheduling
    scheduling_queue = client.create_annotation_queue(
        name="training-scheduling-accuracy",
        description="Verify AI training scheduling recommendations", 
        instruction="""
        Verify this AI training scheduling recommendation:
        
        Rate on scale 1-5:
        1. Employee Identification: Were correct employees identified?
        2. Date Accuracy: Are due dates and deadlines correct?
        3. Prerequisite Logic: Does scheduling respect prerequisites?
        4. Resource Availability: Are room/instructor conflicts considered?
        
        Check for:
        - Missing employees who need training
        - Incorrect due dates or compliance deadlines
        - Scheduling conflicts or capacity issues
        - Clear next steps for booking
        """
    )
    
    # Queue 3: Compliance Reporting
    compliance_queue = client.create_annotation_queue(
        name="training-compliance-review",
        description="Review AI compliance status reports",
        instruction="""
        Review this AI training compliance analysis:
        
        Rate on scale 1-5:
        1. Compliance Accuracy: Is the compliance status correct?
        2. Risk Assessment: Are compliance risks properly identified?
        3. Priority Setting: Are urgent cases flagged appropriately?
        4. Action Clarity: Are next steps clear and actionable?
        
        Verify:
        - All non-compliant employees are identified
        - Compliance percentages are accurate
        - Risk levels are appropriate
        - Recommended actions are specific and timely
        """
    )
    
    return {
        "duplicate_queue": duplicate_queue.id,
        "scheduling_queue": scheduling_queue.id,
        "compliance_queue": compliance_queue.id
    }
```

---

## 7. Training Experiments

### Experiment 1: Duplicate Detection Models

```python
# scripts/training_experiments.py
from langsmith.evaluation import evaluate
import asyncio

async def test_duplicate_detection_models():
    """Test different models for training content duplicate detection."""
    
    models = [
        "anthropic/claude-3-5-haiku-20241022",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-5-sonnet-20241022"
    ]
    
    for model in models:
        results = await evaluate(
            target=lambda inputs: analyze_training_duplicates(inputs, model=model),
            data="training-duplicate-analysis-dataset",
            evaluators=[
                duplicate_detection_evaluator,
                actionability_evaluator,
                business_value_evaluator
            ],
            experiment_prefix=f"duplicate-detection-{model.replace('/', '-')}"
        )
        
        print(f"Model {model} Results:")
        print(f"- Duplicate Detection: {results.scores.get('duplicate_detection_accuracy', 0):.2%}")
        print(f"- Actionability: {results.scores.get('actionability', 0):.2%}")

async def test_scheduling_approaches():
    """Test different approaches to training scheduling."""
    
    approaches = {
        "deadline_focused": "Prioritize employees closest to deadlines",
        "department_grouped": "Group scheduling by department", 
        "prerequisite_optimized": "Optimize for prerequisite chains"
    }
    
    for approach, description in approaches.items():
        results = await evaluate(
            target=lambda inputs: schedule_training(inputs, approach=approach),
            data="training-scheduling-dataset",
            evaluators=[
                scheduling_accuracy_evaluator,
                compliance_impact_evaluator,
                efficiency_evaluator
            ],
            experiment_prefix=f"scheduling-{approach}"
        )
        
        print(f"Approach '{approach}' Results:")
        print(f"- Scheduling Accuracy: {results.scores.get('scheduling_accuracy', 0):.2%}")
```

---

## 8. Quick Implementation Plan

### Week 1: Setup & Basic Testing
1. **Create Bubble.io Training Schema**
   - [ ] Set up training_modules table
   - [ ] Set up training_sessions table  
   - [ ] Set up employee_training_plans table
   - [ ] Add sample data (10-15 records each)

2. **Create First Dataset**
   - [ ] Build "training-duplicate-analysis-dataset" with 10 examples
   - [ ] Test duplicate detection manually first
   - [ ] Upload to LangSmith

3. **Set Up Basic Annotation Queue**
   - [ ] Create "training-duplicate-analysis" queue
   - [ ] Add instruction template
   - [ ] Test with 5 sample responses

### Week 2: Expand & Evaluate
4. **Add More Datasets**
   - [ ] "training-scheduling-dataset" (15 examples)
   - [ ] "training-compliance-dataset" (10 examples)
   - [ ] Test each manually before uploading

5. **Implement Custom Evaluators**
   - [ ] duplicate_detection_evaluator
   - [ ] scheduling_accuracy_evaluator
   - [ ] compliance_reporting_evaluator

6. **Run First Experiments**
   - [ ] Compare 2-3 models on duplicate detection
   - [ ] Test scheduling accuracy
   - [ ] Generate first evaluation report

### Week 3: Production Integration
7. **Integrate with Chat System**
   - [ ] Add training data loader to ingest.py
   - [ ] Update prompts for training queries
   - [ ] Test end-to-end workflow

8. **Set Up Automation**
   - [ ] Daily annotation queue population
   - [ ] Weekly evaluation runs
   - [ ] Monthly performance reports

This training data approach will give you concrete, measurable results and clear business value - perfect for demonstrating LangSmith's capabilities! 