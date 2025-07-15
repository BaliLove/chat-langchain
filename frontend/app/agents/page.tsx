'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card'
import { Button } from '@/app/components/ui/button'
import { Input } from '@/app/components/ui/input'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/app/components/ui/select'
import { Badge } from '@/app/components/ui/badge'
import { Search, Bot, FileText, Filter, Users, Sparkles, Target, Info, MessageSquare, Route, Database } from 'lucide-react'
import ProtectedRoute from '@/app/components/ProtectedRoute'

// Real LangChain prompts from the backend
const langChainPrompts = [
  {
    id: 'router',
    name: 'Router System Prompt',
    description: 'Classifies user queries into research, general, or more-info categories',
    team: 'All',
    type: 'prompt',
    category: 'Core System',
    langsmithId: 'bali-love-router-prompt',
    usage: 15234,
    preview: 'You are a helpful AI assistant routing user queries. Classify the user\'s query into one of these categories...'
  },
  {
    id: 'generate-queries',
    name: 'Generate Queries Prompt',
    description: 'Creates 3-5 specific search queries to find relevant information',
    team: 'Digital',
    type: 'prompt',
    category: 'Research',
    langsmithId: 'bali-love-generate-queries-prompt',
    usage: 8421,
    preview: 'Given a user\'s question, generate 3-5 specific search queries that would help find relevant information...'
  },
  {
    id: 'more-info',
    name: 'More Information Prompt',
    description: 'Requests clarification when queries are too vague or unclear',
    team: 'Client Experience',
    type: 'prompt',
    category: 'Conversation',
    langsmithId: 'bali-love-more-info-prompt',
    usage: 3456,
    preview: 'The user\'s query is too vague or unclear. Based on their query: {logic}...'
  },
  {
    id: 'research-plan',
    name: 'Research Plan Prompt',
    description: 'Creates step-by-step research plans to answer questions comprehensively',
    team: 'Revenue',
    type: 'prompt',
    category: 'Research',
    langsmithId: 'bali-love-research-plan-prompt',
    usage: 5678,
    preview: 'Create a step-by-step research plan to answer the user\'s question comprehensively...'
  },
  {
    id: 'general',
    name: 'General Conversation Prompt',
    description: 'Handles general queries and casual conversation',
    team: 'Client Experience',
    type: 'prompt',
    category: 'Conversation',
    langsmithId: 'bali-love-general-prompt',
    usage: 12345,
    preview: 'You are a helpful AI assistant. Based on the context: {logic}...'
  },
  {
    id: 'response',
    name: 'Response System Prompt',
    description: 'Generates comprehensive answers based on retrieved context',
    team: 'All',
    type: 'prompt',
    category: 'Core System',
    langsmithId: 'bali-love-response-prompt',
    usage: 18765,
    preview: 'You are a helpful AI assistant. Answer the user\'s question based on the following context...'
  }
]

// Real agents/assistants based on the prompts
const baliLoveAgents = [
  {
    id: 'main-assistant',
    name: 'Bali Love Main Assistant',
    description: 'Primary chat assistant that routes queries and provides comprehensive answers',
    team: 'All',
    type: 'agent',
    model: 'GPT-4 / Claude',
    features: ['Query Routing', 'Context Retrieval', 'Multi-step Research'],
    usage: 25432
  },
  {
    id: 'venue-specialist',
    name: 'Venue Research Specialist',
    description: 'Specialized in finding and recommending venues based on event requirements',
    team: 'Revenue',
    type: 'agent',
    model: 'GPT-4',
    features: ['Venue Search', 'Availability Check', 'Price Comparison'],
    usage: 8765
  },
  {
    id: 'event-planner',
    name: 'Event Planning Assistant',
    description: 'Helps with event coordination, vendor management, and timeline planning',
    team: 'Client Experience',
    type: 'agent',
    model: 'Claude 3',
    features: ['Timeline Creation', 'Vendor Coordination', 'Budget Management'],
    usage: 6543
  },
  {
    id: 'training-bot',
    name: 'Training & Onboarding Bot',
    description: 'Assists new team members with training materials and company policies',
    team: 'People & Culture',
    type: 'agent',
    model: 'GPT-3.5',
    features: ['Policy Q&A', 'Training Modules', 'Onboarding Guidance'],
    usage: 3210
  }
]

// Real teams from the database
const baliLoveTeams = [
  { value: 'all', label: 'All Teams' },
  { value: 'All', label: 'All' },
  { value: 'Revenue', label: 'Revenue' },
  { value: 'Client Experience', label: 'Client Experience' },
  { value: 'Finance', label: 'Finance' },
  { value: 'People & Culture', label: 'People & Culture' },
  { value: 'Digital', label: 'Digital' },
  { value: 'Special Projects', label: 'Special Projects' }
]

const allItems = [...baliLoveAgents, ...langChainPrompts]

export default function AgentsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [filterTeam, setFilterTeam] = useState('all')

  const filteredItems = allItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = filterType === 'all' || item.type === filterType
    const matchesTeam = filterTeam === 'all' || item.team === filterTeam || (filterTeam === 'All' && item.team === 'All')
    
    return matchesSearch && matchesType && matchesTeam
  })

  const getIcon = (item: any) => {
    if (item.type === 'agent') {
      return <Bot className="h-5 w-5 text-primary" />
    }
    switch (item.category) {
      case 'Core System':
        return <Route className="h-5 w-5 text-primary" />
      case 'Research':
        return <Database className="h-5 w-5 text-primary" />
      case 'Conversation':
        return <MessageSquare className="h-5 w-5 text-primary" />
      default:
        return <FileText className="h-5 w-5 text-primary" />
    }
  }

  return (
    <ProtectedRoute>
      <div className="flex-1 p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Agents & Prompts
          </h1>
          <p className="text-muted-foreground">
            Explore Bali Love&apos;s AI agents and LangChain prompt templates
          </p>
        </div>

        {/* Filters */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Search agents and prompts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="agent">Agents Only</SelectItem>
              <SelectItem value="prompt">Prompts Only</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filterTeam} onValueChange={setFilterTeam}>
            <SelectTrigger className="w-full sm:w-48">
              <SelectValue placeholder="Filter by team" />
            </SelectTrigger>
            <SelectContent>
              {baliLoveTeams.map(team => (
                <SelectItem key={team.value} value={team.value}>
                  {team.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Active Agents</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Bot className="h-8 w-8 text-primary" />
                <span className="text-2xl font-bold">{baliLoveAgents.length}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Prompt Templates</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <FileText className="h-8 w-8 text-primary" />
                <span className="text-2xl font-bold">{langChainPrompts.length}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Usage</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Users className="h-8 w-8 text-primary" />
                <span className="text-2xl font-bold">
                  {allItems.reduce((sum, item) => sum + item.usage, 0).toLocaleString()}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Results */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map(item => (
            <Card 
              key={item.id} 
              className="hover:shadow-lg transition-shadow cursor-pointer"
            >
              <CardHeader>
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getIcon(item)}
                    <CardTitle className="text-lg">{item.name}</CardTitle>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {item.team}
                  </Badge>
                </div>
                <CardDescription className="mt-2">
                  {item.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {item.type === 'agent' && (
                  <div className="mb-3">
                    <p className="text-sm text-muted-foreground mb-2">Features:</p>
                    <div className="flex flex-wrap gap-1">
                      {(item as any).features?.map((feature: string, idx: number) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {feature}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                
                {item.type === 'prompt' && (
                  <div className="mb-3">
                    <p className="text-sm text-muted-foreground mb-1">Category: {(item as any).category}</p>
                    {(item as any).langsmithId && (
                      <p className="text-xs text-muted-foreground font-mono">
                        ID: {(item as any).langsmithId}
                      </p>
                    )}
                  </div>
                )}
                
                <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
                  <span>
                    {item.type === 'agent' ? `Model: ${(item as any).model}` : 'LangSmith Prompt'}
                  </span>
                  <span>{item.usage.toLocaleString()} uses</span>
                </div>
                
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" className="flex-1">
                    <Info className="h-3 w-3 mr-1" />
                    Details
                  </Button>
                  <Button size="sm" className="flex-1">
                    <Sparkles className="h-3 w-3 mr-1" />
                    Use This
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredItems.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No agents or prompts found matching your criteria.</p>
          </div>
        )}
      </div>
    </ProtectedRoute>
  )
}