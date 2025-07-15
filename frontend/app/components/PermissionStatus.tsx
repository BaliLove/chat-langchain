'use client'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { usePermissions } from '@/app/hooks/usePermissions'
import { Shield, Users, Database, Bot } from 'lucide-react'

export default function PermissionStatus() {
  const { user, userTeamData } = useAuth()
  const { permissions, loading } = usePermissions()

  if (loading || !permissions) {
    return null
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4 text-sm text-gray-300">
      <div className="flex items-center gap-2 mb-3">
        <Shield className="w-4 h-4" />
        <h3 className="font-semibold">Your Permissions</h3>
      </div>
      
      <div className="space-y-2">
        {/* User Info */}
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Email:</span>
          <span>{user?.email}</span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Team:</span>
          <span className="flex items-center gap-1">
            <Users className="w-3 h-3" />
            {userTeamData?.team_name || 'Bali Love'}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Role:</span>
          <span className="capitalize px-2 py-0.5 bg-blue-600 rounded text-xs">
            {userTeamData?.role || 'member'}
          </span>
        </div>

        <hr className="border-gray-700 my-2" />

        {/* Agents */}
        <div>
          <div className="flex items-center gap-1 text-gray-400 mb-1">
            <Bot className="w-3 h-3" />
            <span>Available Agents:</span>
          </div>
          <div className="flex flex-wrap gap-1 ml-4">
            {permissions.allowedAgents.map(agent => (
              <span key={agent} className="px-2 py-0.5 bg-gray-700 rounded text-xs">
                {agent}
              </span>
            ))}
          </div>
        </div>

        {/* Data Sources */}
        <div>
          <div className="flex items-center gap-1 text-gray-400 mb-1">
            <Database className="w-3 h-3" />
            <span>Data Access:</span>
          </div>
          <div className="flex flex-wrap gap-1 ml-4">
            {permissions.allowedDataSources.map(source => (
              <span key={source} className="px-2 py-0.5 bg-gray-700 rounded text-xs">
                {source.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>

        {/* Capabilities */}
        <div className="mt-2 space-y-1 text-xs">
          {permissions.canViewTeamThreads && (
            <div className="text-green-400">✓ Can view team threads</div>
          )}
          {permissions.canExportData && (
            <div className="text-green-400">✓ Can export data</div>
          )}
          {permissions.canManageTeam && (
            <div className="text-green-400">✓ Can manage team</div>
          )}
          <div className="text-gray-500">
            Daily thread limit: {permissions.maxThreadsPerDay}
          </div>
        </div>
      </div>
    </div>
  )
}