'use client'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { Button } from './ui/button'
import { LogOut, User, Shield } from 'lucide-react'
import Link from 'next/link'

export default function Header() {
  const { user, userTeamData, signOut, isAuthorized } = useAuth()

  if (!user || !isAuthorized) return null

  return (
    <header className="bg-gray-900 border-b border-gray-800">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-white text-lg font-semibold">Bali Love Chat</h1>
            {userTeamData && (
              <span className="ml-4 text-sm text-gray-400">
                {userTeamData.team_name} • {userTeamData.role}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            {userTeamData?.role === 'admin' && (
              <Link href="/admin/permissions">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-gray-300 hover:text-white hover:bg-gray-800"
                >
                  <Shield className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">Admin</span>
                </Button>
              </Link>
            )}
            
            <div className="flex items-center text-sm text-gray-300">
              <User className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">{user.email}</span>
            </div>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={signOut}
              className="text-gray-300 hover:text-white hover:bg-gray-800"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}