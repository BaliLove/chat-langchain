import { ReactNode } from 'react'
import ProtectedRoute from '@/app/components/ProtectedRoute'

export default function AdminLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {children}
      </div>
    </ProtectedRoute>
  )
}