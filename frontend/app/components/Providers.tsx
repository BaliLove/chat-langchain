'use client'

import { ReactNode } from 'react'
import { NuqsAdapter } from 'nuqs/adapters/next/app'
import { AuthProvider } from '../contexts/AuthContextStable'
import { AppLayout } from './AppLayout'

export function Providers({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <NuqsAdapter>
        <AppLayout>
          {children}
        </AppLayout>
      </NuqsAdapter>
    </AuthProvider>
  )
}