'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card'
import { Button } from '@/app/components/ui/button'
import { Input } from '@/app/components/ui/input'
import { Badge } from '@/app/components/ui/badge'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/app/components/ui/select'
import { Search, Bot, FileText, Users, Sparkles, Info, MessageSquare, Route, Database, RefreshCw, Clock, Hash } from 'lucide-react'
import ProtectedRoute from '@/app/components/ProtectedRoute'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { format } from 'date-fns'

// Real agents/assistants with contextual tags
const baliLoveAgents = [
  {
    id: 'main-assistant',
    name: 'Bali Love Main Assistant',
    description: 'Primary chat assistant that routes queries and provides comprehensive answers',
    team: 'All',
    type: 'agent',
    contextTags: {
      'All': ['All'],
      'Revenue': ['All'],
      'Client Experience': ['All'],
      'Finance': ['All'],
      'People & Culture': ['All'],
      'Digital': ['All'],
      'Special Projects': ['All']
    },
    features: ['Query Routing', 'Context Retrieval', 'Multi-step Research'],
    usage: 25432,
    lastUpdated: '2025-01-10T10:00:00Z'
  },
  {
    id: 'venue-specialist',
    name: 'Venue Research Specialist',
    description: 'Specialized in finding and recommending venues based on event requirements',
    team: 'Revenue',
    type: 'agent',
    contextTags: {
      'All': ['Venues & Vendors'],
      'Revenue': ['Venues', 'Packages'],
      'Client Experience': ['Weddings', 'Corporate Events'],
      'Finance': ['Bookings', 'Invoices']
    },
    features: ['Venue Search', 'Availability Check', 'Price Comparison'],
    usage: 8765,
    lastUpdated: '2025-01-08T14:30:00Z'
  },
  {
    id: 'event-planner',
    name: 'Event Planning Assistant',
    description: 'Helps with event coordination, vendor management, and timeline planning',
    team: 'Client Experience',
    type: 'agent',
    contextTags: {
      'All': ['Events', 'Venues & Vendors', 'Bookings'],
      'Client Experience': ['Weddings', 'Corporate Events', 'Private Parties'],
      'Revenue': ['Venues', 'Vendors', 'Packages'],
      'Finance': ['Bookings', 'Payments']
    },
    features: ['Timeline Creation', 'Vendor Coordination', 'Budget Management'],
    usage: 6543,
    lastUpdated: '2025-01-07T09:15:00Z'
  },
  {
    id: 'training-bot',
    name: 'Training & Onboarding Bot',
    description: 'Assists new team members with training materials and company policies',
    team: 'People & Culture',
    type: 'agent',
    contextTags: {
      'All': ['Training', 'People'],
      'People & Culture': ['Training Modules', 'Policies', 'Onboarding'],
      'Digital': ['Documentation', 'Systems']
    },
    features: ['Policy Q&A', 'Training Modules', 'Onboarding Guidance'],
    usage: 3210,
    lastUpdated: '2025-01-05T16:45:00Z'
  },
  {
    id: 'finance-assistant',
    name: 'Finance & Booking Assistant',
    description: 'Manages bookings, payments, invoices and financial reporting',
    team: 'Finance',
    type: 'agent',
    contextTags: {
      'All': ['Bookings', 'Finance'],
      'Finance': ['Bookings', 'Payments', 'Invoices', 'Reports'],
      'Revenue': ['Packages', 'Add-ons'],
      'Client Experience': ['Weddings']
    },
    features: ['Booking Status', 'Payment Tracking', 'Invoice Generation', 'Financial Reports'],
    usage: 12890,
    lastUpdated: '2025-01-12T11:30:00Z'
  },
  {
    id: 'wedding-specialist',
    name: 'Wedding Specialist Assistant',
    description: 'Dedicated assistant for wedding planning, vendor coordination, and guest management',
    team: 'Client Experience',
    type: 'agent',
    contextTags: {
      'All': ['Events'],
      'Client Experience': ['Weddings', 'Private Parties'],
      'Revenue': ['Venues', 'Vendors', 'Packages'],
      'Finance': ['Bookings', 'Payments']
    },
    features: ['Wedding Timeline', 'Guest Management', 'Vendor Coordination', 'RSVP Tracking'],
    usage: 18234,
    lastUpdated: '2025-01-14T08:45:00Z'
  }
]

// Teams - removed duplicate 'All'
const baliLoveTeams = [
  'All',
  'Revenue',
  'Client Experience',
  'Finance',
  'People & Culture',
  'Digital',
  'Special Projects'
]

// Team-specific contextual filters (no 'All' team - shows only when specific team selected)
const teamContextualFilters: Record<string, { label: string; options: string[] }> = {
  'Revenue': {
    label: 'Service Category',
    options: ['Venues', 'Vendors', 'Packages', 'Add-ons', 'Products']
  },
  'Client Experience': {
    label: 'Event Type',
    options: ['Weddings', 'Corporate Events', 'Private Parties', 'Special Events']
  },
  'Finance': {
    label: 'Transaction Type',
    options: ['Bookings', 'Payments', 'Invoices', 'Refunds', 'Reports']
  },
  'People & Culture': {
    label: 'Content Type',
    options: ['Training Modules', 'Policies', 'Onboarding', 'Team Info']
  },
  'Digital': {
    label: 'Work Type',
    options: ['Issues', 'Tasks', 'Documentation', 'Systems', 'Integrations']
  },
  'Special Projects': {
    label: 'Project Area',
    options: ['Research', 'Innovation', 'Partnerships', 'New Services']
  }
}

interface Prompt {
  id: string
  name: string
  description: string
  team: string
  type: string
  category: string
  contextTags?: Record<string, string[]>
  usage: number
  lastUpdated: string
  version?: number
}

export default function AgentsPage() {
  const { userTeamData } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [selectedTeam, setSelectedTeam] = useState(userTeamData?.team_name || 'All')
  const [contextualFilter, setContextualFilter] = useState('')
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  // Fetch prompts from API
  useEffect(() => {
    fetchPrompts()
  }, [])

  // Update selected team when user data loads
  useEffect(() => {
    if (userTeamData?.team_name && baliLoveTeams.includes(userTeamData.team_name)) {
      setSelectedTeam(userTeamData.team_name)
    }
  }, [userTeamData])

  // Reset contextual filter when team changes
  useEffect(() => {
    setContextualFilter('')
  }, [selectedTeam])

  const fetchPrompts = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/prompts')
      const data = await response.json()
      if (data.success) {
        setPrompts(data.prompts)
      }
    } catch (error) {
      console.error('Failed to fetch prompts:', error)
    } finally {
      setLoading(false)
    }
  }

  const refreshPrompts = async () => {
    setRefreshing(true)
    await fetchPrompts()
    setRefreshing(false)
  }

  const allItems = [...baliLoveAgents, ...prompts]

  const filteredItems = allItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = filterType === 'all' || item.type === filterType
    const matchesTeam = selectedTeam === 'All' || item.team === selectedTeam
    
    // Check contextual filter based on contextTags
    let matchesContext = contextualFilter === '' // empty filter means show all
    if (!matchesContext && item.contextTags) {
      const teamTags = item.contextTags[selectedTeam] || []
      matchesContext = teamTags.includes('All') || teamTags.includes(contextualFilter)
    }
    
    return matchesSearch && matchesType && matchesTeam && matchesContext
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
      case 'Operations':
        return <Hash className="h-5 w-5 text-primary" />
      default:
        return <FileText className="h-5 w-5 text-primary" />
    }
  }

  const handleUseThis = (item: any) => {
    if (item.type === 'agent') {
      // Navigate to chat with specific agent
      window.location.href = `/chat?agent=${item.id}`
    } else {
      // Copy prompt ID to clipboard
      navigator.clipboard.writeText(item.id)
      alert(`Prompt ID "${item.id}" copied to clipboard!`)
    }
  }

  const handleDetails = (item: any) => {
    // In production, this would open a modal or navigate to details page
    console.log('View details for:', item)
    alert(`Details for ${item.name}:\n\nID: ${item.id}\nTeam: ${item.team}\nUsage: ${item.usage.toLocaleString()}\nLast Updated: ${format(new Date(item.lastUpdated), 'PPp')}`)
  }

  return (
    <ProtectedRoute>
      <div className="flex-1 overflow-y-auto">
        <div className="p-8 max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              <h1 className="text-3xl font-bold text-foreground">
                Agents & Prompts
              </h1>
              <Button 
                onClick={refreshPrompts} 
                disabled={refreshing}
                size="sm"
                variant="outline"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
            <p className="text-muted-foreground">
              Explore AI agents and dynamically loaded LangSmith prompts
            </p>
          </div>

          {/* Filters */}
          <div className="space-y-4 mb-6">
            {/* Team Filter - Primary filter as buttons */}
            <div className="flex flex-wrap gap-2">
              {baliLoveTeams.map(team => (
                <Button
                  key={team}
                  variant={selectedTeam === team ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedTeam(team)}
                >
                  {team}
                  {team === userTeamData?.team_name && (
                    <span className="ml-1 text-xs">(Your Team)</span>
                  )}
                </Button>
              ))}
            </div>

            {/* Contextual Filters Row - Shows only when specific team selected */}
            {selectedTeam !== 'All' && teamContextualFilters[selectedTeam] && (
              <div className="ml-4 p-3 bg-muted/50 rounded-lg">
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={contextualFilter === '' ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => setContextualFilter('')}
                    className="h-7 px-2 text-xs"
                  >
                    All
                  </Button>
                  {teamContextualFilters[selectedTeam].options.map(option => (
                    <Button
                      key={option}
                      variant={contextualFilter === option ? "secondary" : "ghost"}
                      size="sm"
                      onClick={() => setContextualFilter(option)}
                      className="h-7 px-2 text-xs"
                    >
                      {option}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {/* Search and Type Filter Row */}
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="Search agents and prompts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              
              {/* Type Filter */}
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-full sm:w-[180px]">
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="agent">Agents Only</SelectItem>
                  <SelectItem value="prompt">Prompts Only</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>


          {/* Results */}
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
              <p className="text-muted-foreground mt-4">Loading prompts from LangSmith...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredItems.map(item => (
                <Card 
                  key={item.id} 
                  className="hover:shadow-lg transition-shadow"
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
                        <p className="text-sm text-muted-foreground mb-1">
                          Category: {(item as any).category}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>Updated {format(new Date(item.lastUpdated), 'PP')}</span>
                        </div>
                      </div>
                    )}

                    {/* Contextual Tags for current team */}
                    {(item as any).contextTags && (item as any).contextTags[selectedTeam] && 
                     !(item as any).contextTags[selectedTeam].includes('All') && (
                      <div className="mb-3">
                        <p className="text-sm text-muted-foreground mb-1">Best for:</p>
                        <div className="flex flex-wrap gap-1">
                          {(item as any).contextTags[selectedTeam].map((tag: string, idx: number) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
                      <span>{item.usage.toLocaleString()} uses</span>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="flex-1"
                        onClick={() => handleDetails(item)}
                      >
                        <Info className="h-3 w-3 mr-1" />
                        Details
                      </Button>
                      <Button 
                        size="sm" 
                        className="flex-1"
                        onClick={() => handleUseThis(item)}
                      >
                        <Sparkles className="h-3 w-3 mr-1" />
                        Use This
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {!loading && filteredItems.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No agents or prompts found matching your criteria.</p>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  )
}