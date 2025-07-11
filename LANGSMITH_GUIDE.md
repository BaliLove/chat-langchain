# Complete LangSmith Guide: Datasets, Experiments, Annotation Queues & Prompts

## Table of Contents
1. [Current LangSmith Integration](#current-langsmith-integration)
2. [Working with Prompts](#working-with-prompts)
3. [Creating and Managing Datasets](#creating-and-managing-datasets)
4. [Running Experiments](#running-experiments)
5. [Setting Up Annotation Queues](#setting-up-annotation-queues)
6. [Advanced Evaluation Strategies](#advanced-evaluation-strategies)
7. [Venue/Event-Specific Use Cases](#venueevent-specific-use-cases)

---

## Current LangSmith Integration

Your system already has excellent LangSmith integration! Here's what's currently working:

### ✅ Automatic Tracing
```bash
# These environment variables enable full tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key
LANGCHAIN_PROJECT=your_project_name
```

### ✅ Feedback Collection
- Users can give 👍/👎 feedback on responses
- Feedback automatically sent to LangSmith for analysis
- Traces include user satisfaction metrics

### ✅ Prompt Management
Your system pulls prompts from LangSmith:
```python
# backend/retrieval_graph/prompts.py
client = Client()
ROUTER_SYSTEM_PROMPT = client.pull_prompt("langchain-ai/chat-langchain-router-prompt")
RESPONSE_SYSTEM_PROMPT = client.pull_prompt("langchain-ai/chat-langchain-response-prompt")
```

### ✅ Automated Evaluations
Your CI/CD runs evaluations on every commit:
```yaml
# .github/workflows/eval.yml
- name: Evaluate
  run: poetry run pytest backend/tests/evals
```

---

## Working with Prompts

### Accessing Your Prompts in LangSmith

1. **Navigate to Prompts Section** in LangSmith dashboard
2. **Search for your prompts** (they're in the `langchain-ai` organization):
   - `chat-langchain-router-prompt`
   - `chat-langchain-response-prompt`
   - `chat-langchain-research-plan-prompt`
   - `chat-langchain-generate-queries-prompt`
   - `chat-langchain-general-prompt`
   - `chat-langchain-more-info-prompt`

### Creating Custom Prompts for Your Venue Business

#### 1. Create Venue-Specific Router Prompt
```python
# In LangSmith, create a new prompt called "bali-venue-router-prompt"
"""
You are an AI assistant for a luxury venue booking platform in Bali.
Analyze user queries and classify them:

VENUE_INQUIRY: Questions about specific venues, amenities, locations
- "Tell me about Uluwatu villas"
- "What beachfront venues do you have?"
- "Which venues have wedding packages?"

EVENT_INQUIRY: Questions about events, planning, bookings
- "How do I book a wedding ceremony?"
- "What events are available this month?"
- "Can you help plan a corporate retreat?"

PRODUCT_INQUIRY: Questions about services, pricing, packages
- "What's included in the premium package?"
- "How much does venue rental cost?"
- "What catering options are available?"

GENERAL: General conversation or platform questions
- "How does your booking system work?"
- "What are your cancellation policies?"

For venue/event/product inquiries, route to research.
For general inquiries, provide direct response.

Respond in JSON format:
{
  "classification": "VENUE_INQUIRY|EVENT_INQUIRY|PRODUCT_INQUIRY|GENERAL",
  "needs_research": true|false,
  "reasoning": "Brief explanation of classification"
}
"""
```

#### 2. Create Venue Response Prompt
```python
# Create "bali-venue-response-prompt" in LangSmith
"""
You are an expert venue consultant for luxury Bali venues and events.

Context about venues and events:
{context}

User Question: {question}

Guidelines:
- Highlight unique features and amenities
- Mention specific locations (Uluwatu, Canggu, Seminyak, etc.)
- Include practical details (capacity, pricing ranges, availability)
- Suggest complementary services or venues
- Maintain an enthusiastic but professional tone
- Always end with a call-to-action for booking or more information

Provide a comprehensive, helpful response that showcases the beauty and luxury of Bali venues.
"""
```

#### 3. Update Your Code to Use Custom Prompts
```python
# backend/retrieval_graph/prompts.py
def get_venue_specific_prompts():
    """Get prompts optimized for venue/event queries."""
    return {
        "router": client.pull_prompt("your-org/bali-venue-router-prompt"),
        "response": client.pull_prompt("your-org/bali-venue-response-prompt"),
        "research_plan": client.pull_prompt("your-org/bali-venue-research-prompt")
    }

# Use environment variable to switch between prompt sets
USE_VENUE_PROMPTS = os.getenv("USE_VENUE_PROMPTS", "false").lower() == "true"

if USE_VENUE_PROMPTS:
    venue_prompts = get_venue_specific_prompts()
    ROUTER_SYSTEM_PROMPT = venue_prompts["router"].messages[0].prompt.template
    RESPONSE_SYSTEM_PROMPT = venue_prompts["response"].messages[0].prompt.template
```

---

## Creating and Managing Datasets

### Why Datasets Matter for Your Venue Business

Datasets help you evaluate how well your AI handles:
- Venue-specific questions ("Tell me about Uluwatu villas")
- Event planning queries ("Best venues for 50-person wedding")
- Pricing and availability questions
- Location-based searches

### Creating Your First Dataset

#### 1. Manual Dataset Creation (Recommended Start)

**In LangSmith Dashboard:**
1. Go to **Datasets & Experiments** → **New Dataset**
2. Name: `bali-venue-qa-dataset`
3. Description: `Questions and answers about Bali venues and events`

**Add Examples:**
```json
[
  {
    "inputs": {
      "question": "Tell me about Uluwatu villas with ocean views"
    },
    "outputs": {
      "answer": "Our Uluwatu villas offer stunning clifftop ocean views...",
      "sources": ["uluwatu_villas.json"],
      "venue_type": "villa",
      "location": "uluwatu"
    }
  },
  {
    "inputs": {
      "question": "What's the best venue for a 100-person wedding in Seminyak?"
    },
    "outputs": {
      "answer": "For a 100-person wedding in Seminyak, I recommend...",
      "sources": ["seminyak_venues.json"],
      "venue_type": "wedding_venue",
      "location": "seminyak",
      "capacity": 100
    }
  },
  {
    "inputs": {
      "question": "Do you have beachfront venues for corporate events?"
    },
    "outputs": {
      "answer": "Yes, we have several beachfront venues perfect for corporate events...",
      "sources": ["beachfront_venues.json"],
      "venue_type": "corporate",
      "location": "beachfront"
    }
  }
]
```

#### 2. Automated Dataset Creation from Production Data

```python
# Create a script to build datasets from your actual user queries
from langsmith import Client
import json

def create_dataset_from_traces():
    """Extract good examples from production traces."""
    client = Client()
    
    # Get traces with high user feedback
    runs = client.list_runs(
        project_name="your-project",
        filter="feedback.user_score > 0.8",  # High-rated responses
        limit=100
    )
    
    dataset_examples = []
    for run in runs:
        if run.inputs and run.outputs:
            example = {
                "inputs": run.inputs,
                "outputs": {
                    "answer": run.outputs.get("messages", [{}])[-1].get("content"),
                    "run_id": str(run.id)
                }
            }
            dataset_examples.append(example)
    
    # Create dataset
    dataset = client.create_dataset(
        dataset_name="production-venue-queries",
        description="High-quality examples from production"
    )
    
    client.create_examples(
        inputs=[ex["inputs"] for ex in dataset_examples],
        outputs=[ex["outputs"] for ex in dataset_examples],
        dataset_id=dataset.id
    )

# Run this weekly to continuously improve your dataset
create_dataset_from_traces()
```

#### 3. Venue-Specific Dataset Categories

Create specialized datasets for different query types:

**Dataset: `venue-discovery-queries`**
- "What venues are available in Uluwatu?"
- "Show me beach clubs in Canggu"
- "Which villas have infinity pools?"

**Dataset: `event-planning-queries`**
- "How do I plan a destination wedding in Bali?"
- "What's included in your event packages?"
- "Can you coordinate vendors for my event?"

**Dataset: `pricing-availability-queries`**
- "How much does it cost to rent Villa Semarapura?"
- "Is the Beach Club available on December 15th?"
- "What's the price difference between peak and off-season?"

---

## Running Experiments

### Setting Up Experiments for Your Venue System

#### 1. Model Comparison Experiment

Test different AI models on your venue queries:

```python
# scripts/run_venue_experiments.py
from langsmith import Client
from langsmith.evaluation import evaluate
import asyncio

client = Client()

async def run_model_comparison():
    """Compare different models on venue queries."""
    
    models_to_test = [
        "anthropic/claude-3-5-haiku-20241022",
        "openai/gpt-4o-mini", 
        "anthropic/claude-3-5-sonnet-20241022"
    ]
    
    for model in models_to_test:
        experiment_results = await evaluate(
            lambda inputs: run_venue_chat(inputs, model=model),
            data="bali-venue-qa-dataset",
            evaluators=[
                venue_accuracy_evaluator,
                source_citation_evaluator,
                response_helpfulness_evaluator
            ],
            experiment_prefix=f"venue-chat-{model.replace('/', '-')}"
        )
        
        print(f"Results for {model}:")
        print(f"- Venue Accuracy: {experiment_results.aggregate_score}")

asyncio.run(run_model_comparison())
```

#### 2. Prompt A/B Testing

Test different prompt variations:

```python
async def test_prompt_variations():
    """Test different prompt approaches for venue queries."""
    
    prompt_variants = {
        "standard": "langchain-ai/chat-langchain-response-prompt",
        "venue_optimized": "your-org/bali-venue-response-prompt", 
        "conversion_focused": "your-org/bali-venue-conversion-prompt"
    }
    
    for name, prompt_id in prompt_variants.items():
        experiment_results = await evaluate(
            lambda inputs: run_venue_chat(inputs, prompt=prompt_id),
            data="bali-venue-qa-dataset",
            evaluators=[
                venue_accuracy_evaluator,
                conversion_potential_evaluator,
                user_satisfaction_evaluator
            ],
            experiment_prefix=f"prompt-test-{name}"
        )
        
        print(f"Prompt '{name}' Results:")
        print(f"- Accuracy: {experiment_results.aggregate_score}")
```

#### 3. Bubble.io Data Integration Testing

Test how well your system uses Bubble.io data:

```python
async def test_bubble_integration():
    """Test retrieval and usage of Bubble.io venue data."""
    
    # Test with and without Bubble.io data
    configurations = [
        {"use_bubble_data": True, "bubble_priority": 0.8},
        {"use_bubble_data": True, "bubble_priority": 0.5},
        {"use_bubble_data": False}  # Control group
    ]
    
    for i, config in enumerate(configurations):
        experiment_results = await evaluate(
            lambda inputs: run_venue_chat(inputs, **config),
            data="bali-venue-qa-dataset",
            evaluators=[
                venue_detail_accuracy_evaluator,
                bubble_data_usage_evaluator,
                response_completeness_evaluator
            ],
            experiment_prefix=f"bubble-integration-test-{i+1}"
        )
```

#### 4. Custom Evaluators for Venue Queries

```python
# Custom evaluators for your venue business
def venue_accuracy_evaluator(run, example):
    """Evaluate if the response accurately describes venue features."""
    response = run.outputs["messages"][-1]["content"]
    expected_venue = example.outputs.get("venue_type")
    expected_location = example.outputs.get("location")
    
    # Check if response mentions correct venue type and location
    accuracy_score = 0
    if expected_venue and expected_venue.lower() in response.lower():
        accuracy_score += 0.5
    if expected_location and expected_location.lower() in response.lower():
        accuracy_score += 0.5
        
    return {"key": "venue_accuracy", "score": accuracy_score}

def conversion_potential_evaluator(run, example):
    """Evaluate if response encourages booking/inquiry."""
    response = run.outputs["messages"][-1]["content"].lower()
    
    conversion_signals = [
        "book now", "contact us", "reserve", "available", 
        "inquiry", "more information", "schedule", "visit"
    ]
    
    score = sum(1 for signal in conversion_signals if signal in response) / len(conversion_signals)
    return {"key": "conversion_potential", "score": min(score, 1.0)}

def bubble_data_usage_evaluator(run, example):
    """Evaluate if response uses Bubble.io data effectively."""
    documents = run.outputs.get("documents", [])
    bubble_sources = [doc for doc in documents if "bubble" in doc.metadata.get("source", "")]
    
    score = 1.0 if bubble_sources else 0.0
    return {"key": "bubble_data_usage", "score": score}
```

---

## Setting Up Annotation Queues

### Why Annotation Queues for Venue Business

Since you currently see "No annotation queues found", let's set them up! Annotation queues help you:
- Review AI responses for accuracy about your venues
- Collect expert feedback on event planning advice
- Ensure pricing and availability information is correct
- Build training data for future improvements

### Creating Your First Annotation Queue

#### 1. Manual Setup in LangSmith Dashboard

1. **Click "New Annotation Queue"** in the LangSmith interface
2. **Queue Name**: `venue-response-review`
3. **Description**: `Review AI responses about Bali venues for accuracy and helpfulness`

#### 2. Programmatic Queue Creation

```python
# scripts/setup_annotation_queues.py
from langsmith import Client

client = Client()

def create_venue_annotation_queues():
    """Create annotation queues for venue business."""
    
    # Queue 1: General venue responses
    venue_queue = client.create_annotation_queue(
        name="venue-response-accuracy",
        description="Review venue descriptions and recommendations for accuracy",
        instruction="""
        Please review this AI response about Bali venues and rate:
        
        1. Venue Information Accuracy (1-5): Are venue details correct?
        2. Helpfulness (1-5): How helpful is the response for planning?
        3. Conversion Potential (1-5): Does it encourage booking/inquiry?
        4. Missing Information: What important details are missing?
        
        Focus on factual accuracy about:
        - Venue locations and features
        - Capacity and amenities  
        - Pricing ranges (if mentioned)
        - Booking procedures
        """
    )
    
    # Queue 2: Event planning responses
    event_queue = client.create_annotation_queue(
        name="event-planning-quality",
        description="Review AI responses about event planning and coordination",
        instruction="""
        Evaluate this AI response about event planning:
        
        1. Planning Accuracy (1-5): Is the event advice practical and accurate?
        2. Venue Suitability (1-5): Are venue recommendations appropriate?
        3. Completeness (1-5): Does it cover key planning considerations?
        4. Actionability (1-5): Can the user take clear next steps?
        
        Note any:
        - Missing vendor information
        - Incorrect capacity recommendations
        - Unrealistic timeline suggestions
        """
    )
    
    # Queue 3: Pricing and availability
    pricing_queue = client.create_annotation_queue(
        name="pricing-availability-accuracy",
        description="Verify pricing and availability information accuracy",
        instruction="""
        Check this AI response for pricing/availability accuracy:
        
        1. Pricing Accuracy (1-5): Are mentioned prices current and correct?
        2. Availability Logic (1-5): Does availability info make sense?
        3. Transparency (1-5): Is pricing information clear and honest?
        4. Upselling Appropriateness (1-5): Are additional services suggested appropriately?
        
        Flag any:
        - Outdated pricing information
        - Availability conflicts
        - Missing seasonal pricing notes
        """
    )
    
    return {
        "venue_queue": venue_queue.id,
        "event_queue": event_queue.id,
        "pricing_queue": pricing_queue.id
    }

# Create the queues
queue_ids = create_venue_annotation_queues()
print("Created annotation queues:", queue_ids)
```

#### 3. Automatically Adding Runs to Queues

```python
# Add runs to annotation queues based on criteria
def add_runs_to_annotation_queues():
    """Automatically add relevant runs to annotation queues."""
    
    # Get recent runs with venue-related queries
    recent_runs = client.list_runs(
        project_name="your-project",
        limit=50,
        start_time=datetime.now() - timedelta(days=1)
    )
    
    for run in recent_runs:
        query = run.inputs.get("messages", [{}])[-1].get("content", "").lower()
        
        # Route to appropriate queue based on query type
        if any(word in query for word in ["venue", "villa", "location", "where"]):
            client.add_runs_to_annotation_queue(
                queue_id=queue_ids["venue_queue"],
                run_ids=[run.id]
            )
        elif any(word in query for word in ["event", "wedding", "party", "ceremony"]):
            client.add_runs_to_annotation_queue(
                queue_id=queue_ids["event_queue"], 
                run_ids=[run.id]
            )
        elif any(word in query for word in ["price", "cost", "book", "available"]):
            client.add_runs_to_annotation_queue(
                queue_id=queue_ids["pricing_queue"],
                run_ids=[run.id]
            )

# Run this daily to keep queues populated
add_runs_to_annotation_queues()
```

#### 4. Team Annotation Workflow

```python
# scripts/manage_annotation_workflow.py
def setup_annotation_workflow():
    """Set up annotation workflow for your team."""
    
    # Assign different team members to different queues
    team_assignments = {
        "venue_manager": "venue-response-accuracy",      # Venue expert
        "event_coordinator": "event-planning-quality",   # Event planning expert  
        "sales_manager": "pricing-availability-accuracy" # Pricing expert
    }
    
    # Send daily annotation tasks
    for role, queue_name in team_assignments.items():
        pending_annotations = client.list_annotation_queue_runs(
            queue_name=queue_name,
            status="pending"
        )
        
        if pending_annotations:
            send_notification(
                role=role,
                message=f"You have {len(pending_annotations)} venue responses to review in {queue_name}",
                queue_url=f"https://smith.langchain.com/annotation-queues/{queue_name}"
            )

def send_notification(role, message, queue_url):
    """Send notification to team member (implement with your notification system)."""
    # Could be Slack, email, etc.
    print(f"📧 {role}: {message}")
    print(f"🔗 Review here: {queue_url}")
```

---

## Advanced Evaluation Strategies

### Venue-Specific Evaluation Metrics

#### 1. Location Accuracy Evaluator
```python
def location_accuracy_evaluator(run, example):
    """Verify AI correctly identifies and describes locations."""
    response = run.outputs["messages"][-1]["content"]
    question = run.inputs["question"]
    
    # Extract mentioned locations
    bali_locations = ["uluwatu", "canggu", "seminyak", "ubud", "nusa dua", "jimbaran", "sanur"]
    mentioned_locations = [loc for loc in bali_locations if loc in response.lower()]
    
    # Check if mentioned locations are relevant to query
    query_locations = [loc for loc in bali_locations if loc in question.lower()]
    
    if query_locations:
        accuracy = len(set(mentioned_locations) & set(query_locations)) / len(query_locations)
    else:
        accuracy = 1.0 if not mentioned_locations else 0.5  # No specific location required
    
    return {"key": "location_accuracy", "score": accuracy}
```

#### 2. Venue Feature Completeness
```python
def venue_feature_completeness_evaluator(run, example):
    """Evaluate if response covers important venue features."""
    response = run.outputs["messages"][-1]["content"].lower()
    
    # Key features customers care about
    important_features = [
        "capacity", "guest", "people",           # Capacity info
        "ocean", "beach", "view", "pool",       # Scenic features  
        "wedding", "ceremony", "reception",      # Event suitability
        "catering", "food", "dining",           # Food services
        "accommodation", "stay", "rooms",        # Lodging
        "transport", "access", "location"        # Accessibility
    ]
    
    mentioned_features = sum(1 for feature in important_features if feature in response)
    completeness_score = mentioned_features / len(important_features)
    
    return {"key": "feature_completeness", "score": min(completeness_score, 1.0)}
```

#### 3. Business Impact Evaluator
```python
def business_impact_evaluator(run, example):
    """Evaluate if response drives business outcomes."""
    response = run.outputs["messages"][-1]["content"].lower()
    
    # Business-positive signals
    positive_signals = [
        "book", "reserve", "contact", "inquiry",    # Direct conversion
        "available", "schedule", "visit",           # Engagement
        "recommend", "perfect", "ideal",            # Positive sentiment
        "package", "deal", "offer"                  # Value proposition
    ]
    
    # Business-negative signals  
    negative_signals = [
        "not available", "fully booked", "cannot",  # Unavailability
        "expensive", "costly", "budget",            # Price concerns
        "difficult", "complicated", "problem"       # Friction
    ]
    
    positive_score = sum(1 for signal in positive_signals if signal in response)
    negative_score = sum(1 for signal in negative_signals if signal in response)
    
    # Calculate net business impact
    net_score = (positive_score - negative_score) / len(positive_signals)
    normalized_score = max(0, min(1, (net_score + 1) / 2))  # Normalize to 0-1
    
    return {"key": "business_impact", "score": normalized_score}
```

### Running Comprehensive Evaluations

```python
# scripts/comprehensive_venue_evaluation.py
async def run_comprehensive_evaluation():
    """Run a comprehensive evaluation of your venue chat system."""
    
    evaluation_results = await evaluate(
        target=lambda inputs: run_venue_chat_system(inputs),
        data="bali-venue-qa-dataset",
        evaluators=[
            # Accuracy evaluators
            venue_accuracy_evaluator,
            location_accuracy_evaluator, 
            venue_feature_completeness_evaluator,
            
            # Business evaluators
            business_impact_evaluator,
            conversion_potential_evaluator,
            
            # Technical evaluators  
            response_time_evaluator,
            source_citation_evaluator,
            bubble_data_usage_evaluator,
            
            # User experience evaluators
            response_helpfulness_evaluator,
            clarity_evaluator,
            tone_appropriateness_evaluator
        ],
        experiment_prefix="comprehensive-venue-eval"
    )
    
    # Generate business report
    generate_business_report(evaluation_results)

def generate_business_report(results):
    """Generate a business-focused evaluation report."""
    report = f"""
    🏨 VENUE CHAT SYSTEM EVALUATION REPORT
    =======================================
    
    📊 OVERALL PERFORMANCE
    - System Accuracy: {results.aggregate_score:.2%}
    - Business Impact Score: {results.scores.get('business_impact', 0):.2%}
    - Conversion Potential: {results.scores.get('conversion_potential', 0):.2%}
    
    🎯 VENUE-SPECIFIC METRICS
    - Location Accuracy: {results.scores.get('location_accuracy', 0):.2%}
    - Feature Completeness: {results.scores.get('feature_completeness', 0):.2%}
    - Bubble.io Data Usage: {results.scores.get('bubble_data_usage', 0):.2%}
    
    💡 RECOMMENDATIONS
    {generate_recommendations(results)}
    """
    
    print(report)
    
    # Save to file for sharing with team
    with open(f"venue_eval_report_{datetime.now().strftime('%Y%m%d')}.txt", "w") as f:
        f.write(report)

def generate_recommendations(results):
    """Generate specific recommendations based on evaluation results."""
    recommendations = []
    
    if results.scores.get('location_accuracy', 0) < 0.8:
        recommendations.append("- Improve location-specific training data")
        
    if results.scores.get('conversion_potential', 0) < 0.7:
        recommendations.append("- Enhance call-to-action phrases in responses")
        
    if results.scores.get('bubble_data_usage', 0) < 0.9:
        recommendations.append("- Increase Bubble.io data retrieval priority")
        
    return "\n".join(recommendations) if recommendations else "- System performing well across all metrics!"
```

---

## Venue/Event-Specific Use Cases

### 1. Seasonal Performance Monitoring

```python
def monitor_seasonal_performance():
    """Track how well the system handles seasonal queries."""
    
    # High season (June-August, December)
    # Low season (January-March, September-November)
    
    seasonal_datasets = {
        "high_season": "venue-queries-high-season",
        "low_season": "venue-queries-low-season",
        "wedding_season": "venue-queries-wedding-season"
    }
    
    for season, dataset_name in seasonal_datasets.items():
        results = await evaluate(
            target=venue_chat_system,
            data=dataset_name,
            evaluators=[
                pricing_accuracy_evaluator,
                availability_accuracy_evaluator,
                seasonal_recommendations_evaluator
            ],
            experiment_prefix=f"seasonal-performance-{season}"
        )
        
        print(f"{season.title()} Performance: {results.aggregate_score:.2%}")
```

### 2. Multi-Language Support Evaluation

```python
def evaluate_multilingual_support():
    """Evaluate AI performance in different languages."""
    
    # Create datasets in different languages
    languages = {
        "english": "venue-queries-english",
        "indonesian": "venue-queries-bahasa", 
        "chinese": "venue-queries-chinese",
        "japanese": "venue-queries-japanese"
    }
    
    for lang, dataset in languages.items():
        results = await evaluate(
            target=lambda inputs: venue_chat_system(inputs, language=lang),
            data=dataset,
            evaluators=[
                language_accuracy_evaluator,
                cultural_sensitivity_evaluator,
                venue_translation_accuracy_evaluator
            ],
            experiment_prefix=f"multilingual-{lang}"
        )
```

### 3. Competitive Analysis Evaluation

```python
def competitive_analysis_evaluation():
    """Compare your AI against competitor responses."""
    
    # Dataset with questions that might be asked about competitors
    competitive_queries = [
        "How do your venues compare to other Bali properties?",
        "Why should I choose your venues over others?",
        "What makes your service unique?",
        "Are your prices competitive?"
    ]
    
    results = await evaluate(
        target=venue_chat_system,
        data="competitive-comparison-queries",
        evaluators=[
            competitive_positioning_evaluator,
            value_proposition_clarity_evaluator,
            professional_tone_evaluator
        ],
        experiment_prefix="competitive-analysis"
    )
```

---

## Quick Start Checklist

### ✅ Immediate Actions (This Week)

1. **Create Your First Dataset**
   - [ ] Collect 20-50 venue-related Q&A pairs
   - [ ] Upload to LangSmith as "bali-venue-qa-v1"
   - [ ] Run baseline evaluation

2. **Set Up Annotation Queue**
   - [ ] Create "venue-response-review" queue
   - [ ] Add instruction template for reviewers
   - [ ] Add 10 recent runs for initial review

3. **Customize Key Prompts**
   - [ ] Create venue-specific router prompt
   - [ ] Create venue-optimized response prompt
   - [ ] Test new prompts against existing dataset

### 🎯 This Month Goals

4. **Expand Evaluation Coverage**
   - [ ] Add business impact evaluators
   - [ ] Set up automated daily evaluations  
   - [ ] Create weekly performance reports

5. **Team Integration**
   - [ ] Train team on annotation queues
   - [ ] Set up notification workflows
   - [ ] Establish review process

6. **Advanced Features**
   - [ ] Multi-language dataset creation
   - [ ] Seasonal performance monitoring
   - [ ] Competitive analysis evaluation

### 📈 Long-term Strategy (3+ Months)

7. **Continuous Improvement Loop**
   - [ ] Weekly dataset updates from production
   - [ ] Monthly prompt optimization cycles
   - [ ] Quarterly comprehensive evaluations

8. **Business Intelligence**
   - [ ] ROI tracking from AI interactions
   - [ ] Customer satisfaction correlation
   - [ ] Conversion rate optimization

This comprehensive LangSmith setup will help you continuously improve your venue chat system while maintaining high quality responses that drive bookings and customer satisfaction! 