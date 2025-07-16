'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card'
import { Button } from '@/app/components/ui/button'
import { Badge } from '@/app/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs'
import { Textarea } from '@/app/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/app/components/ui/select'
import { Alert, AlertDescription } from '@/app/components/ui/alert'
import { 
  ArrowLeft, Copy, ExternalLink, MessageCircle, Clock, TrendingUp, 
  Users, Calendar, TestTube, History, BarChart, AlertCircle, Edit,
  FileText, Bot, Route, Database, MessageSquare, Hash, Star
} from 'lucide-react'
import ProtectedRoute from '@/app/components/ProtectedRoute'
import { format } from 'date-fns'

export default function PromptDetailPage() {
  const params = useParams()
  const promptId = params.id as string
  const [prompt, setPrompt] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [testInput, setTestInput] = useState('')
  const [testOutput, setTestOutput] = useState('')
  const [testLoading, setTestLoading] = useState(false)
  const [copySuccess, setCopySuccess] = useState(false)
  const [isFavorite, setIsFavorite] = useState(false)

  useEffect(() => {
    fetchPromptDetails()
    fetchFavoriteStatus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [promptId])

  const fetchPromptDetails = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/prompts/${promptId}`)
      const data = await response.json()
      
      if (data.success && data.prompt) {
        setPrompt(data.prompt)
      } else {
        setPrompt(null)
      }
    } catch (error) {
      console.error('Failed to fetch prompt details:', error)
      setPrompt(null)
    } finally {
      setLoading(false)
    }
  }

  const fetchFavoriteStatus = async () => {
    try {
      const response = await fetch(`/api/favorites/${promptId}`)
      const data = await response.json()
      if (data.success) {
        setIsFavorite(data.isFavorite)
      }
    } catch (error) {
      console.error('Failed to fetch favorite status:', error)
    }
  }

  const toggleFavorite = async () => {
    try {
      const response = await fetch('/api/favorites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ promptId })
      })
      const data = await response.json()
      if (data.success) {
        setIsFavorite(data.isFavorite)
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error)
    }
  }

  const handleCopyTemplate = () => {
    navigator.clipboard.writeText(prompt.template)
    setCopySuccess(true)
    setTimeout(() => setCopySuccess(false), 2000)
  }

  const handleCopyId = () => {
    navigator.clipboard.writeText(prompt.id)
    setCopySuccess(true)
    setTimeout(() => setCopySuccess(false), 2000)
  }

  const handleTestPrompt = async () => {
    setTestLoading(true)
    // Simulate API call
    setTimeout(() => {
      // Mock response based on input
      if (testInput.toLowerCase().includes('venue') || testInput.toLowerCase().includes('wedding')) {
        setTestOutput('research')
      } else if (testInput.toLowerCase().includes('hello') || testInput.toLowerCase().includes('hi')) {
        setTestOutput('general')
      } else {
        setTestOutput('more-info')
      }
      setTestLoading(false)
    }, 1000)
  }

  const handleRequestModification = () => {
    // In production, this would create an issue or send a notification
    const subject = `Modification Request: ${prompt.name}`
    const body = `I would like to request a modification to the "${prompt.name}" prompt (ID: ${prompt.id}).%0A%0AReason for modification:%0A%0A[Please describe what changes you'd like]`
    window.location.href = `mailto:team@bali.love?subject=${encodeURIComponent(subject)}&body=${body}`
  }

  const handleReportIssue = () => {
    const subject = `Issue Report: ${prompt.name}`
    const body = `I encountered an issue with the "${prompt.name}" prompt (ID: ${prompt.id}).%0A%0AIssue description:%0A%0A[Please describe the issue]`
    window.location.href = `mailto:team@bali.love?subject=${encodeURIComponent(subject)}&body=${body}`
  }

  const getIcon = (category: string) => {
    switch (category) {
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

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </ProtectedRoute>
    )
  }

  if (!prompt) {
    return (
      <ProtectedRoute>
        <div className="flex-1 p-8">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Prompt not found. Please check the ID and try again.
            </AlertDescription>
          </Alert>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <div className="flex-1 overflow-y-auto">
        <div className="p-8 max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => window.history.back()}
              className="mb-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Prompts
            </Button>
            
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-primary/10 rounded-lg">
                  {getIcon(prompt.category)}
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
                    {prompt.name}
                    <Badge variant="outline">v{prompt.version}</Badge>
                  </h1>
                  <p className="text-muted-foreground mt-1">{prompt.description}</p>
                  <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      {prompt.team}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      Updated {prompt.lastUpdated || prompt.last_updated ? format(new Date(prompt.lastUpdated || prompt.last_updated), 'PPp') : 'Unknown'}
                    </span>
                    <span className="flex items-center gap-1">
                      <TrendingUp className="h-3 w-3" />
                      {(prompt.usage || prompt.usage_count || 0).toLocaleString()} uses
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-2">
                <Button 
                  variant="outline"
                  size="icon"
                  onClick={toggleFavorite}
                  title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
                >
                  <Star className={`h-4 w-4 ${isFavorite ? 'fill-yellow-400 text-yellow-400' : ''}`} />
                </Button>
                <Button onClick={() => window.location.href = `/?prompt=${prompt.id}`}>
                  <MessageCircle className="h-4 w-4 mr-2" />
                  Start Chat
                </Button>
                <Button variant="outline" onClick={handleCopyId}>
                  <Copy className="h-4 w-4 mr-2" />
                  {copySuccess ? 'Copied!' : 'Copy ID'}
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => window.open(`https://smith.langchain.com/prompts/${prompt.id}`, '_blank')}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View in LangSmith
                </Button>
              </div>
            </div>
          </div>

          {/* Content Tabs */}
          <Tabs defaultValue="template" className="space-y-4">
            <TabsList>
              <TabsTrigger value="template">Template</TabsTrigger>
              <TabsTrigger value="playground">Playground</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="examples">Examples</TabsTrigger>
              <TabsTrigger value="versions">Version History</TabsTrigger>
            </TabsList>

            <TabsContent value="template" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    Prompt Template
                    <Button size="sm" variant="outline" onClick={handleCopyTemplate}>
                      <Copy className="h-3 w-3 mr-1" />
                      Copy
                    </Button>
                  </CardTitle>
                  <CardDescription>
                    The full prompt template used by this system
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-4 rounded-lg overflow-x-auto whitespace-pre-wrap">
                    <code className="text-sm font-mono">{prompt.template}</code>
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="playground" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TestTube className="h-5 w-5" />
                    Test Playground
                  </CardTitle>
                  <CardDescription>
                    Test this prompt with sample inputs
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Test Input</label>
                    <Textarea
                      placeholder="Enter a test query..."
                      value={testInput}
                      onChange={(e) => setTestInput(e.target.value)}
                      className="min-h-[100px]"
                    />
                  </div>
                  
                  <Button 
                    onClick={handleTestPrompt} 
                    disabled={!testInput || testLoading}
                    className="w-full"
                  >
                    {testLoading ? 'Testing...' : 'Test Prompt'}
                  </Button>
                  
                  {testOutput && (
                    <Alert>
                      <AlertDescription>
                        <strong>Output:</strong> {testOutput}
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="analytics" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Average Response Time</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{prompt.analytics?.avgResponseTime || 0}ms</div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Success Rate</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{prompt.analytics?.successRate || 0}%</div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Total Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{(prompt.usage || prompt.usage_count || 0).toLocaleString()}</div>
                  </CardContent>
                </Card>
              </div>
              
              <Card>
                <CardHeader>
                  <CardTitle>Usage by Team</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(prompt.analytics?.byTeam || {}).map(([team, percentage]) => (
                      <div key={team} className="flex items-center justify-between">
                        <span className="text-sm">{team}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-muted rounded-full h-2">
                            <div 
                              className="bg-primary h-2 rounded-full" 
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span className="text-sm text-muted-foreground w-10 text-right">
                            {percentage as number}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="examples" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Recent Examples</CardTitle>
                  <CardDescription>
                    Recent successful uses of this prompt
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {(prompt.examples || []).map((example: any, idx: number) => (
                      <div key={idx} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <Badge variant="outline">{example.team}</Badge>
                          <span className="text-xs text-muted-foreground">
                            {example.timestamp ? format(new Date(example.timestamp), 'PPp') : 'Unknown'}
                          </span>
                        </div>
                        <div className="space-y-2">
                          <div>
                            <span className="text-sm font-medium">Input:</span>
                            <p className="text-sm text-muted-foreground mt-1">{example.input}</p>
                          </div>
                          <div>
                            <span className="text-sm font-medium">Output:</span>
                            <Badge className="ml-2">{example.output}</Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="versions" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Version History</CardTitle>
                  <CardDescription>
                    Track changes and updates to this prompt
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {(prompt.versions || []).map((version: any, idx: number) => (
                      <div key={idx} className="flex items-start gap-4 pb-4 border-b last:border-0">
                        <div className="flex-shrink-0">
                          <Badge variant="outline">v{version.version}</Badge>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium">{version.modifiedBy}</span>
                            <span className="text-xs text-muted-foreground">
                              {version.date ? format(new Date(version.date), 'PPp') : 'Unknown'}
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground">{version.changes}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Actions */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleRequestModification}>
                  <Edit className="h-4 w-4 mr-2" />
                  Request Modification
                </Button>
                <Button variant="outline" onClick={handleReportIssue}>
                  <AlertCircle className="h-4 w-4 mr-2" />
                  Report Issue
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </ProtectedRoute>
  )
}