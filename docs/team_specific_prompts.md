# Team-Specific Prompts for Bali Love Internal Users

## Overview
Since all users are internal team members, these prompts are designed to enhance operational efficiency and support daily workflows for each team. The existing 6 prompts handle general conversation flow - these additional prompts provide specialized assistance for team-specific tasks.

## Existing Prompts (Already Implemented)
1. Router System Prompt - Query classification
2. Generate Queries Prompt - Search query generation  
3. More Info Prompt - Clarification requests
4. Research Plan Prompt - Complex query planning
5. General Prompt - Conversational responses
6. Response Prompt - Final answer generation

## Team-Specific Prompt Recommendations

### 1. REVENUE TEAM PROMPTS

#### A. Sales Pipeline Assistant
**ID**: `bali-love-revenue-pipeline-prompt`
**Priority**: HIGH

**Purpose**: Help Revenue team track leads, conversions, and sales opportunities.

**Use Cases**:
- "Show me all leads from last month that haven't been contacted"
- "Which venues have the highest conversion rate?"
- "What's our pipeline value for Q3 weddings?"
- "List high-value leads needing follow-up this week"

**Key Features**:
- Lead scoring and prioritization
- Conversion tracking by vendor/venue type
- Revenue forecasting
- Follow-up reminders
- Commission calculations

#### B. Vendor Negotiation Intelligence
**ID**: `bali-love-vendor-negotiation-prompt`
**Priority**: HIGH

**Purpose**: Provide data-driven insights for vendor negotiations and pricing.

**Use Cases**:
- "What's the average markup for beach wedding venues?"
- "Show me pricing history for Bali Catering Company"
- "Which vendors offer the best package deals?"
- "Compare commission rates across photography vendors"

**Key Features**:
- Historical pricing analysis
- Competitor comparisons
- Package optimization suggestions
- Seasonal pricing trends
- Negotiation talking points

### 2. CLIENT EXPERIENCE TEAM PROMPTS

#### A. Event Status Dashboard
**ID**: `bali-love-event-status-prompt`
**Priority**: CRITICAL

**Purpose**: Provide real-time event status and identify issues requiring attention.

**Use Cases**:
- "Show me all events happening this week with pending tasks"
- "Which events have unresolved issues?"
- "List upcoming events missing key vendor confirmations"
- "What's the RSVP status for next month's events?"

**Key Features**:
- Multi-event timeline view
- Task completion tracking
- Vendor confirmation status
- Issue prioritization
- Client satisfaction indicators

#### B. Client Communication Optimizer
**ID**: `bali-love-client-comm-prompt`
**Priority**: HIGH

**Purpose**: Help craft and track client communications effectively.

**Use Cases**:
- "Draft a response to an unhappy client about catering delays"
- "Show me all unanswered client messages from this week"
- "Generate a wedding day timeline email for the Johnson wedding"
- "Which clients haven't been contacted in 30+ days?"

**Key Features**:
- Response templates by situation
- Sentiment analysis of client messages
- Follow-up tracking
- Communication history summaries
- Escalation recommendations

### 3. FINANCE TEAM PROMPTS

#### A. Financial Health Monitor
**ID**: `bali-love-financial-monitor-prompt`
**Priority**: CRITICAL

**Purpose**: Track payments, budgets, and financial KPIs across all events.

**Use Cases**:
- "Show me all overdue payments from vendors"
- "Which events are over budget by more than 10%?"
- "Generate a cash flow forecast for next quarter"
- "List all pending refunds that need processing"

**Key Features**:
- Accounts receivable/payable tracking
- Budget vs. actual analysis
- Cash flow projections
- Currency conversion handling
- Tax calculation assistance

#### B. Vendor Payment Coordinator
**ID**: `bali-love-vendor-payment-prompt`
**Priority**: HIGH

**Purpose**: Manage vendor payments and financial relationships.

**Use Cases**:
- "Which vendors need to be paid this week?"
- "Show payment history for all photography vendors"
- "Generate a payment schedule for the Smith wedding"
- "Identify vendors with payment disputes"

**Key Features**:
- Payment scheduling
- Invoice verification
- Dispute tracking
- Commission calculations
- Vendor financial ratings

### 4. PEOPLE & CULTURE TEAM PROMPTS

#### A. Team Performance Navigator
**ID**: `bali-love-team-performance-prompt`
**Priority**: MEDIUM

**Purpose**: Track team member performance and training needs.

**Use Cases**:
- "Who hasn't completed their event coordination training?"
- "Show me team members available for event assignments next week"
- "Which employees have the highest client satisfaction scores?"
- "List training certifications expiring this quarter"

**Key Features**:
- Training completion tracking
- Performance metrics dashboard
- Availability management
- Skill gap analysis
- Recognition opportunities

#### B. Onboarding Assistant
**ID**: `bali-love-onboarding-prompt`
**Priority**: MEDIUM

**Purpose**: Guide new employees through onboarding and initial training.

**Use Cases**:
- "Create an onboarding checklist for a new Revenue team member"
- "What training modules should a new event coordinator complete first?"
- "Show me all new hires who haven't completed safety training"
- "Generate a 30-day onboarding plan"

**Key Features**:
- Role-specific onboarding paths
- Progress tracking
- Mentor assignment suggestions
- Documentation access
- First-month milestones

### 5. ALL TEAMS (CROSS-FUNCTIONAL) PROMPTS

#### A. Daily Operations Brief
**ID**: `bali-love-daily-brief-prompt`
**Priority**: HIGH

**Purpose**: Provide personalized daily briefings for any team member.

**Use Cases**:
- "What do I need to focus on today?"
- "Show me urgent items across all my events"
- "What meetings and deadlines do I have this week?"
- "Give me a status update on my assigned tasks"

**Key Features**:
- Personalized task lists
- Priority-based sorting
- Calendar integration
- Team collaboration items
- Quick wins identification

## Implementation Priority Matrix

### CRITICAL (Implement First)
1. Event Status Dashboard (Client Experience)
2. Financial Health Monitor (Finance)

### HIGH (Implement Second)
1. Sales Pipeline Assistant (Revenue)
2. Client Communication Optimizer (Client Experience)
3. Vendor Payment Coordinator (Finance)
4. Daily Operations Brief (All Teams)
5. Vendor Negotiation Intelligence (Revenue)

### MEDIUM (Implement Third)
1. Team Performance Navigator (People & Culture)
2. Onboarding Assistant (People & Culture)

## Success Metrics

### Revenue Team
- Lead response time reduction
- Conversion rate improvement
- Revenue forecast accuracy

### Client Experience Team
- Client response time
- Issue resolution speed
- Client satisfaction scores

### Finance Team
- Payment processing time
- Budget variance reduction
- Cash flow accuracy

### People & Culture Team
- Training completion rates
- Onboarding time reduction
- Employee satisfaction scores

## Integration Notes

1. **Context Awareness**: Each prompt should know the user's team and role
2. **Data Access**: Prompts should only access data the user's team has permission to view
3. **Workflow Integration**: Prompts should connect to existing tools (calendar, task management)
4. **Mobile Optimization**: Many team members work on-site and need mobile-friendly responses
5. **Multilingual Support**: Consider Bahasa Indonesia support for local team members

## Testing Priorities

Focus testing on the most common daily queries for each team:

**Revenue**: "Show me this week's high-priority leads"
**Client Experience**: "What events need attention today?"
**Finance**: "Which payments are overdue?"
**People & Culture**: "Who needs training renewal?"