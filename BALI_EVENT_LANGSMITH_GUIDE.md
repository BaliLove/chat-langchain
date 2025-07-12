# LangSmith for Bali Event Planning Business

Based on your actual production data from Bali.Love, here's a realistic LangSmith implementation guide for your event planning business.

## Your Current Data Structure

### ✅ **Production Data Types** (Confirmed)
- **Events** - Wedding planning, corporate events, celebrations
- **Venues** - Renaissance Hotel, Stone Villa Uluwatu, etc.
- **Products** - Services like "Painting Souvenir on Canvas - Platinum"
- **Bookings** - Client reservations and scheduling
- **Comments** - Client feedback and internal notes
- **Users** - Team members and clients
- **Teams** - Internal organization
- **Clients** - Customer management
- **Payments** - Financial transactions

## Realistic Query Categories for Your Business

### 1. **Venue Recommendation Queries**
```
"Find beachfront venues for a 150-person wedding in Uluwatu"
"Which venues can accommodate both ceremony and reception?"
"Compare venue pricing for corporate events vs weddings"
"What venues are available for next month?"
```

### 2. **Service & Product Queries**
```
"What photography packages include drone footage?"
"Compare catering options for vegan wedding menus"
"Which decoration services work best with outdoor venues?"
"Find all-inclusive packages under $50,000"
```

### 3. **Event Planning Coordination**
```
"List all vendors needed for a traditional Balinese ceremony"
"What's the timeline for planning a 6-month advance wedding?"
"Which services require advance booking during peak season?"
```

### 4. **Duplicate Detection Scenarios**
```
"Review venue listings for duplicate or overlapping descriptions"
"Check for similar product offerings that could be consolidated"
"Identify redundant services across different packages"
```

### 5. **Client Management Queries**
```
"Show all pending bookings for this quarter"
"Which clients need follow-up on payment schedules?"
"Generate inquiry reports for potential wedding bookings"
```

## LangSmith Datasets for Your Business

### Dataset 1: **Venue Discovery & Recommendations**
**Purpose**: Test venue matching based on client requirements

**Sample Questions & Expected Outputs**:
```json
[
  {
    "input": "I need a beachfront venue for 80 guests with catering facilities",
    "expected_output": "Based on your requirements, I recommend Stone Villa Uluwatu for its beachfront location and capacity for 80 guests. The venue includes catering facilities and offers stunning ocean views perfect for ceremonies.",
    "reference_venues": ["Stone Villa Uluwatu"]
  },
  {
    "input": "What venues work best for traditional Balinese wedding ceremonies?",
    "expected_output": "For traditional Balinese ceremonies, I recommend venues that can accommodate cultural requirements...",
    "reference_venues": ["venue_ids_from_your_data"]
  }
]
```

### Dataset 2: **Service Integration & Package Planning**
**Purpose**: Test ability to coordinate multiple services

**Sample Scenarios**:
```json
[
  {
    "input": "Plan a complete wedding package with photography, catering, and decoration",
    "expected_services": ["photography", "catering", "decoration"],
    "budget_consideration": true
  }
]
```

### Dataset 3: **Duplicate Content Detection**
**Purpose**: Identify overlapping venue descriptions or service offerings

**Sample Cases**:
```json
[
  {
    "venue_1": "Renaissance Hotel description...",
    "venue_2": "Another hotel with similar amenities...",
    "expected_similarity": 0.3,
    "action_needed": "consolidate_descriptions"
  }
]
```

### Dataset 4: **Client Inquiry Handling**
**Purpose**: Test proper response to client questions

**Sample Inquiries**:
```json
[
  {
    "inquiry": "What's included in your platinum wedding package?",
    "expected_components": ["Painting Souvenir on Canvas - Platinum", "other_services"],
    "should_include_pricing": false,
    "follow_up_required": true
  }
]
```

## Custom Evaluators for Event Planning

### 1. **Venue Matching Accuracy Evaluator**
```python
def venue_matching_evaluator(run, example):
    """Evaluate if recommended venues match client requirements"""
    predicted_venues = extract_venue_recommendations(run.outputs["output"])
    required_features = example.inputs["requirements"]
    
    accuracy_score = calculate_venue_feature_match(
        predicted_venues, 
        required_features
    )
    
    return EvaluationResult(
        key="venue_matching_accuracy",
        score=accuracy_score,
        comment=f"Venue recommendations matched {accuracy_score:.1%} of requirements"
    )
```

### 2. **Service Completeness Evaluator**
```python
def service_completeness_evaluator(run, example):
    """Check if all necessary services are included in event planning"""
    recommended_services = extract_services(run.outputs["output"])
    event_type = example.inputs["event_type"]
    
    required_services = get_required_services_for_event_type(event_type)
    completeness = len(set(recommended_services) & set(required_services)) / len(required_services)
    
    return EvaluationResult(
        key="service_completeness",
        score=completeness,
        comment=f"Covered {completeness:.1%} of essential services"
    )
```

### 3. **Budget Appropriateness Evaluator**
```python
def budget_appropriateness_evaluator(run, example):
    """Ensure recommendations fit within client budget"""
    recommended_total = calculate_package_cost(run.outputs["output"])
    client_budget = example.inputs.get("budget")
    
    if not client_budget:
        return EvaluationResult(key="budget_appropriateness", score=1.0)
    
    budget_ratio = recommended_total / client_budget
    score = 1.0 if budget_ratio <= 1.0 else max(0.0, 2.0 - budget_ratio)
    
    return EvaluationResult(
        key="budget_appropriateness",
        score=score,
        comment=f"Recommended total: ${recommended_total:,.0f} vs Budget: ${client_budget:,.0f}"
    )
```

### 4. **Cultural Sensitivity Evaluator**
```python
def cultural_sensitivity_evaluator(run, example):
    """Ensure recommendations respect Balinese culture and traditions"""
    response = run.outputs["output"].lower()
    event_type = example.inputs.get("event_type", "")
    
    cultural_keywords = ["traditional", "balinese", "ceremony", "blessing", "temple"]
    sensitivity_indicators = ["respect", "cultural", "appropriate", "traditional"]
    
    if "balinese" in event_type.lower() or "traditional" in event_type.lower():
        cultural_mentions = sum(1 for keyword in cultural_keywords if keyword in response)
        sensitivity_mentions = sum(1 for indicator in sensitivity_indicators if indicator in response)
        
        score = min(1.0, (cultural_mentions + sensitivity_mentions) / 3)
    else:
        score = 1.0  # Not applicable for non-cultural events
    
    return EvaluationResult(
        key="cultural_sensitivity",
        score=score,
        comment=f"Cultural awareness score for {event_type}"
    )
```

## Annotation Queues for Event Planning

### 1. **Venue Recommendation Review Queue**
**Purpose**: Review venue suggestions for accuracy and completeness
**Assigned to**: Senior event planners
**Review criteria**:
- Venue capacity matches requirements
- Location appropriateness 
- Amenity completeness
- Pricing accuracy

### 2. **Service Package Review Queue**
**Purpose**: Validate service combinations and packages
**Assigned to**: Service coordinators
**Review criteria**:
- Service compatibility
- Timeline feasibility
- Vendor availability
- Cost accuracy

### 3. **Cultural Events Review Queue**
**Purpose**: Ensure cultural appropriateness for traditional ceremonies
**Assigned to**: Cultural consultants
**Review criteria**:
- Cultural accuracy
- Traditional protocol adherence
- Venue suitability for ceremonies
- Vendor cultural competency

## Implementation Roadmap

### Week 1: Data Foundation
- ✅ Bubble.io integration working
- 🔄 Fix database connection for sync management
- 📊 Create first venue recommendation dataset (20 examples)
- 🧪 Test basic venue matching queries

### Week 2: Core Evaluators
- 🧮 Implement venue matching evaluator
- 💰 Add budget appropriateness checking
- 🏷️ Set up service completeness validation
- 📝 Create annotation queue for venue reviews

### Week 3: Advanced Features
- 🎭 Add cultural sensitivity evaluator
- 🔄 Implement duplicate detection for venues/services
- 📊 Expand datasets to 50+ examples per category
- 🤝 Train team on LangSmith annotation interface

### Week 4: Production Monitoring
- 📈 Set up production tracing for live inquiries
- 🚨 Configure alerts for low-scoring responses
- 📊 Create executive dashboard for query performance
- 🎯 Optimize based on real client interaction data

## Next Steps

1. **Fix Database Connection**: Resolve the Supabase connection issue for proper sync management
2. **Start Small**: Begin with 10-15 venue recommendation examples from your actual data
3. **Focus on Real Scenarios**: Use actual client inquiries from your booking system
4. **Iterate Based on Results**: Adjust evaluators based on what matters most to your business

This approach leverages your actual Bali event planning data instead of artificial training scenarios, making it immediately useful for your business! 