'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { useGraphContext } from '../contexts/GraphContext'
import { useAuth } from '../contexts/AuthContextStable'
import { getCookie } from '../utils/cookies'
import { USER_ID_COOKIE_NAME } from '../utils/constants'
import { RefreshCw, AlertCircle, CheckCircle } from 'lucide-react'
import { Badge } from './ui/badge'

export function ThreadDebugPanel() {
  const { threadsData, userData } = useGraphContext()
  const { userThreads, isUserThreadsLoading, getUserThreads } = threadsData
  const { userId } = userData
  const { user } = useAuth()
  const [cookieUserId, setCookieUserId] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  useEffect(() => {
    const cookieId = getCookie(USER_ID_COOKIE_NAME)
    setCookieUserId(cookieId || null)
  }, [])

  const handleRefresh = async () => {
    if (!userId) return
    setIsRefreshing(true)
    await getUserThreads(userId)
    setIsRefreshing(false)
  }

  const hasIdMismatch = user?.id && cookieUserId && user.id !== cookieUserId

  return (
    <Card className="m-4">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Thread Debug Panel
          <Button
            size="sm"
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing || !userId}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh Threads
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* ID Status */}
        <div className="space-y-2">
          <h3 className="font-medium">User IDs</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Auth ID:</span>
              <code className="ml-2 bg-muted px-2 py-1 rounded text-xs">
                {user?.id || 'Not authenticated'}
              </code>
            </div>
            <div>
              <span className="text-muted-foreground">Cookie ID:</span>
              <code className="ml-2 bg-muted px-2 py-1 rounded text-xs">
                {cookieUserId || 'None'}
              </code>
            </div>
          </div>
          <div>
            <span className="text-muted-foreground">Current User ID:</span>
            <code className="ml-2 bg-muted px-2 py-1 rounded text-xs">
              {userId || 'None'}
            </code>
          </div>
          {hasIdMismatch && (
            <Badge variant="destructive" className="mt-2">
              <AlertCircle className="h-3 w-3 mr-1" />
              ID Mismatch Detected
            </Badge>
          )}
        </div>

        {/* Thread Status */}
        <div className="space-y-2">
          <h3 className="font-medium">Thread Status</h3>
          <div className="space-y-1 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Loading:</span>
              <span>{isUserThreadsLoading ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Total Threads:</span>
              <span className="font-mono">{userThreads.length}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Threads with Values:</span>
              <span className="font-mono">
                {userThreads.filter(t => t.values && Object.keys(t.values).length > 0).length}
              </span>
            </div>
          </div>
        </div>

        {/* Thread List */}
        {userThreads.length > 0 && (
          <div className="space-y-2">
            <h3 className="font-medium">Recent Threads (First 5)</h3>
            <div className="space-y-1 text-xs">
              {userThreads.slice(0, 5).map((thread) => (
                <div key={thread.thread_id} className="p-2 bg-muted rounded">
                  <div className="font-mono">{thread.thread_id}</div>
                  <div className="text-muted-foreground">
                    Created: {new Date(thread.created_at).toLocaleString()}
                  </div>
                  <div className="text-muted-foreground">
                    Has values: {thread.values && Object.keys(thread.values).length > 0 ? 
                      <CheckCircle className="inline h-3 w-3 text-green-500" /> : 
                      <AlertCircle className="inline h-3 w-3 text-yellow-500" />
                    }
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Console Instructions */}
        <div className="text-xs text-muted-foreground border-t pt-2">
          Check browser console for detailed [THREAD DEBUG] and [USER DEBUG] logs
        </div>
      </CardContent>
    </Card>
  )
}