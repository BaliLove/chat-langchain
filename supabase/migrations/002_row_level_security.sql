-- Row Level Security Policies for Team & Permission Management

-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_access_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_workspace_sync ENABLE ROW LEVEL SECURITY;
ALTER TABLE permission_audit_log ENABLE ROW LEVEL SECURITY;

-- User Profiles Policies
CREATE POLICY "Users can view their own profile" ON user_profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON user_profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view profiles in their organizations" ON user_profiles
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM organization_members om1
      WHERE om1.user_id = auth.uid()
      AND om1.status = 'active'
      AND EXISTS (
        SELECT 1 FROM organization_members om2
        WHERE om2.user_id = user_profiles.id
        AND om2.organization_id = om1.organization_id
        AND om2.status = 'active'
      )
    )
  );

-- Organizations Policies
CREATE POLICY "Users can view their organizations" ON organizations
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM organization_members
      WHERE organization_members.user_id = auth.uid()
      AND organization_members.organization_id = organizations.id
      AND organization_members.status = 'active'
    )
  );

CREATE POLICY "Owners and admins can update organizations" ON organizations
  FOR UPDATE USING (
    check_permission(auth.uid(), id, 'organization', 'update')
  );

CREATE POLICY "Users can create organizations" ON organizations
  FOR INSERT WITH CHECK (
    auth.uid() = created_by
  );

-- Organization Members Policies
CREATE POLICY "Users can view members in their organizations" ON organization_members
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM organization_members om
      WHERE om.user_id = auth.uid()
      AND om.organization_id = organization_members.organization_id
      AND om.status = 'active'
    )
  );

CREATE POLICY "Admins can manage organization members" ON organization_members
  FOR ALL USING (
    check_permission(auth.uid(), organization_id, 'user', 'manage')
  );

-- Roles Policies
CREATE POLICY "Everyone can view system roles" ON roles
  FOR SELECT USING (is_system = true);

CREATE POLICY "Users can view custom roles in their organizations" ON roles
  FOR SELECT USING (
    is_system = false AND
    EXISTS (
      SELECT 1 FROM organization_members om
      WHERE om.user_id = auth.uid()
      AND om.status = 'active'
      AND check_permission(auth.uid(), om.organization_id, 'role', 'read')
    )
  );

-- Agents Policies
CREATE POLICY "Users can view agents they have access to" ON agents
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM organization_members om
      WHERE om.user_id = auth.uid()
      AND om.organization_id = agents.organization_id
      AND om.status = 'active'
      AND (
        check_permission(auth.uid(), agents.organization_id, 'agent', 'read')
        OR EXISTS (
          SELECT 1 FROM agent_permissions ap
          WHERE ap.agent_id = agents.id
          AND (
            (ap.user_id = auth.uid())
            OR (ap.role_id IN (
              SELECT role_id FROM organization_members
              WHERE user_id = auth.uid()
              AND organization_id = agents.organization_id
            ))
          )
        )
      )
    )
  );

CREATE POLICY "Admins can manage agents" ON agents
  FOR ALL USING (
    check_permission(auth.uid(), organization_id, 'agent', 'manage')
  );

-- Agent Permissions Policies
CREATE POLICY "Users can view agent permissions" ON agent_permissions
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM agents a
      JOIN organization_members om ON om.organization_id = a.organization_id
      WHERE a.id = agent_permissions.agent_id
      AND om.user_id = auth.uid()
      AND om.status = 'active'
      AND check_permission(auth.uid(), a.organization_id, 'agent', 'read')
    )
  );

CREATE POLICY "Admins can manage agent permissions" ON agent_permissions
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM agents a
      WHERE a.id = agent_permissions.agent_id
      AND check_permission(auth.uid(), a.organization_id, 'agent', 'manage')
    )
  );

-- Data Sources Policies
CREATE POLICY "Users can view data sources they have access to" ON data_sources
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM organization_members om
      WHERE om.user_id = auth.uid()
      AND om.organization_id = data_sources.organization_id
      AND om.status = 'active'
      AND (
        check_permission(auth.uid(), data_sources.organization_id, 'data_source', 'read')
        OR EXISTS (
          SELECT 1 FROM data_access_permissions dap
          WHERE dap.data_source_id = data_sources.id
          AND (
            (dap.user_id = auth.uid())
            OR (dap.role_id IN (
              SELECT role_id FROM organization_members
              WHERE user_id = auth.uid()
              AND organization_id = data_sources.organization_id
            ))
          )
        )
      )
    )
  );

CREATE POLICY "Admins can manage data sources" ON data_sources
  FOR ALL USING (
    check_permission(auth.uid(), organization_id, 'data_source', 'manage')
  );

-- Data Access Permissions Policies
CREATE POLICY "Users can view data access permissions" ON data_access_permissions
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM data_sources ds
      JOIN organization_members om ON om.organization_id = ds.organization_id
      WHERE ds.id = data_access_permissions.data_source_id
      AND om.user_id = auth.uid()
      AND om.status = 'active'
      AND check_permission(auth.uid(), ds.organization_id, 'data_source', 'read')
    )
  );

CREATE POLICY "Admins can manage data access permissions" ON data_access_permissions
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM data_sources ds
      WHERE ds.id = data_access_permissions.data_source_id
      AND check_permission(auth.uid(), ds.organization_id, 'data_source', 'manage')
    )
  );

-- Google Workspace Sync Policies
CREATE POLICY "Admins can view and manage Google Workspace sync" ON google_workspace_sync
  FOR ALL USING (
    check_permission(auth.uid(), organization_id, 'organization', 'update')
  );

-- Permission Audit Log Policies
CREATE POLICY "Users can view audit logs for their organizations" ON permission_audit_log
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM organization_members om
      WHERE om.user_id = auth.uid()
      AND om.organization_id = permission_audit_log.organization_id
      AND om.status = 'active'
      AND check_permission(auth.uid(), permission_audit_log.organization_id, 'organization', 'read')
    )
  );

-- Function to automatically create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_profiles (id, email, full_name, metadata)
  VALUES (
    new.id,
    new.email,
    new.raw_user_meta_data->>'full_name',
    COALESCE(new.raw_user_meta_data, '{}'::jsonb)
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user profile creation
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to log permission changes
CREATE OR REPLACE FUNCTION log_permission_change()
RETURNS TRIGGER AS $$
DECLARE
  v_organization_id UUID;
  v_resource_type TEXT;
  v_resource_id UUID;
BEGIN
  -- Determine organization_id and resource info based on table
  CASE TG_TABLE_NAME
    WHEN 'organization_members' THEN
      v_organization_id := COALESCE(NEW.organization_id, OLD.organization_id);
      v_resource_type := 'user_role';
      v_resource_id := COALESCE(NEW.id, OLD.id);
    WHEN 'agent_permissions' THEN
      SELECT organization_id INTO v_organization_id
      FROM agents WHERE id = COALESCE(NEW.agent_id, OLD.agent_id);
      v_resource_type := 'agent_permission';
      v_resource_id := COALESCE(NEW.id, OLD.id);
    WHEN 'data_access_permissions' THEN
      SELECT organization_id INTO v_organization_id
      FROM data_sources WHERE id = COALESCE(NEW.data_source_id, OLD.data_source_id);
      v_resource_type := 'data_permission';
      v_resource_id := COALESCE(NEW.id, OLD.id);
    ELSE
      RETURN NEW;
  END CASE;

  -- Log the change
  INSERT INTO permission_audit_log (
    organization_id,
    user_id,
    action,
    resource_type,
    resource_id,
    old_value,
    new_value
  ) VALUES (
    v_organization_id,
    auth.uid(),
    TG_OP,
    v_resource_type,
    v_resource_id,
    CASE WHEN TG_OP != 'INSERT' THEN to_jsonb(OLD) ELSE NULL END,
    CASE WHEN TG_OP != 'DELETE' THEN to_jsonb(NEW) ELSE NULL END
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Triggers for permission change logging
CREATE TRIGGER log_organization_member_changes
  AFTER INSERT OR UPDATE OR DELETE ON organization_members
  FOR EACH ROW EXECUTE FUNCTION log_permission_change();

CREATE TRIGGER log_agent_permission_changes
  AFTER INSERT OR UPDATE OR DELETE ON agent_permissions
  FOR EACH ROW EXECUTE FUNCTION log_permission_change();

CREATE TRIGGER log_data_permission_changes
  AFTER INSERT OR UPDATE OR DELETE ON data_access_permissions
  FOR EACH ROW EXECUTE FUNCTION log_permission_change();