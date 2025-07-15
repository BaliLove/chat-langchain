import { NextResponse } from 'next/server'

// Mock data for prompts - in production this would fetch from LangSmith
const LANGSMITH_PROMPTS = [
  {
    id: 'bali-love-router-prompt',
    name: 'Router System Prompt',
    description: 'Classifies user queries into research, general, or more-info categories',
    team: 'All',
    type: 'prompt',
    category: 'Core System',
    contextTags: {
      'All': ['All'],
      'Revenue': ['All'],
      'Client Experience': ['All'],
      'Finance': ['All'],
      'People & Culture': ['All'],
      'Digital': ['All'],
      'Special Projects': ['All']
    },
    usage: 15234,
    lastUpdated: '2025-01-15T10:30:00Z',
    version: 1,
  },
  {
    id: 'bali-love-generate-queries-prompt',
    name: 'Generate Queries Prompt',
    description: 'Creates 3-5 specific search queries to find relevant information',
    team: 'Digital',
    type: 'prompt',
    category: 'Research',
    contextTags: {
      'All': ['All'],
      'Digital': ['Documentation', 'Systems'],
      'Special Projects': ['Research']
    },
    usage: 8421,
    lastUpdated: '2025-01-15T09:45:00Z',
    version: 1,
  },
  {
    id: 'bali-love-more-info-prompt',
    name: 'More Information Prompt',
    description: 'Requests clarification when queries are too vague or unclear',
    team: 'Client Experience',
    type: 'prompt',
    category: 'Conversation',
    contextTags: {
      'All': ['Communication'],
      'Client Experience': ['Weddings', 'Corporate Events', 'All']
    },
    usage: 3456,
    lastUpdated: '2025-01-14T16:20:00Z',
    version: 1,
  },
  {
    id: 'bali-love-research-plan-prompt',
    name: 'Research Plan Prompt',
    description: 'Creates step-by-step research plans to answer questions comprehensively',
    team: 'Revenue',
    type: 'prompt',
    category: 'Research',
    contextTags: {
      'All': ['Events', 'Venues & Vendors'],
      'Revenue': ['Venues', 'Vendors', 'Packages'],
      'Client Experience': ['Weddings', 'Corporate Events']
    },
    usage: 5678,
    lastUpdated: '2025-01-13T14:30:00Z',
    version: 1,
  },
  {
    id: 'bali-love-general-prompt',
    name: 'General Conversation Prompt',
    description: 'Handles general queries and casual conversation',
    team: 'Client Experience',
    type: 'prompt',
    category: 'Conversation',
    contextTags: {
      'All': ['Communication'],
      'Client Experience': ['All'],
      'People & Culture': ['Team Info']
    },
    usage: 12345,
    lastUpdated: '2025-01-12T11:15:00Z',
    version: 1,
  },
  {
    id: 'bali-love-response-prompt',
    name: 'Response System Prompt',
    description: 'Generates comprehensive answers based on retrieved context',
    team: 'All',
    type: 'prompt',
    category: 'Core System',
    contextTags: {
      'All': ['All'],
      'Revenue': ['All'],
      'Client Experience': ['All'],
      'Finance': ['All'],
      'People & Culture': ['All'],
      'Digital': ['All'],
      'Special Projects': ['All']
    },
    usage: 18765,
    lastUpdated: '2025-01-11T08:00:00Z',
    version: 1,
  },
  {
    id: 'bali-love-eos-issue-prompt',
    name: 'EOS Issue Management',
    description: 'Helps team manage EOS issues - find duplicates, review stale items, track ownership',
    team: 'Digital',
    type: 'prompt',
    category: 'Operations',
    contextTags: {
      'All': ['Tasks & Issues'],
      'Digital': ['Issues', 'Tasks'],
      'Finance': ['Reports'],
      'Client Experience': ['All']
    },
    usage: 0,
    lastUpdated: '2025-01-15T12:00:00Z',
    version: 1,
  }
]

export async function GET() {
  try {
    // In production, this would:
    // 1. Initialize LangSmith client with API key
    // 2. Fetch all prompts with 'bali-love' prefix
    // 3. Get usage statistics
    // 4. Return formatted data
    
    // For now, return mock data
    return NextResponse.json({
      prompts: LANGSMITH_PROMPTS,
      success: true
    })
  } catch (error) {
    console.error('Failed to fetch prompts:', error)
    return NextResponse.json(
      { error: 'Failed to fetch prompts', success: false },
      { status: 500 }
    )
  }
}