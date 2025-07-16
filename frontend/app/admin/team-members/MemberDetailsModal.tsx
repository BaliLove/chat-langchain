import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/app/components/ui/dialog"
import { Badge } from "@/app/components/ui/badge"
import { Avatar, AvatarFallback } from "@/app/components/ui/avatar"
import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Shield, Users, UserCheck, Bot, Database, Calendar, Clock, CheckCircle, XCircle } from "lucide-react"

interface TeamMember {
  email: string
  team_id: string
  team_name: string
  role: 'admin' | 'manager' | 'member'
  allowed_agents: string[]
  allowed_data_sources: string[]
  created_at: string
  last_sign_in_at?: string
}

interface MemberDetailsModalProps {
  member: TeamMember | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function MemberDetailsModal({ member, open, onOpenChange }: MemberDetailsModalProps) {
  if (!member) return null

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin':
        return <Shield className="h-4 w-4" />
      case 'manager':
        return <Users className="h-4 w-4" />
      default:
        return <UserCheck className="h-4 w-4" />
    }
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'destructive'
      case 'manager':
        return 'default'
      case 'member':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  const getPermissionsForRole = (role: string) => {
    switch (role) {
      case 'admin':
        return {
          canCreateThreads: true,
          canDeleteOwnThreads: true,
          canViewTeamThreads: true,
          canExportData: true,
          canManageTeam: true,
          canAccessAllAgents: true,
          canAccessAllDataSources: true,
        }
      case 'manager':
        return {
          canCreateThreads: true,
          canDeleteOwnThreads: true,
          canViewTeamThreads: true,
          canExportData: true,
          canManageTeam: false,
          canAccessAllAgents: false,
          canAccessAllDataSources: false,
        }
      default:
        return {
          canCreateThreads: true,
          canDeleteOwnThreads: true,
          canViewTeamThreads: false,
          canExportData: false,
          canManageTeam: false,
          canAccessAllAgents: false,
          canAccessAllDataSources: false,
        }
    }
  }

  const permissions = getPermissionsForRole(member.role)

  // Common agents and data sources in Bali Love system
  const allAgents = [
    'researcher', 
    'message-finder', 
    'event-analyzer', 
    'vendor-search',
    'issue-tracker',
    'training-assistant'
  ]

  const allDataSources = [
    'events',
    'inbox_messages', 
    'vendors',
    'venues',
    'issues',
    'training',
    'guests',
    'products'
  ]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Member Details</DialogTitle>
          <DialogDescription>
            Complete access and permission details for this team member
          </DialogDescription>
        </DialogHeader>

        <div className="max-h-[calc(90vh-120px)] overflow-y-auto pr-4">
          <div className="space-y-6">
            {/* Member Info */}
            <div className="flex items-start gap-4">
              <Avatar className="h-12 w-12">
                <AvatarFallback className="text-lg">
                  {member.email.substring(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 space-y-1">
                <h3 className="font-semibold text-lg">{member.email}</h3>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {member.team_name}
                  </span>
                  <Badge variant={getRoleBadgeColor(member.role)}>
                    <span className="flex items-center gap-1">
                      {getRoleIcon(member.role)}
                      {member.role}
                    </span>
                  </Badge>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    Joined {new Date(member.created_at).toLocaleDateString()}
                  </span>
                  {member.last_sign_in_at && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      Last active {new Date(member.last_sign_in_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200"></div>

            {/* Permissions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Permissions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2">
                    {permissions.canCreateThreads ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className="text-sm">Create conversations</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {permissions.canDeleteOwnThreads ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className="text-sm">Delete own conversations</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {permissions.canViewTeamThreads ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className="text-sm">View team conversations</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {permissions.canExportData ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className="text-sm">Export data</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {permissions.canManageTeam ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className="text-sm">Manage team settings</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {permissions.canAccessAllAgents ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className="text-sm">Access all agents</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Agents Access */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Bot className="h-4 w-4" />
                  Agent Access
                </CardTitle>
              </CardHeader>
              <CardContent>
                {member.role === 'admin' ? (
                  <p className="text-sm text-muted-foreground mb-3">
                    Full access to all agents as an admin
                  </p>
                ) : member.allowed_agents?.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No specific agent access configured
                  </p>
                ) : null}
                
                <div className="grid grid-cols-2 gap-2">
                  {allAgents.map((agent) => {
                    const hasAccess = member.role === 'admin' || member.allowed_agents?.includes(agent)
                    return (
                      <div key={agent} className="flex items-center gap-2">
                        {hasAccess ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <XCircle className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className={`text-sm ${!hasAccess && 'text-muted-foreground'}`}>
                          {agent}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Data Sources Access */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Database className="h-4 w-4" />
                  Data Source Access
                </CardTitle>
              </CardHeader>
              <CardContent>
                {member.role === 'admin' ? (
                  <p className="text-sm text-muted-foreground mb-3">
                    Full access to all data sources as an admin
                  </p>
                ) : member.allowed_data_sources?.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No specific data source access configured
                  </p>
                ) : null}
                
                <div className="grid grid-cols-2 gap-2">
                  {allDataSources.map((source) => {
                    const hasAccess = member.role === 'admin' || member.allowed_data_sources?.includes(source)
                    return (
                      <div key={source} className="flex items-center gap-2">
                        {hasAccess ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <XCircle className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className={`text-sm ${!hasAccess && 'text-muted-foreground'}`}>
                          {source}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Access Summary */}
            <Card className="bg-muted/50">
              <CardHeader>
                <CardTitle className="text-base">Access Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  {member.role === 'admin' ? (
                    <>
                      As an <strong>admin</strong>, this user has full access to all features, 
                      can manage team settings, view all team conversations, and access all agents 
                      and data sources without restrictions.
                    </>
                  ) : member.role === 'manager' ? (
                    <>
                      As a <strong>manager</strong>, this user can view team conversations and 
                      export data, but has restricted access to only {member.allowed_agents?.length || 0} agents 
                      and {member.allowed_data_sources?.length || 0} data sources.
                    </>
                  ) : (
                    <>
                      As a <strong>member</strong>, this user has basic access with restricted 
                      permissions. They can only access {member.allowed_agents?.length || 0} agents 
                      and {member.allowed_data_sources?.length || 0} data sources.
                    </>
                  )}
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}