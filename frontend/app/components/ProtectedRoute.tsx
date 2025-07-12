'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading, isAuthorized } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && (!user || !isAuthorized)) {
      router.push('/login')
    }
  }, [user, loading, isAuthorized, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (!user || !isAuthorized) {
    return null
  }

  return <>{children}</>
}