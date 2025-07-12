// Team & Permission Management Types

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  logo_url?: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

export interface Role {
  id: string;
  name: string;
  slug: string;
  description?: string;
  permissions: Permission[];
  is_system: boolean;
  created_at: string;
}

export interface Permission {
  resource: 'organization' | 'agent' | 'data_source' | 'user' | 'role' | '*';
  action: 'create' | 'read' | 'update' | 'delete' | 'use' | 'manage' | '*';
  conditions?: Record<string, any>;
}

export interface OrganizationMember {
  id: string;
  organization_id: string;
  user_id: string;
  role_id: string;
  joined_at: string;
  invited_by?: string;
  status: 'active' | 'invited' | 'suspended';
  // Relations
  user?: UserProfile;
  role?: Role;
  organization?: Organization;
}

export interface Agent {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  config: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface AgentPermission {
  id: string;
  agent_id: string;
  role_id?: string;
  user_id?: string;
  permissions: Permission[];
  created_at: string;
}

export interface DataSource {
  id: string;
  organization_id: string;
  name: string;
  type: 'bubble' | 'google_drive' | 'notion' | 'custom';
  config: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DataAccessPermission {
  id: string;
  data_source_id: string;
  role_id?: string;
  user_id?: string;
  access_level: 'read' | 'write' | 'admin';
  filters: Record<string, any>;
  created_at: string;
}

export interface GoogleWorkspaceSync {
  id: string;
  organization_id: string;
  domain: string;
  last_sync_at?: string;
  sync_config: GoogleWorkspaceSyncConfig;
  sync_status: 'pending' | 'syncing' | 'completed' | 'failed';
  error_details?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface GoogleWorkspaceSyncConfig {
  service_account_key?: string;
  admin_email?: string;
  sync_groups?: boolean;
  sync_org_units?: boolean;
  group_role_mapping?: Record<string, string>;
}

export interface PermissionAuditLog {
  id: string;
  organization_id?: string;
  user_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  old_value?: Record<string, any>;
  new_value?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

// System roles enum
export enum SystemRoles {
  OWNER = 'owner',
  ADMIN = 'admin',
  MEMBER = 'member',
  GUEST = 'guest'
}

// Helper types
export interface PermissionCheck {
  resource: string;
  action: string;
  allowed: boolean;
}

export interface InviteUserRequest {
  email: string;
  role_id: string;
  organization_id: string;
}

export interface UpdateUserRoleRequest {
  user_id: string;
  role_id: string;
  organization_id: string;
}

export interface CreateOrganizationRequest {
  name: string;
  slug: string;
  description?: string;
}

export interface GoogleWorkspaceSyncRequest {
  organization_id: string;
  domain: string;
  config: GoogleWorkspaceSyncConfig;
}