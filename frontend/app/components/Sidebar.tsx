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
  Shield,
  MoreVertical,
  FileText
} from 'lucide-react'
import { Button } from '@/app/components/ui/button'
import { Input } from '@/app/components/ui/input'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { cn } from '@/app/utils/cn'
import { ThreadHistory } from './thread-history'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/app/components/ui/dropdown-menu'

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
      "h-full bg-background border-r border-border flex flex-col transition-all duration-300",
      isCollapsed ? "w-16" : "w-64"
    )}>
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <h2 className="text-lg font-semibold text-foreground">
              LoveGPT
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
          
          <Link href="/issues">
            <Button
              variant={pathname === '/issues' ? 'secondary' : 'ghost'}
              className={cn("w-full justify-start gap-2", isCollapsed && "justify-center")}
            >
              <FileText className="h-4 w-4" />
              {!isCollapsed && "Issue Reviews"}
            </Button>
          </Link>
        </div>

        {/* Chat History */}
        {!isCollapsed && (
          <div className="mt-6">
            <h3 className="mb-2 px-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Recent Chats
            </h3>
            <div className="space-y-1 max-h-96 overflow-y-auto">
              <ThreadHistory />
            </div>
          </div>
        )}
      </nav>

      {/* Bottom Section - User Profile */}
      <div className="mt-auto border-t border-border">
        {/* User Profile */}
        <div className={cn(
          "flex items-center gap-3 p-4",
          isCollapsed && "justify-center px-2"
        )}>
          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
            <User className="h-5 w-5 text-primary" />
          </div>
          {!isCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">
                {user?.email?.split('@')[0] || 'User'}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {userTeamData?.team_name || 'Team Member'} • {userTeamData?.role || 'member'}
              </p>
            </div>
          )}
          
          {/* More Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 ml-auto"
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align={isCollapsed ? "center" : "end"} side="top" className="w-56">
              {/* Admin Link */}
              {isAdmin && (
                <>
                  <DropdownMenuItem asChild>
                    <Link href="/admin" className="flex items-center cursor-pointer">
                      <Shield className="mr-2 h-4 w-4" />
                      Admin Panel
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                </>
              )}
              
              {/* Settings */}
              <DropdownMenuItem asChild>
                <Link href="/settings" className="flex items-center cursor-pointer">
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </Link>
              </DropdownMenuItem>
              
              <DropdownMenuSeparator />
              
              {/* Sign Out */}
              <DropdownMenuItem 
                onClick={signOut}
                className="text-destructive focus:text-destructive cursor-pointer"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Sign Out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  )
}