'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { 
  MessageSquare, 
  Search, 
  Users, 
  Plus, 
  Settings, 
  User,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Shield
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/app/contexts/AuthContext'
import { cn } from '@/utils/cn'
import { ThreadHistory } from './thread-history'

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const pathname = usePathname()
  const router = useRouter()
  const { user, userTeamData, signOut } = useAuth()

  const isAdmin = userTeamData?.role === 'admin'

  const handleNewChat = () => {
    // Clear current thread and start fresh
    window.location.href = '/'
  }

  const toggleSearch = () => {
    setShowSearch(!showSearch)
    setSearchQuery('')
  }

  return (
    <div className={cn(
      "h-full bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col transition-all duration-300",
      isCollapsed ? "w-16" : "w-64"
    )}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Bali Chat
            </h2>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="ml-auto"
          >
            {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <Button 
          onClick={handleNewChat}
          className="w-full justify-start gap-2"
          variant="outline"
        >
          <Plus className="h-4 w-4" />
          {!isCollapsed && "New Chat"}
        </Button>
      </div>

      {/* Search */}
      <div className="px-4 pb-4">
        {showSearch && !isCollapsed ? (
          <div className="relative">
            <Input
              placeholder="Search chats..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pr-8"
            />
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSearch}
              className="absolute right-0 top-0 h-full"
            >
              <Search className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <Button
            variant="ghost"
            className={cn("w-full justify-start gap-2", isCollapsed && "justify-center")}
            onClick={toggleSearch}
          >
            <Search className="h-4 w-4" />
            {!isCollapsed && "Search Chats"}
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 pb-4">
        <div className="space-y-2">
          <Link href="/agents">
            <Button
              variant={pathname === '/agents' ? 'secondary' : 'ghost'}
              className={cn("w-full justify-start gap-2", isCollapsed && "justify-center")}
            >
              <Users className="h-4 w-4" />
              {!isCollapsed && "Agents & Prompts"}
            </Button>
          </Link>
        </div>

        {/* Chat History */}
        {!isCollapsed && (
          <div className="mt-6">
            <h3 className="mb-2 px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Recent Chats
            </h3>
            <div className="space-y-1 max-h-96 overflow-y-auto">
              <ThreadHistory searchQuery={searchQuery} />
            </div>
          </div>
        )}
      </nav>

      {/* Bottom Section - User Profile */}
      <div className="mt-auto border-t border-gray-200 dark:border-gray-800 p-4">
        <div className="space-y-2">
          {/* Settings */}
          <Link href="/settings">
            <Button
              variant="ghost"
              className={cn("w-full justify-start gap-2", isCollapsed && "justify-center")}
            >
              <Settings className="h-4 w-4" />
              {!isCollapsed && "Settings"}
            </Button>
          </Link>

          {/* Admin Link */}
          {isAdmin && (
            <Link href="/admin">
              <Button
                variant="ghost"
                className={cn("w-full justify-start gap-2", isCollapsed && "justify-center")}
              >
                <Shield className="h-4 w-4" />
                {!isCollapsed && "Admin"}
              </Button>
            </Link>
          )}

          {/* User Profile */}
          <div className={cn(
            "flex items-center gap-2 p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer",
            isCollapsed && "justify-center"
          )}>
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
              <User className="h-4 w-4 text-primary" />
            </div>
            {!isCollapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                  {user?.email?.split('@')[0] || 'User'}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {userTeamData?.team_name || 'Team Member'}
                </p>
              </div>
            )}
          </div>

          {/* Sign Out */}
          <Button
            variant="ghost"
            className={cn("w-full justify-start gap-2 text-red-600 hover:text-red-700 hover:bg-red-50", 
              isCollapsed && "justify-center"
            )}
            onClick={signOut}
          >
            <LogOut className="h-4 w-4" />
            {!isCollapsed && "Sign Out"}
          </Button>
        </div>
      </div>
    </div>
  )
}