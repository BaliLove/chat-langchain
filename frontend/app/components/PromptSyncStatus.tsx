'use client'

import { useEffect, useState } from 'react'
import { Badge } from '@/app/components/ui/badge'
import { Button } from '@/app/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card'
import { RefreshCw, CheckCircle, AlertCircle, Clock } from 'lucide-react'

interface SyncStatus {
  last_sync_at: string
  sync_status: 'success' | 'error' | 'in_progress'
  error_message?: string
  prompts_synced: number
}

export function PromptSyncStatus() {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  const fetchSyncStatus = async () => {
    try {
      const response = await fetch('/api/prompts/sync-status')
      const data = await response.json()
      if (data.success && data.status) {
        setSyncStatus(data.status)
      }
    } catch (error) {
      console.error('Failed to fetch sync status:', error)
    } finally {
      setLoading(false)
    }
  }

  const triggerSync = async () => {
    setSyncing(true)
    try {
      const response = await fetch('/api/prompts/sync', {
        method: 'POST'
      })
      const data = await response.json()
      
      if (data.success) {
        // Refresh status after sync
        await fetchSyncStatus()
      }
    } catch (error) {
      console.error('Failed to trigger sync:', error)
    } finally {
      setSyncing(false)
    }
  }

  useEffect(() => {
    fetchSyncStatus()
    // Refresh every 30 seconds
    const interval = setInterval(fetchSyncStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Sync Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">Loading sync status...</div>
        </CardContent>
      </Card>
    )
  }

  if (!syncStatus) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sync Status</CardTitle>
          <CardDescription>No sync information available</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={triggerSync} disabled={syncing} className="w-full">
            {syncing ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Syncing...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Sync Now
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    )
  }

  const getStatusIcon = () => {
    switch (syncStatus.sync_status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'in_progress':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusBadge = () => {
    switch (syncStatus.sync_status) {
      case 'success':
        return <Badge variant="default" className="bg-green-100 text-green-800">Success</Badge>
      case 'error':
        return <Badge variant="destructive">Error</Badge>
      case 'in_progress':
        return <Badge variant="secondary">In Progress</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  const formatLastSync = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {getStatusIcon()}
          Prompt Sync Status
        </CardTitle>
        <CardDescription>
          LangSmith ↔ Local Database
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Status</span>
          {getStatusBadge()}
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Last Sync</span>
          <span className="text-sm font-medium">
            {formatLastSync(syncStatus.last_sync_at)}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Prompts Synced</span>
          <span className="text-sm font-medium">{syncStatus.prompts_synced}</span>
        </div>

        {syncStatus.error_message && (
          <div className="p-3 bg-red-50 rounded-md">
            <div className="text-sm text-red-800">
              <strong>Error:</strong> {syncStatus.error_message}
            </div>
          </div>
        )}

        <Button 
          onClick={triggerSync} 
          disabled={syncing || syncStatus.sync_status === 'in_progress'} 
          className="w-full"
          variant="outline"
        >
          {syncing ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              Syncing...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4 mr-2" />
              Sync Now
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}