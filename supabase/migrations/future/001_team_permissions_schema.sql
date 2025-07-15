-- Team & Permission Management System Schema
-- This migration creates the core tables for managing teams, permissions, and access control

-- User profiles (extending Supabase auth.users)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Organizations/Teams
CREATE TABLE IF NOT EXISTS organizations (
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
CREATE TABLE IF NOT EXISTS roles (
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
CREATE TABLE IF NOT EXISTS organization_members (
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
CREATE TABLE IF NOT EXISTS agents (
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
CREATE TABLE IF NOT EXISTS agent_permissions (
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
CREATE TABLE IF NOT EXISTS data_sources (
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
CREATE TABLE IF NOT EXISTS data_access_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id),
    user_id UUID REFERENCES auth.users(id),
    access_level TEXT NOT NULL CHECK (access_level IN ('read', 'write', 'admin')),
    filters JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_role_or_user CHECK (
        (role_id IS NOT NULL AND user_id IS NULL) OR 
        (role_id IS NULL AND user_id IS NOT NULL)
    )
);

-- Google Workspace sync data
CREATE TABLE IF NOT EXISTS google_workspace_sync (
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
CREATE TABLE IF NOT EXISTS permission_audit_log (
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

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_org_members_org_id ON organization_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_permissions_agent_id ON agent_permissions(agent_id);
CREATE INDEX IF NOT EXISTS idx_data_access_source_id ON data_access_permissions(data_source_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_org_id ON permission_audit_log(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON permission_audit_log(created_at DESC);

-- Insert default system roles
INSERT INTO roles (name, slug, description, permissions, is_system) VALUES
('Owner', 'owner', 'Full access to all organization resources', 
 '[{"resource": "*", "action": "*"}]'::jsonb, true),
('Administrator', 'admin', 'Can manage users, agents, and data sources',
 '[
   {"resource": "organization", "action": "read"},
   {"resource": "organization", "action": "update"},
   {"resource": "agent", "action": "*"},
   {"resource": "data_source", "action": "*"},
   {"resource": "user", "action": "*"},
   {"resource": "role", "action": "read"}
 ]'::jsonb, true),
('Member', 'member', 'Can use agents and access assigned data',
 '[
   {"resource": "organization", "action": "read"},
   {"resource": "agent", "action": "read"},
   {"resource": "agent", "action": "use"},
   {"resource": "data_source", "action": "read", "conditions": {"assigned": true}}
 ]'::jsonb, true),
('Guest', 'guest', 'Limited read-only access',
 '[
   {"resource": "organization", "action": "read"},
   {"resource": "agent", "action": "read", "conditions": {"public": true}}
 ]'::jsonb, true)
ON CONFLICT (slug) DO NOTHING;

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
      OR r.permissions @> json_build_array(
        json_build_object(
          'resource', p_resource,
          'action', '*'
        )
      )::jsonb
    )
  ) INTO v_has_permission;
  
  RETURN v_has_permission;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON data_sources
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_google_workspace_sync_updated_at BEFORE UPDATE ON google_workspace_sync
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();