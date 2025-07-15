'use client'

import { Sidebar } from './Sidebar'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { GraphProvider } from '@/app/contexts/GraphContext'

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
    <GraphProvider>
      <div className="flex h-full w-full bg-white dark:bg-gray-950">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          {children}
        </div>
      </div>
    </GraphProvider>
  )
}