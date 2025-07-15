import { useEffect, useState } from 'react'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { createClient } from '@/lib/supabase'

export interface UserPermissions {
  canCreateThreads: boolean
  canDeleteOwnThreads: boolean
  canViewTeamThreads: boolean
  canExportData: boolean
  canManageTeam: boolean
  maxThreadsPerDay: number
  allowedAgents: string[]
  allowedDataSources: string[]
  customPermissions: Record<string, any>
}

export function usePermissions() {
  const { user, userTeamData } = useAuth()
  const [permissions, setPermissions] = useState<UserPermissions | null>(null)
  const [loading, setLoading] = useState(true)
  const supabase = createClient()

  useEffect(() => {
    const fetchPermissions = async () => {
      if (!user?.email) {
        setLoading(false)
        return
      }

      try {
        // Fetch detailed permissions from user_permissions view
        const { data, error } = await supabase
          .from('user_permissions')
          .select('*')
          .eq('email', user.email)
          .single()

        if (error) {
          console.error('Error fetching permissions:', error)
          // Use default permissions from userTeamData
          if (userTeamData) {
            setPermissions({
              canCreateThreads: true,
              canDeleteOwnThreads: true,
              canViewTeamThreads: userTeamData.role === 'admin' || userTeamData.role === 'manager',
              canExportData: userTeamData.role === 'admin',
              canManageTeam: userTeamData.role === 'admin',
              maxThreadsPerDay: userTeamData.role === 'admin' ? 100 : 50,
              allowedAgents: userTeamData.allowed_agents || ['chat', 'search'],
              allowedDataSources: userTeamData.allowed_data_sources || ['public', 'company_wide'],
              customPermissions: {}
            })
          }
        } else if (data) {
          // Parse permissions from database
          const perms = data.permissions || {}
          setPermissions({
            canCreateThreads: perms.can_create_threads ?? true,
            canDeleteOwnThreads: perms.can_delete_own_threads ?? true,
            canViewTeamThreads: perms.can_view_team_threads ?? false,
            canExportData: perms.can_export_data ?? false,
            canManageTeam: perms.can_manage_team ?? false,
            maxThreadsPerDay: perms.max_threads_per_day ?? 50,
            allowedAgents: data.allowed_agents || ['chat', 'search'],
            allowedDataSources: data.allowed_data_sources || ['public', 'company_wide'],
            customPermissions: perms.custom_permissions || {}
          })
        }
      } catch (error) {
        console.error('Error in permission fetch:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchPermissions()
  }, [user, userTeamData])

  const hasAgent = (agentName: string): boolean => {
    return permissions?.allowedAgents.includes(agentName) ?? false
  }

  const hasDataSource = (sourceName: string): boolean => {
    return permissions?.allowedDataSources.includes(sourceName) ?? false
  }

  const checkCustomPermission = (permissionKey: string): boolean => {
    return permissions?.customPermissions[permissionKey] ?? false
  }

  return {
    permissions,
    loading,
    hasAgent,
    hasDataSource,
    checkCustomPermission
  }
}