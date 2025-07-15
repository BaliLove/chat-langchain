'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { usePermissions } from '@/app/hooks/usePermissions'
import { createClient } from '@/lib/supabase'
import { Button } from '@/app/components/ui/button'
import { Input } from '@/app/components/ui/input'
import { Card, CardHeader, CardTitle, CardContent } from '@/app/components/ui/card'
import { Shield, Users, Search, Edit2, Trash2, Plus, RefreshCw } from 'lucide-react'
import { useToast } from '@/app/hooks/use-toast'
import AdminRoute from '@/app/components/AdminRoute'

interface UserTeamData {
  id: string
  email: string
  team_name: string
  role: string
  allowed_agents: string[]
  allowed_data_sources: string[]
  permissions: Record<string, any>
  updated_at: string
}

export const dynamic = 'force-dynamic'

export default function PermissionsAdminPage() {
  const { user, userTeamData, loading: authLoading } = useAuth()
  const { permissions, loading: permLoading } = usePermissions()
  const router = useRouter()
  const { toast } = useToast()
  const supabase = createClient()
  
  const [users, setUsers] = useState<UserTeamData[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [editingUser, setEditingUser] = useState<UserTeamData | null>(null)
  const [syncing, setSyncing] = useState(false)

  // Check if user is admin
  useEffect(() => {
    if (!authLoading && !permLoading) {
      // Get role from userTeamData in auth context
      const userRole = userTeamData?.role
      if (!user || userRole !== 'admin') {
        router.push('/')
        toast({
          title: "Access Denied",
          description: "You need admin permissions to access this page.",
          variant: "destructive"
        })
      }
    }
  }, [user, userTeamData, authLoading, permLoading, router, toast])

  // Fetch users
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const { data, error } = await supabase
          .from('user_teams')
          .select('*')
          .order('email')

        if (error) throw error
        setUsers(data || [])
      } catch (error) {
        console.error('Error fetching users:', error)
        toast({
          title: "Error",
          description: "Failed to load users",
          variant: "destructive"
        })
      } finally {
        setLoading(false)
      }
    }

    if (userTeamData?.role === 'admin') {
      fetchUsers()
    }
  }, [userTeamData, supabase, toast])

  const filteredUsers = users.filter(u => 
    u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.team_name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const updateUser = async (userId: string, updates: Partial<UserTeamData>) => {
    try {
      const { error } = await supabase
        .from('user_teams')
        .update(updates)
        .eq('id', userId)

      if (error) throw error

      toast({
        title: "Success",
        description: "User permissions updated"
      })

      // Refresh users
      const { data } = await supabase
        .from('user_teams')
        .select('*')
        .order('email')
      setUsers(data || [])
      setEditingUser(null)
    } catch (error) {
      console.error('Error updating user:', error)
      toast({
        title: "Error",
        description: "Failed to update user permissions",
        variant: "destructive"
      })
    }
  }

  const syncFromBubble = async () => {
    setSyncing(true)
    try {
      // This would call your sync endpoint
      const response = await fetch('/api/admin/sync-permissions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${await supabase.auth.getSession().then(s => s.data.session?.access_token)}`
        }
      })

      if (!response.ok) throw new Error('Sync failed')

      toast({
        title: "Success",
        description: "Permissions synced from Bubble"
      })

      // Refresh users
      const { data } = await supabase
        .from('user_teams')
        .select('*')
        .order('email')
      setUsers(data || [])
    } catch (error) {
      console.error('Error syncing:', error)
      toast({
        title: "Error",
        description: "Failed to sync permissions",
        variant: "destructive"
      })
    } finally {
      setSyncing(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <AdminRoute>
      <div className="container mx-auto p-6 max-w-7xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Shield className="w-8 h-8" />
          <h1 className="text-3xl font-bold">Permission Management</h1>
        </div>
        <Button 
          onClick={syncFromBubble}
          disabled={syncing}
          className="flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          Sync from Bubble
        </Button>
      </div>

      {/* Search */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search by email or team..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Users ({filteredUsers.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Email</th>
                  <th className="text-left p-2">Team</th>
                  <th className="text-left p-2">Role</th>
                  <th className="text-left p-2">Agents</th>
                  <th className="text-left p-2">Data Sources</th>
                  <th className="text-left p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map(user => (
                  <tr key={user.id} className="border-b hover:bg-gray-50">
                    <td className="p-2">{user.email}</td>
                    <td className="p-2">{user.team_name}</td>
                    <td className="p-2">
                      {editingUser?.id === user.id ? (
                        <select
                          value={editingUser.role}
                          onChange={(e) => setEditingUser({...editingUser, role: e.target.value})}
                          className="border rounded px-2 py-1"
                        >
                          <option value="member">Member</option>
                          <option value="manager">Manager</option>
                          <option value="admin">Admin</option>
                        </select>
                      ) : (
                        <span className={`px-2 py-1 rounded text-xs ${
                          user.role === 'admin' ? 'bg-red-100 text-red-800' :
                          user.role === 'manager' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {user.role}
                        </span>
                      )}
                    </td>
                    <td className="p-2">
                      <div className="flex flex-wrap gap-1">
                        {user.allowed_agents.map(agent => (
                          <span key={agent} className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                            {agent}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="p-2">
                      <div className="flex flex-wrap gap-1">
                        {user.allowed_data_sources.slice(0, 3).map(source => (
                          <span key={source} className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                            {source}
                          </span>
                        ))}
                        {user.allowed_data_sources.length > 3 && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                            +{user.allowed_data_sources.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="p-2">
                      <div className="flex gap-2">
                        {editingUser?.id === user.id ? (
                          <>
                            <Button
                              size="sm"
                              onClick={() => updateUser(user.id, editingUser)}
                            >
                              Save
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditingUser(null)}
                            >
                              Cancel
                            </Button>
                          </>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setEditingUser(user)}
                          >
                            <Edit2 className="w-3 h-3" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{users.filter(u => u.role === 'admin').length}</div>
            <p className="text-sm text-gray-500">Admins</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{users.filter(u => u.role === 'manager').length}</div>
            <p className="text-sm text-gray-500">Managers</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{users.filter(u => u.role === 'member').length}</div>
            <p className="text-sm text-gray-500">Members</p>
          </CardContent>
        </Card>
      </div>
    </div>
    </AdminRoute>
  )
}