'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { AlertCircle, Info, RefreshCw } from 'lucide-react'
import { Alert, AlertDescription } from './ui/alert'
import { useAuth } from '../contexts/AuthContextStable'
import { getCookie } from '../utils/cookies'
import { USER_ID_COOKIE_NAME } from '../utils/constants'

export function ThreadDebugInfo() {
  const { user } = useAuth()
  const [cookieUserId, setCookieUserId] = useState<string | null>(null)
  const [showDebug, setShowDebug] = useState(false)

  useEffect(() => {
    const cookieId = getCookie(USER_ID_COOKIE_NAME)
    setCookieUserId(cookieId)
  }, [])

  if (!showDebug) {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowDebug(true)}
        className="fixed bottom-4 right-4 opacity-50 hover:opacity-100"
      >
        <Info className="h-4 w-4 mr-2" />
        Debug Thread Issues
      </Button>
    )
  }

  const hasIdMismatch = user?.id && cookieUserId && user.id !== cookieUserId

  return (
    <Card className="fixed bottom-4 right-4 w-96 shadow-lg z-50">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Thread Debug Info
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowDebug(false)}
          >
            ×
          </Button>
        </CardTitle>
        <CardDescription>
          Debugging information for thread visibility issues
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Auth User ID:</span>
            <code className="text-xs bg-muted px-2 py-1 rounded">
              {user?.id || 'Not authenticated'}
            </code>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Cookie User ID:</span>
            <code className="text-xs bg-muted px-2 py-1 rounded">
              {cookieUserId || 'None'}
            </code>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Status:</span>
            <span className={`text-xs font-medium ${hasIdMismatch ? 'text-destructive' : 'text-green-600'}`}>
              {hasIdMismatch ? 'ID Mismatch Detected' : 'IDs Match'}
            </span>
          </div>
        </div>

        {hasIdMismatch && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Your authentication ID doesn&apos;t match your cookie ID. This may cause threads to not appear.
              Try refreshing the page to sync the IDs.
            </AlertDescription>
          </Alert>
        )}

        <div className="space-y-2">
          <Button
            onClick={() => window.location.reload()}
            size="sm"
            className="w-full"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh Page
          </Button>
          
          {hasIdMismatch && (
            <Alert className="mt-2">
              <Info className="h-4 w-4" />
              <AlertDescription className="text-xs">
                If you had chats before signing in, they may be associated with the old cookie ID: 
                <code className="block mt-1 text-xs bg-muted px-2 py-1 rounded break-all">
                  {cookieUserId}
                </code>
              </AlertDescription>
            </Alert>
          )}
        </div>
      </CardContent>
    </Card>
  )
}