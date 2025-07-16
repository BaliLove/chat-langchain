"use client"

import { useEffect, useState } from "react"
import { createClient } from "@/lib/supabase"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card"
import { Badge } from "@/app/components/ui/badge"
import { Button } from "@/app/components/ui/button"
import { Input } from "@/app/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs"
import { Avatar, AvatarFallback } from "@/app/components/ui/avatar"
import { Users, Shield, Database, Bot, Search, Filter, ChevronDown, ChevronRight, UserCheck } from "lucide-react"
import AdminRoute from "@/app/components/AdminRoute"
import { toast } from "@/app/components/ui/use-toast"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/app/components/ui/table"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/app/components/ui/collapsible"
import { MemberDetailsModal } from "./MemberDetailsModal"

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

interface TeamGroup {
  team_id: string
  team_name: string
  members: TeamMember[]
}

export default function TeamMembersPage() {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([])
  const [teamGroups, setTeamGroups] = useState<TeamGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [filterRole, setFilterRole] = useState<string>("all")
  const [expandedTeams, setExpandedTeams] = useState<Set<string>>(new Set())
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null)
  const [detailsModalOpen, setDetailsModalOpen] = useState(false)
  const supabase = createClient()

  useEffect(() => {
    fetchTeamMembers()
  }, [])

  const fetchTeamMembers = async () => {
    try {
      const { data, error } = await supabase
        .from('user_teams')
        .select('*')
        .order('team_name', { ascending: true })
        .order('role', { ascending: true })

      if (error) throw error

      setTeamMembers(data || [])
      
      // Group by teams
      const groups = data?.reduce((acc: Record<string, TeamGroup>, member) => {
        if (!acc[member.team_id]) {
          acc[member.team_id] = {
            team_id: member.team_id,
            team_name: member.team_name,
            members: []
          }
        }
        acc[member.team_id].members.push(member)
        return acc
      }, {}) || {}

      setTeamGroups(Object.values(groups))
    } catch (error) {
      console.error('Error fetching team members:', error)
      toast({
        title: "Error",
        description: "Failed to load team members",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const toggleTeam = (teamId: string) => {
    const newExpanded = new Set(expandedTeams)
    if (newExpanded.has(teamId)) {
      newExpanded.delete(teamId)
    } else {
      newExpanded.add(teamId)
    }
    setExpandedTeams(newExpanded)
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

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin':
        return <Shield className="h-3 w-3" />
      case 'manager':
        return <Users className="h-3 w-3" />
      default:
        return <UserCheck className="h-3 w-3" />
    }
  }

  const filteredMembers = teamMembers.filter(member => {
    const matchesSearch = member.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         member.team_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = filterRole === "all" || member.role === filterRole
    return matchesSearch && matchesRole
  })

  const filteredGroups = teamGroups.map(group => ({
    ...group,
    members: group.members.filter(member => {
      const matchesSearch = member.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           member.team_name.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesRole = filterRole === "all" || member.role === filterRole
      return matchesSearch && matchesRole
    })
  })).filter(group => group.members.length > 0)

  const getAccessSummary = (member: TeamMember) => {
    const agentCount = member.allowed_agents?.length || 0
    const dataSourceCount = member.allowed_data_sources?.length || 0
    
    if (member.role === 'admin') {
      return "Full access to all agents and data sources"
    }
    
    return `${agentCount} agents, ${dataSourceCount} data sources`
  }

  return (
    <AdminRoute>
      <div className="flex-1 w-full max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Team Members</h1>
          <p className="text-muted-foreground">
            View all team members, their roles, and access permissions
          </p>
        </div>

        {/* Stats Overview */}
        <div className="grid gap-4 md:grid-cols-4 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Members</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{teamMembers.length}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Teams</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{teamGroups.length}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Admins</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {teamMembers.filter(m => m.role === 'admin').length}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Managers</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {teamMembers.filter(m => m.role === 'manager').length}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by email or team name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant={filterRole === "all" ? "default" : "outline"}
              onClick={() => setFilterRole("all")}
              size="sm"
            >
              All
            </Button>
            <Button
              variant={filterRole === "admin" ? "default" : "outline"}
              onClick={() => setFilterRole("admin")}
              size="sm"
            >
              Admins
            </Button>
            <Button
              variant={filterRole === "manager" ? "default" : "outline"}
              onClick={() => setFilterRole("manager")}
              size="sm"
            >
              Managers
            </Button>
            <Button
              variant={filterRole === "member" ? "default" : "outline"}
              onClick={() => setFilterRole("member")}
              size="sm"
            >
              Members
            </Button>
          </div>
        </div>

        {/* View Tabs */}
        <Tabs defaultValue="by-team" className="space-y-4">
          <TabsList>
            <TabsTrigger value="by-team">By Team</TabsTrigger>
            <TabsTrigger value="all-members">All Members</TabsTrigger>
          </TabsList>

          {/* By Team View */}
          <TabsContent value="by-team" className="space-y-4">
            {loading ? (
              <Card>
                <CardContent className="flex items-center justify-center py-8">
                  <p className="text-muted-foreground">Loading team members...</p>
                </CardContent>
              </Card>
            ) : filteredGroups.length === 0 ? (
              <Card>
                <CardContent className="flex items-center justify-center py-8">
                  <p className="text-muted-foreground">No team members found</p>
                </CardContent>
              </Card>
            ) : (
              filteredGroups.map((group) => (
                <Card key={group.team_id}>
                  <Collapsible
                    open={expandedTeams.has(group.team_id)}
                    onOpenChange={() => toggleTeam(group.team_id)}
                  >
                    <CollapsibleTrigger asChild>
                      <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                              {expandedTeams.has(group.team_id) ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                              <CardTitle className="text-lg">{group.team_name}</CardTitle>
                            </div>
                            <Badge variant="outline">{group.members.length} members</Badge>
                          </div>
                          <div className="flex gap-2">
                            {group.members.some(m => m.role === 'admin') && (
                              <Badge variant="destructive" className="text-xs">
                                {group.members.filter(m => m.role === 'admin').length} admin(s)
                              </Badge>
                            )}
                            {group.members.some(m => m.role === 'manager') && (
                              <Badge variant="default" className="text-xs">
                                {group.members.filter(m => m.role === 'manager').length} manager(s)
                              </Badge>
                            )}
                          </div>
                        </div>
                      </CardHeader>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Member</TableHead>
                              <TableHead>Role</TableHead>
                              <TableHead>Access</TableHead>
                              <TableHead>Agents</TableHead>
                              <TableHead>Data Sources</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {group.members.map((member) => (
                              <TableRow 
                                key={member.email}
                                className="cursor-pointer hover:bg-muted/50"
                                onClick={() => {
                                  setSelectedMember(member)
                                  setDetailsModalOpen(true)
                                }}
                              >
                                <TableCell>
                                  <div className="flex items-center gap-3">
                                    <Avatar className="h-8 w-8">
                                      <AvatarFallback>
                                        {member.email.substring(0, 2).toUpperCase()}
                                      </AvatarFallback>
                                    </Avatar>
                                    <div>
                                      <p className="font-medium">{member.email}</p>
                                      <p className="text-xs text-muted-foreground">
                                        Joined {new Date(member.created_at).toLocaleDateString()}
                                      </p>
                                    </div>
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <Badge variant={getRoleBadgeColor(member.role)}>
                                    <span className="flex items-center gap-1">
                                      {getRoleIcon(member.role)}
                                      {member.role}
                                    </span>
                                  </Badge>
                                </TableCell>
                                <TableCell>
                                  <p className="text-sm text-muted-foreground">
                                    {getAccessSummary(member)}
                                  </p>
                                </TableCell>
                                <TableCell>
                                  <div className="flex flex-wrap gap-1">
                                    {member.allowed_agents?.slice(0, 3).map((agent) => (
                                      <Badge key={agent} variant="outline" className="text-xs">
                                        <Bot className="h-3 w-3 mr-1" />
                                        {agent}
                                      </Badge>
                                    ))}
                                    {member.allowed_agents?.length > 3 && (
                                      <Badge variant="outline" className="text-xs">
                                        +{member.allowed_agents.length - 3} more
                                      </Badge>
                                    )}
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <div className="flex flex-wrap gap-1">
                                    {member.allowed_data_sources?.slice(0, 3).map((source) => (
                                      <Badge key={source} variant="outline" className="text-xs">
                                        <Database className="h-3 w-3 mr-1" />
                                        {source}
                                      </Badge>
                                    ))}
                                    {member.allowed_data_sources?.length > 3 && (
                                      <Badge variant="outline" className="text-xs">
                                        +{member.allowed_data_sources.length - 3} more
                                      </Badge>
                                    )}
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </CollapsibleContent>
                  </Collapsible>
                </Card>
              ))
            )}
          </TabsContent>

          {/* All Members View */}
          <TabsContent value="all-members">
            <Card>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Member</TableHead>
                      <TableHead>Team</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Access</TableHead>
                      <TableHead>Agents & Data Sources</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredMembers.map((member) => (
                      <TableRow 
                        key={member.email}
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => {
                          setSelectedMember(member)
                          setDetailsModalOpen(true)
                        }}
                      >
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Avatar className="h-8 w-8">
                              <AvatarFallback>
                                {member.email.substring(0, 2).toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="font-medium">{member.email}</p>
                              <p className="text-xs text-muted-foreground">
                                Joined {new Date(member.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{member.team_name}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getRoleBadgeColor(member.role)}>
                            <span className="flex items-center gap-1">
                              {getRoleIcon(member.role)}
                              {member.role}
                            </span>
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <p className="text-sm text-muted-foreground">
                            {getAccessSummary(member)}
                          </p>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <Bot className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">
                                {member.allowed_agents?.length || 0} agents
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Database className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">
                                {member.allowed_data_sources?.length || 0} data sources
                              </span>
                            </div>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
        
        <MemberDetailsModal 
          member={selectedMember}
          open={detailsModalOpen}
          onOpenChange={setDetailsModalOpen}
        />
      </div>
    </AdminRoute>
  )
}