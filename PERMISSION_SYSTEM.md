# Permission System Documentation

## Overview

The Bali Love Chat application implements a comprehensive permission system that integrates with your existing Bubble.io user and team data. This system controls access to chat agents, data sources, and various features based on user roles and team assignments.

## Architecture

### Database Schema

The permission system uses three main tables in Supabase:

1. **teams** - Stores team information synced from Bubble
   - `id`: UUID (Supabase primary key)
   - `bubble_id`: Original Bubble ID
   - `name`: Team name
   - `description`: Team description

2. **user_teams** - Extended user data with permissions
   - `user_id`: Reference to auth.users
   - `email`: User email (unique)
   - `team_id`: Reference to teams table
   - `role`: User role (admin, manager, member)
   - `allowed_agents`: JSON array of allowed AI agents
   - `allowed_data_sources`: JSON array of accessible data sources
   - `permissions`: Flexible JSON object for custom permissions

3. **user_permissions** (view) - Convenient view joining users and teams

### Permission Levels

#### Roles
- **Admin**: Full access to all features, can manage team
- **Manager**: Enhanced access, can view team threads
- **Member**: Standard access to personal threads

#### Agent Access
Users can be granted access to specific AI agents:
- `chat`: Main conversational agent
- `search`: Search-focused agent
- Additional agents can be configured

#### Data Sources
Control which data sources users can query:
- `public`: Publicly available information
- `company_wide`: Company-wide documentation
- `team_specific`: Team-specific data
- `department_specific`: Department data
- `admin_only`: Administrative data

## Setup Instructions

### 1. Database Setup

Run the migration script to create the necessary tables:

```bash
# Apply the migration to your Supabase instance
psql $DATABASE_URL < supabase/migrations/create_permission_tables.sql
```

### 2. Environment Variables

Ensure these variables are set in your `.env` file:

```env
# Bubble API Configuration
BUBBLE_API_TOKEN=your_bubble_api_token
BUBBLE_APP_URL=https://app.bali.love
BUBBLE_BATCH_SIZE=100

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 3. Initial Data Sync

Run the sync script to import users and teams from Bubble:

```bash
python sync_bubble_permissions.py
```

This script will:
- Fetch all teams from your Bubble app
- Fetch all users with @bali.love email addresses
- Create team records in Supabase
- Create user permission records with appropriate roles

### 4. Scheduled Sync (Optional)

To keep permissions in sync, you can schedule the sync script:

#### Using cron:
```bash
# Run every hour
0 * * * * cd /path/to/project && python sync_bubble_permissions.py
```

#### Using GitHub Actions:
```yaml
name: Sync Bubble Permissions
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run sync
        env:
          BUBBLE_API_TOKEN: ${{ secrets.BUBBLE_API_TOKEN }}
          BUBBLE_APP_URL: ${{ secrets.BUBBLE_APP_URL }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
        run: python sync_bubble_permissions.py
```

## Frontend Integration

### Using Permissions in Components

The `usePermissions` hook provides easy access to user permissions:

```typescript
import { usePermissions } from '@/app/hooks/usePermissions'

function MyComponent() {
  const { permissions, hasAgent, hasDataSource } = usePermissions()
  
  // Check if user can use chat agent
  if (!hasAgent('chat')) {
    return <div>You don't have access to the chat agent</div>
  }
  
  // Check data source access
  if (hasDataSource('admin_only')) {
    // Show admin-only features
  }
  
  // Check specific permissions
  if (permissions?.canExportData) {
    // Show export button
  }
}
```

### Permission Status Display

The `PermissionStatus` component shows users their current permissions:

```typescript
import PermissionStatus from '@/app/components/PermissionStatus'

// Add to your layout or sidebar
<PermissionStatus />
```

## Managing Permissions

### Via Bubble

Update user roles and team assignments in your Bubble app, then run the sync script to propagate changes.

### Via Supabase Dashboard

For immediate updates, you can modify the `user_teams` table directly in Supabase:

```sql
-- Grant admin role to a user
UPDATE user_teams 
SET role = 'admin',
    allowed_data_sources = allowed_data_sources || '["admin_only"]'::jsonb
WHERE email = 'user@bali.love';

-- Add a new agent permission
UPDATE user_teams 
SET allowed_agents = allowed_agents || '["analytics"]'::jsonb
WHERE email = 'user@bali.love';
```

### Custom Permissions

The `permissions` JSONB field allows for flexible custom permissions:

```sql
-- Add custom permission
UPDATE user_teams 
SET permissions = permissions || '{"can_access_beta_features": true}'::jsonb
WHERE email = 'user@bali.love';
```

Access in frontend:
```typescript
const { checkCustomPermission } = usePermissions()

if (checkCustomPermission('can_access_beta_features')) {
  // Show beta features
}
```

## Security Considerations

1. **Row Level Security (RLS)**: Enabled on all permission tables
2. **Service Role Key**: Only use for admin operations and sync scripts
3. **Email Domain Validation**: Only @bali.love emails are allowed by default
4. **Auth Integration**: Permissions are linked to Supabase Auth users

## Troubleshooting

### Users can't access the chat
1. Check if user is in `user_teams` table
2. Verify `allowed_agents` includes "chat"
3. Ensure user email ends with @bali.love

### Sync script errors
1. Verify all environment variables are set
2. Check Bubble API token has correct permissions
3. Ensure Supabase service role key is valid

### Permission updates not reflecting
1. User may need to log out and back in
2. Check browser console for errors
3. Verify sync script ran successfully

## Future Enhancements

1. **Granular Permissions**: Add more specific permissions per data source
2. **Permission Groups**: Create permission templates for common roles
3. **Audit Trail**: Log permission changes and access attempts
4. **Self-Service**: Allow team admins to manage their team's permissions