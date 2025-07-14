'use client'

import { Sidebar } from './Sidebar'
import { useAuth } from '@/app/contexts/AuthContext'

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const { user } = useAuth()

  // Only show sidebar for authenticated users
  if (!user) {
    return <>{children}</>
  }

  return (
    <div className="flex h-full w-full bg-white dark:bg-gray-950">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        {children}
      </div>
    </div>
  )
}