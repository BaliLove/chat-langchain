# Team & Permission Management System Design

## Overview

This document outlines a comprehensive permission and team management system for the bali.love chat application. The system is designed to be scalable, secure, and incrementally implementable.

## 1. Database Schema Design

### Core Tables Structure

```sql
-- User profiles (extending Supabase auth.users)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Organizations/Teams
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    logo_url TEXT,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Roles definition
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(slug)
);

-- User-Organization relationships
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    invited_by UUID REFERENCES auth.users(id),
    status TEXT CHECK (status IN ('active', 'invited', 'suspended')) DEFAULT 'active',
    UNIQUE(organization_id, user_id)
);

-- Agent/Assistant definitions
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Agent permissions
CREATE TABLE agent_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id),
    user_id UUID REFERENCES auth.users(id),
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_role_or_user CHECK (
        (role_id IS NOT NULL AND user_id IS NULL) OR 
        (role_id IS NULL AND user_id IS NOT NULL)
    )
);

-- Data sources
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('bubble', 'google_drive', 'notion', 'custom')),
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Data access permissions
CREATE TABLE data_access_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id),
    user_id UUID REFERENCES auth.users(id),
    access_level TEXT NOT NULL CHECK (access_level IN ('read', 'write', 'admin')),
    filters JSONB DEFAULT '{}'::jsonb, -- For row-level filtering
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_role_or_user CHECK (
        (role_id IS NOT NULL AND user_id IS NULL) OR 
        (role_id IS NULL AND user_id IS NOT NULL)
    )
);

-- Google Workspace sync data
CREATE TABLE google_workspace_sync (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    domain TEXT NOT NULL,
    last_sync_at TIMESTAMPTZ,
    sync_config JSONB DEFAULT '{}'::jsonb,
    sync_status TEXT CHECK (sync_status IN ('pending', 'syncing', 'completed', 'failed')),
    error_details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit log for permission changes
CREATE TABLE permission_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id),
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Indexes for Performance

```sql
-- Performance indexes
CREATE INDEX idx_org_members_org_id ON organization_members(organization_id);
CREATE INDEX idx_org_members_user_id ON organization_members(user_id);
CREATE INDEX idx_agent_permissions_agent_id ON agent_permissions(agent_id);
CREATE INDEX idx_data_access_source_id ON data_access_permissions(data_source_id);
CREATE INDEX idx_audit_log_org_id ON permission_audit_log(organization_id);
CREATE INDEX idx_audit_log_created_at ON permission_audit_log(created_at DESC);
```

## 2. Permission Model

### Default System Roles

```typescript
enum SystemRoles {
  OWNER = 'owner',           // Full access to everything
  ADMIN = 'admin',           // Manage users, agents, data sources
  MEMBER = 'member',         // Use agents, access allowed data
  GUEST = 'guest'            // Limited read-only access
}

// Permission structure
interface Permission {
  resource: 'organization' | 'agent' | 'data_source' | 'user' | 'role';
  action: 'create' | 'read' | 'update' | 'delete' | 'use' | 'manage';
  conditions?: Record<string, any>; // For conditional permissions
}

// Default permissions by role
const DEFAULT_PERMISSIONS: Record<SystemRoles, Permission[]> = {
  [SystemRoles.OWNER]: [
    { resource: '*', action: '*' } // Full access
  ],
  [SystemRoles.ADMIN]: [
    { resource: 'organization', action: 'read' },
    { resource: 'organization', action: 'update' },
    { resource: 'agent', action: '*' },
    { resource: 'data_source', action: '*' },
    { resource: 'user', action: '*' },
    { resource: 'role', action: 'read' }
  ],
  [SystemRoles.MEMBER]: [
    { resource: 'organization', action: 'read' },
    { resource: 'agent', action: 'read' },
    { resource: 'agent', action: 'use' },
    { resource: 'data_source', action: 'read', conditions: { assigned: true } }
  ],
  [SystemRoles.GUEST]: [
    { resource: 'organization', action: 'read' },
    { resource: 'agent', action: 'read', conditions: { public: true } }
  ]
};
```

## 3. Row Level Security (RLS) Policies

### Supabase RLS Implementation

```sql
-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;

-- User profiles: Users can only see profiles in their organizations
CREATE POLICY "Users can view profiles in their organizations" ON user_profiles
  FOR SELECT USING (
    auth.uid() = id OR
    EXISTS (
      SELECT 1 FROM organization_members om1
      WHERE om1.user_id = auth.uid()
      AND EXISTS (
        SELECT 1 FROM organization_members om2
        WHERE om2.user_id = user_profiles.id
        AND om2.organization_id = om1.organization_id
      )
    )
  );

-- Organizations: Users can only see organizations they belong to
CREATE POLICY "Users can view their organizations" ON organizations
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM organization_members
      WHERE organization_members.user_id = auth.uid()
      AND organization_members.organization_id = organizations.id
    )
  );

-- Agents: Access based on organization membership and permissions
CREATE POLICY "Users can view agents in their organizations" ON agents
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM organization_members om
      JOIN roles r ON om.role_id = r.id
      WHERE om.user_id = auth.uid()
      AND om.organization_id = agents.organization_id
      AND (
        r.permissions @> '[{"resource": "agent", "action": "read"}]'::jsonb
        OR EXISTS (
          SELECT 1 FROM agent_permissions ap
          WHERE ap.agent_id = agents.id
          AND ap.user_id = auth.uid()
        )
      )
    )
  );

-- Function to check permissions
CREATE OR REPLACE FUNCTION check_permission(
  p_user_id UUID,
  p_organization_id UUID,
  p_resource TEXT,
  p_action TEXT
) RETURNS BOOLEAN AS $$
DECLARE
  v_has_permission BOOLEAN;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM organization_members om
    JOIN roles r ON om.role_id = r.id
    WHERE om.user_id = p_user_id
    AND om.organization_id = p_organization_id
    AND om.status = 'active'
    AND (
      r.permissions @> json_build_array(
        json_build_object(
          'resource', p_resource,
          'action', p_action
        )
      )::jsonb
      OR r.permissions @> json_build_array(
        json_build_object(
          'resource', '*',
          'action', '*'
        )
      )::jsonb
    )
  ) INTO v_has_permission;
  
  RETURN v_has_permission;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## 4. Data Source Integration

### Google Workspace Integration

```typescript
// Google Workspace sync service
interface GoogleWorkspaceConfig {
  domain: string;
  serviceAccountKey: string;
  adminEmail: string;
  syncGroups: boolean;
  syncOrgUnits: boolean;
}

class GoogleWorkspaceSync {
  async syncOrganization(organizationId: string, config: GoogleWorkspaceConfig) {
    // 1. Authenticate with Google Admin SDK
    const auth = await this.authenticateGoogle(config);
    
    // 2. Fetch users from Google Workspace
    const users = await this.fetchGoogleUsers(auth, config.domain);
    
    // 3. Fetch groups if enabled
    const groups = config.syncGroups ? 
      await this.fetchGoogleGroups(auth, config.domain) : [];
    
    // 4. Map Google groups to roles
    const roleMapping = await this.mapGroupsToRoles(groups);
    
    // 5. Sync users to database
    await this.syncUsersToDatabase(organizationId, users, roleMapping);
    
    // 6. Update sync status
    await this.updateSyncStatus(organizationId, 'completed');
  }
  
  private async syncUsersToDatabase(
    organizationId: string, 
    users: GoogleUser[], 
    roleMapping: Map<string, string>
  ) {
    for (const user of users) {
      // Create or update user profile
      const dbUser = await this.createOrUpdateUser(user);
      
      // Add to organization with appropriate role
      const roleId = this.determineUserRole(user, roleMapping);
      await this.addUserToOrganization(
        organizationId, 
        dbUser.id, 
        roleId
      );
    }
  }
}
```

### Manual Team Management API

```typescript
// API endpoints for manual team management
export const teamManagementAPI = {
  // Invite user to organization
  async inviteUser(req: Request) {
    const { email, roleId, organizationId } = req.body;
    
    // Check permissions
    if (!await checkPermission(req.user.id, organizationId, 'user', 'create')) {
      throw new ForbiddenError();
    }
    
    // Create invitation
    const invitation = await createInvitation({
      email,
      roleId,
      organizationId,
      invitedBy: req.user.id
    });
    
    // Send invitation email
    await sendInvitationEmail(invitation);
    
    return { success: true, invitation };
  },
  
  // Update user role
  async updateUserRole(req: Request) {
    const { userId, roleId, organizationId } = req.body;
    
    // Check permissions
    if (!await checkPermission(req.user.id, organizationId, 'user', 'update')) {
      throw new ForbiddenError();
    }
    
    // Update role
    await updateOrganizationMember({
      userId,
      organizationId,
      roleId
    });
    
    // Audit log
    await createAuditLog({
      userId: req.user.id,
      action: 'update_user_role',
      resourceType: 'user',
      resourceId: userId,
      organizationId
    });
    
    return { success: true };
  }
};
```

## 5. Implementation Plan

### Phase 1: Core Infrastructure (Week 1-2)
1. Create database schema and migrations
2. Implement basic RLS policies
3. Create system roles and default permissions
4. Build authentication context extensions

### Phase 2: Manual Team Management (Week 3-4)
1. Build UI for organization creation
2. Implement user invitation system
3. Create role management interface
4. Add basic permission checks

### Phase 3: Google Workspace Integration (Week 5-6)
1. Set up Google Admin SDK integration
2. Implement sync service
3. Create sync scheduling system
4. Build sync status UI

### Phase 4: Agent & Data Permissions (Week 7-8)
1. Implement agent permission system
2. Create data source access controls
3. Build permission management UI
4. Add audit logging

### Phase 5: Advanced Features (Week 9-10)
1. Implement conditional permissions
2. Add bulk permission management
3. Create permission templates
4. Build analytics dashboard

## 6. Security Considerations

### API Security
```typescript
// Middleware for permission checking
export const requirePermission = (resource: string, action: string) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    const organizationId = req.params.organizationId || req.body.organizationId;
    
    if (!organizationId) {
      return res.status(400).json({ error: 'Organization ID required' });
    }
    
    const hasPermission = await checkPermission(
      req.user.id,
      organizationId,
      resource,
      action
    );
    
    if (!hasPermission) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }
    
    next();
  };
};

// Rate limiting for sensitive operations
export const rateLimiter = {
  permissionChanges: rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 10 // Max 10 permission changes per window
  }),
  
  userInvitations: rateLimit({
    windowMs: 60 * 60 * 1000, // 1 hour
    max: 50 // Max 50 invitations per hour
  })
};
```

### Data Isolation
```typescript
// Ensure complete data isolation between organizations
export const dataIsolationMiddleware = async (
  req: Request, 
  res: Response, 
  next: NextFunction
) => {
  // Add organization context to all queries
  req.organizationContext = {
    id: req.params.organizationId,
    userId: req.user.id,
    permissions: await getUserPermissions(req.user.id, req.params.organizationId)
  };
  
  // Override database client to include org filter
  req.db = createScopedDatabaseClient(req.organizationContext);
  
  next();
};
```

## 7. Frontend Integration

### React Context for Permissions
```typescript
// Extended Auth Context
interface TeamAuthContextType extends AuthContextType {
  currentOrganization: Organization | null;
  organizations: Organization[];
  permissions: Permission[];
  hasPermission: (resource: string, action: string) => boolean;
  switchOrganization: (organizationId: string) => Promise<void>;
}

// Permission hook
export const usePermission = (resource: string, action: string) => {
  const { hasPermission } = useTeamAuth();
  return hasPermission(resource, action);
};

// Protected component wrapper
export const RequirePermission: React.FC<{
  resource: string;
  action: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}> = ({ resource, action, fallback, children }) => {
  const hasPermission = usePermission(resource, action);
  
  if (!hasPermission) {
    return fallback || <div>You don't have permission to view this.</div>;
  }
  
  return <>{children}</>;
};
```

## 8. Migration Strategy

### For Existing Users
```sql
-- Migration script to move existing users to new system
BEGIN;

-- Create default organization for existing users
INSERT INTO organizations (name, slug, created_by)
SELECT 
  COALESCE(split_part(email, '@', 2), 'default-org') as name,
  COALESCE(split_part(email, '@', 2), 'default-org') as slug,
  id as created_by
FROM auth.users
WHERE NOT EXISTS (
  SELECT 1 FROM organization_members WHERE user_id = auth.users.id
);

-- Add existing users as owners of their default organizations
INSERT INTO organization_members (organization_id, user_id, role_id)
SELECT 
  o.id,
  u.id,
  (SELECT id FROM roles WHERE slug = 'owner')
FROM auth.users u
JOIN organizations o ON o.created_by = u.id
WHERE NOT EXISTS (
  SELECT 1 FROM organization_members 
  WHERE user_id = u.id AND organization_id = o.id
);

COMMIT;
```

## 9. Monitoring & Analytics

### Permission Usage Analytics
```sql
-- View to track permission usage
CREATE VIEW permission_usage_stats AS
SELECT 
  o.name as organization_name,
  r.name as role_name,
  jsonb_array_elements(r.permissions)->>'resource' as resource,
  jsonb_array_elements(r.permissions)->>'action' as action,
  COUNT(DISTINCT om.user_id) as user_count
FROM organizations o
JOIN organization_members om ON o.id = om.organization_id
JOIN roles r ON om.role_id = r.id
GROUP BY o.name, r.name, resource, action;

-- Audit trail analysis
CREATE VIEW security_events AS
SELECT 
  pal.created_at,
  o.name as organization_name,
  up.email as user_email,
  pal.action,
  pal.resource_type,
  pal.ip_address
FROM permission_audit_log pal
JOIN organizations o ON pal.organization_id = o.id
JOIN user_profiles up ON pal.user_id = up.id
WHERE pal.created_at > NOW() - INTERVAL '30 days'
ORDER BY pal.created_at DESC;
```

## 10. Best Practices

1. **Principle of Least Privilege**: Always grant minimum necessary permissions
2. **Regular Audits**: Schedule monthly permission audits
3. **Separation of Duties**: Don't allow users to approve their own permission changes
4. **Time-based Access**: Implement temporary permissions for contractors
5. **Emergency Access**: Have break-glass procedures for emergencies

This design provides a robust, scalable foundation for team and permission management that can grow with the application's needs while maintaining security and usability.