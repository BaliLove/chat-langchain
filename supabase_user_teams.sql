-- Create user_teams table to store user and team information from Bubble
CREATE TABLE IF NOT EXISTS public.user_teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL UNIQUE,
  team_id TEXT NOT NULL,
  team_name TEXT,
  role TEXT DEFAULT 'member',
  -- Permissions
  allowed_agents TEXT[] DEFAULT ARRAY[]::TEXT[], -- List of agent IDs user can access
  allowed_data_sources TEXT[] DEFAULT ARRAY[]::TEXT[], -- List of data sources user can access
  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  synced_from_bubble_at TIMESTAMPTZ
);

-- Create indexes for performance
CREATE INDEX idx_user_teams_email ON public.user_teams(email);
CREATE INDEX idx_user_teams_team_id ON public.user_teams(team_id);
CREATE INDEX idx_user_teams_user_id ON public.user_teams(user_id);

-- Enable Row Level Security
ALTER TABLE public.user_teams ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read their own team data
CREATE POLICY "Users can read own team data" ON public.user_teams
  FOR SELECT USING (auth.uid() = user_id);

-- Policy: Service role can manage all data (for sync from Bubble)
CREATE POLICY "Service role can manage all data" ON public.user_teams
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update timestamp
CREATE TRIGGER update_user_teams_updated_at
  BEFORE UPDATE ON public.user_teams
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();