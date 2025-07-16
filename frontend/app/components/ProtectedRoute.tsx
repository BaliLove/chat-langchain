'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/contexts/AuthContextStable'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading, isAuthorized } = useAuth()
  const router = useRouter()

  useEffect(() => {
    // Debug logging
    console.log('🛡️ ProtectedRoute state:', { 
      user: user ? `${user.email} (${user.id})` : null, 
      loading, 
      isAuthorized,
      shouldRedirect: !loading && (!user || !isAuthorized)
    })
    
    if (!loading && (!user || !isAuthorized)) {
      console.log('🚫 Redirecting to login - no user or not authorized')
      router.push('/login')
    }
  }, [user, loading, isAuthorized, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
          <p className="text-sm text-gray-600">Loading authentication...</p>
        </div>
      </div>
    )
  }

  if (!user || !isAuthorized) {
    return null
  }

  return <>{children}</>
}