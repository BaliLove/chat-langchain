'use client'

import React, { useState, useEffect } from 'react'
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
import { Search, Bot, FileText, Users, Sparkles, Info, MessageSquare, Route, Database, RefreshCw, Clock, Hash, MessageCircle, Copy, CheckCircle, AlertCircle, Star } from 'lucide-react'
import ProtectedRoute from '@/app/components/ProtectedRoute'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { format } from 'date-fns'

// No placeholder agents - only real prompts from LangSmith will be shown

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
  const [selectedTeam, setSelectedTeam] = useState('All')
  const [contextualFilter, setContextualFilter] = useState('')
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [syncStatus, setSyncStatus] = useState<any>(null)
  const [favorites, setFavorites] = useState<Set<string>>(new Set())
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false)

  // Fetch prompts from API
  useEffect(() => {
    fetchPrompts()
    fetchSyncStatus()
    fetchFavorites()
  }, [])

  // Keep selected team as 'All' by default
  // Remove auto-selection based on user's team

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
        console.log(`Loaded ${data.prompts.length} prompts from ${data.source || 'API'}`)
      }
    } catch (error) {
      console.error('Failed to fetch prompts:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchSyncStatus = async () => {
    try {
      const response = await fetch('/api/prompts/sync-status')
      const data = await response.json()
      if (data.success) {
        setSyncStatus(data.syncStatus)
      }
    } catch (error) {
      console.error('Failed to fetch sync status:', error)
    }
  }

  const fetchFavorites = async () => {
    try {
      const response = await fetch('/api/favorites')
      const data = await response.json()
      if (data.success) {
        const favoriteIds = new Set<string>(data.favorites.map((f: any) => f.prompt_id))
        setFavorites(favoriteIds)
      }
    } catch (error) {
      console.error('Failed to fetch favorites:', error)
    }
  }

  const toggleFavorite = async (promptId: string) => {
    try {
      const response = await fetch('/api/favorites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ promptId })
      })
      const data = await response.json()
      if (data.success) {
        const newFavorites = new Set(favorites)
        if (data.isFavorite) {
          newFavorites.add(promptId)
        } else {
          newFavorites.delete(promptId)
        }
        setFavorites(newFavorites)
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error)
    }
  }

  const refreshPrompts = async () => {
    setRefreshing(true)
    await fetchPrompts()
    await fetchSyncStatus()
    await fetchFavorites()
    setRefreshing(false)
  }

  const allItems = [...prompts] // Only show real prompts from LangSmith

  const filteredItems = allItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = filterType === 'all' || item.type === filterType
    const matchesTeam = selectedTeam === 'All' || item.team === selectedTeam
    const matchesFavorites = !showFavoritesOnly || favorites.has(item.id)
    
    // Check contextual filter based on contextTags
    let matchesContext = contextualFilter === '' // empty filter means show all
    if (!matchesContext && item.contextTags) {
      const teamTags = item.contextTags[selectedTeam] || []
      matchesContext = teamTags.includes('All') || teamTags.includes(contextualFilter)
    }
    
    return matchesSearch && matchesType && matchesTeam && matchesContext && matchesFavorites
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

  const handleStartChat = async (e: React.MouseEvent, item: any) => {
    e.stopPropagation()
    
    // Track usage
    try {
      await fetch(`/api/prompts/${item.id}/track-usage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ team: userTeamData?.team_name || 'Unknown' })
      })
    } catch (error) {
      console.error('Failed to track usage:', error)
    }
    
    // Navigate to chat with specific prompt
    window.location.href = `/?prompt=${item.id}`
  }

  const handleCopyId = (e: React.MouseEvent, item: any) => {
    e.stopPropagation()
    navigator.clipboard.writeText(item.id)
    // Show a subtle notification instead of alert
    const button = e.currentTarget
    const originalText = button.querySelector('span')?.textContent
    if (originalText) {
      button.querySelector('span')!.textContent = 'Copied!'
      setTimeout(() => {
        button.querySelector('span')!.textContent = originalText
      }, 1000)
    }
  }

  const handleCardClick = (item: any) => {
    // Navigate to detail page
    window.location.href = `/prompts/${item.id}`
  }

  return (
    <ProtectedRoute>
      <div className="flex-1 overflow-y-auto">
        <div className="p-8 max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              <h1 className="text-3xl font-bold text-foreground">
                Prompts
              </h1>
              <div className="flex items-center gap-4">
                {syncStatus && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    {syncStatus.sync_status === 'success' ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : syncStatus.sync_status === 'error' ? (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    ) : syncStatus.sync_status === 'tables_not_created' ? (
                      <AlertCircle className="h-4 w-4 text-yellow-500" />
                    ) : (
                      <Clock className="h-4 w-4" />
                    )}
                    <span>
                      {syncStatus.sync_status === 'tables_not_created' ? (
                        'Database setup required'
                      ) : syncStatus.last_sync_at ? (
                        <>Synced {format(new Date(syncStatus.last_sync_at), 'PPp')}</>
                      ) : (
                        'Never synced'
                      )}
                    </span>
                  </div>
                )}
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
            </div>
            <p className="text-muted-foreground">
              LangSmith prompts for your AI assistant
            </p>
          </div>

          {/* Filters */}
          <div className="space-y-4 mb-6">
            {/* Team Filter - Primary filter as buttons */}
            <div className="flex flex-wrap gap-2">
              {baliLoveTeams.map((team, index) => (
                <React.Fragment key={team}>
                  {/* Add star filter button after "All" */}
                  {index === 1 && (
                    <Button
                      variant={showFavoritesOnly ? "default" : "outline"}
                      size="sm"
                      onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
                      className="gap-1"
                    >
                      <Star className={`h-4 w-4 ${showFavoritesOnly ? 'fill-current' : ''}`} />
                      Favorites
                    </Button>
                  )}
                  <Button
                    variant={selectedTeam === team && !showFavoritesOnly ? "default" : "outline"}
                    size="sm"
                    onClick={() => {
                      setSelectedTeam(team)
                      setShowFavoritesOnly(false)
                    }}
                  >
                    {team}
                    {team === userTeamData?.team_name && (
                      <span className="ml-1 text-xs">(Your Team)</span>
                    )}
                  </Button>
                </React.Fragment>
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
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {filteredItems.map(item => (
                <Card 
                  key={item.id} 
                  className="hover:shadow-md transition-all hover:scale-[1.02] cursor-pointer relative"
                  onClick={() => handleCardClick(item)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="p-2 bg-primary/10 rounded-lg">
                        {getIcon(item)}
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 w-7 p-0"
                          onClick={(e) => {
                            e.stopPropagation()
                            toggleFavorite(item.id)
                          }}
                        >
                          <Star className={`h-4 w-4 ${favorites.has(item.id) ? 'fill-yellow-400 text-yellow-400' : 'text-muted-foreground'}`} />
                        </Button>
                        <Badge variant="outline" className="text-xs">
                          {item.team}
                        </Badge>
                      </div>
                    </div>
                    <CardTitle className="text-sm font-medium line-clamp-1">
                      {item.name}
                    </CardTitle>
                    <CardDescription className="text-xs line-clamp-2 mt-1">
                      {item.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                      <span>{(item as any).category}</span>
                      <span>{item.usage.toLocaleString()}</span>
                    </div>
                    
                    {/* Action buttons */}
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        className="flex-1 h-7 text-xs"
                        onClick={(e) => handleStartChat(e, item)}
                      >
                        <MessageCircle className="h-3 w-3 mr-1" />
                        Start Chat
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 px-2"
                        onClick={(e) => handleCopyId(e, item)}
                      >
                        <Copy className="h-3 w-3" />
                        <span className="sr-only">Copy ID</span>
                      </Button>
                    </div>
                    
                    {/* Show contextual tags only if they exist for selected team */}
                    {(item as any).contextTags && (item as any).contextTags[selectedTeam] && 
                     !(item as any).contextTags[selectedTeam].includes('All') && (
                      <div className="mt-3 flex flex-wrap gap-1">
                        {(item as any).contextTags[selectedTeam].slice(0, 2).map((tag: string, idx: number) => (
                          <Badge key={idx} variant="secondary" className="text-xs px-1.5 py-0">
                            {tag}
                          </Badge>
                        ))}
                        {(item as any).contextTags[selectedTeam].length > 2 && (
                          <span className="text-xs text-muted-foreground">
                            +{(item as any).contextTags[selectedTeam].length - 2}
                          </span>
                        )}
                      </div>
                    )}
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