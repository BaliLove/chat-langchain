'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/contexts/AuthContext'
import { usePermissions } from '@/app/hooks/usePermissions'

interface AdminRouteProps {
  children: React.ReactNode
}

export default function AdminRoute({ children }: AdminRouteProps) {
  const { user, userTeamData, loading: authLoading } = useAuth()
  const { permissions, loading: permLoading } = usePermissions()
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !permLoading) {
      if (!user || userTeamData?.role !== 'admin') {
        router.push('/')
      }
    }
  }, [user, userTeamData, authLoading, permLoading, router])

  if (authLoading || permLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (!user || userTeamData?.role !== 'admin') {
    return null
  }

  return <>{children}</>
}