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
import { Search, Bot, FileText, Filter, Users } from 'lucide-react'
import ProtectedRoute from '@/app/components/ProtectedRoute'

// Mock data for agents and prompts
const mockAgents = [
  {
    id: '1',
    name: 'Venue Assistant',
    description: 'Helps users find and book venues in Bali',
    team: 'sales',
    type: 'agent',
    model: 'GPT-4',
    created: '2024-01-15',
    usage: 1234
  },
  {
    id: '2',
    name: 'Event Planner',
    description: 'Assists with event planning and coordination',
    team: 'operations',
    type: 'agent',
    model: 'Claude 3',
    created: '2024-01-20',
    usage: 856
  },
  {
    id: '3',
    name: 'Customer Service Bot',
    description: 'Handles customer inquiries and support tickets',
    team: 'support',
    type: 'agent',
    model: 'GPT-3.5',
    created: '2024-01-10',
    usage: 3421
  }
]

const mockPrompts = [
  {
    id: '4',
    name: 'Venue Search Prompt',
    description: 'Optimized prompt for searching venue database',
    team: 'sales',
    type: 'prompt',
    category: 'search',
    created: '2024-01-18',
    usage: 567
  },
  {
    id: '5',
    name: 'Welcome Message',
    description: 'Initial greeting for new chat sessions',
    team: 'all',
    type: 'prompt',
    category: 'greeting',
    created: '2024-01-05',
    usage: 10234
  },
  {
    id: '6',
    name: 'Training Module Q&A',
    description: 'Handles questions about training and onboarding',
    team: 'hr',
    type: 'prompt',
    category: 'training',
    created: '2024-01-22',
    usage: 234
  }
]

const allItems = [...mockAgents, ...mockPrompts]

export default function AgentsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [filterTeam, setFilterTeam] = useState('all')

  const filteredItems = allItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = filterType === 'all' || item.type === filterType
    const matchesTeam = filterTeam === 'all' || item.team === filterTeam
    
    return matchesSearch && matchesType && matchesTeam
  })

  return (
    <ProtectedRoute>
      <div className="flex-1 p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Agents & Prompts
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage and explore available AI agents and prompt templates
          </p>
        </div>

        {/* Filters */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
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
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="Filter by team" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Teams</SelectItem>
              <SelectItem value="sales">Sales</SelectItem>
              <SelectItem value="operations">Operations</SelectItem>
              <SelectItem value="support">Support</SelectItem>
              <SelectItem value="hr">HR</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total Agents</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Bot className="h-8 w-8 text-primary" />
                <span className="text-2xl font-bold">{mockAgents.length}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total Prompts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <FileText className="h-8 w-8 text-primary" />
                <span className="text-2xl font-bold">{mockPrompts.length}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total Usage</CardTitle>
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
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    {item.type === 'agent' ? 
                      <Bot className="h-5 w-5 text-primary" /> : 
                      <FileText className="h-5 w-5 text-primary" />
                    }
                    <CardTitle className="text-lg">{item.name}</CardTitle>
                  </div>
                  <span className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                    {item.team}
                  </span>
                </div>
                <CardDescription className="mt-2">
                  {item.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span>{item.type === 'agent' ? `Model: ${(item as any).model}` : `Type: ${(item as any).category}`}</span>
                  <span>{item.usage.toLocaleString()} uses</span>
                </div>
                <div className="mt-4 flex gap-2">
                  <Button size="sm" variant="outline" className="flex-1">
                    View Details
                  </Button>
                  <Button size="sm" className="flex-1">
                    Use This
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredItems.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No agents or prompts found matching your criteria.</p>
          </div>
        )}
      </div>
    </ProtectedRoute>
  )
}