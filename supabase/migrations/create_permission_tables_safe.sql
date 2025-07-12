-- Safe migration script that checks for existing objects before creating them

-- Create teams table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bubble_id TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create user_teams table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.user_teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    bubble_user_id TEXT UNIQUE,
    team_id UUID REFERENCES public.teams(id),
    team_name TEXT,
    role TEXT DEFAULT 'member' CHECK (role IN ('admin', 'manager', 'member')),
    allowed_agents JSONB DEFAULT '["chat", "search"]'::jsonb,
    allowed_data_sources JSONB DEFAULT '["public", "company_wide"]'::jsonb,
    permissions JSONB DEFAULT '{}'::jsonb,
    synced_from_bubble_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create indexes only if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_user_teams_email') THEN
        CREATE INDEX idx_user_teams_email ON public.user_teams(email);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_user_teams_user_id') THEN
        CREATE INDEX idx_user_teams_user_id ON public.user_teams(user_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_user_teams_team_id') THEN
        CREATE INDEX idx_user_teams_team_id ON public.user_teams(team_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_teams_bubble_id') THEN
        CREATE INDEX idx_teams_bubble_id ON public.teams(bubble_id);
    END IF;
END $$;

-- Enable RLS only if not already enabled
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename = 'teams' 
        AND rowsecurity = true
    ) THEN
        ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename = 'user_teams' 
        AND rowsecurity = true
    ) THEN
        ALTER TABLE public.user_teams ENABLE ROW LEVEL SECURITY;
    END IF;
END $$;

-- Drop existing policies if they exist and recreate them
DROP POLICY IF EXISTS "Teams viewable by authenticated users" ON public.teams;
CREATE POLICY "Teams viewable by authenticated users" ON public.teams
    FOR SELECT USING (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Users can view their own team data" ON public.user_teams;
CREATE POLICY "Users can view their own team data" ON public.user_teams
    FOR SELECT USING (auth.uid() = user_id OR email = auth.jwt() ->> 'email');

DROP POLICY IF EXISTS "Service role can manage all user_teams" ON public.user_teams;
CREATE POLICY "Service role can manage all user_teams" ON public.user_teams
    FOR ALL USING (auth.role() = 'service_role');

-- Create or replace function for handling new users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
    -- Check if user_teams entry already exists for this email
    IF EXISTS (SELECT 1 FROM public.user_teams WHERE email = NEW.email) THEN
        -- Update the user_id reference
        UPDATE public.user_teams 
        SET user_id = NEW.id, 
            updated_at = timezone('utc'::text, now())
        WHERE email = NEW.email;
    ELSE
        -- Create a new entry with default permissions
        INSERT INTO public.user_teams (
            user_id, 
            email, 
            team_name,
            role,
            allowed_agents,
            allowed_data_sources
        ) VALUES (
            NEW.id,
            NEW.email,
            'Bali Love',
            'member',
            '["chat", "search"]'::jsonb,
            '["public", "company_wide"]'::jsonb
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop and recreate trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Create or replace view for user permissions
CREATE OR REPLACE VIEW public.user_permissions AS
SELECT 
    ut.user_id,
    ut.email,
    ut.team_id,
    ut.team_name,
    ut.role,
    ut.allowed_agents,
    ut.allowed_data_sources,
    ut.permissions,
    t.name as team_full_name,
    t.description as team_description
FROM public.user_teams ut
LEFT JOIN public.teams t ON ut.team_id = t.id;

-- Grant permissions
GRANT SELECT ON public.user_permissions TO authenticated;
GRANT ALL ON public.teams TO service_role;
GRANT ALL ON public.user_teams TO service_role;

-- Add any missing columns to existing tables
DO $$
BEGIN
    -- Check if columns exist and add them if they don't
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_teams' AND column_name = 'permissions') THEN
        ALTER TABLE public.user_teams ADD COLUMN permissions JSONB DEFAULT '{}'::jsonb;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_teams' AND column_name = 'synced_from_bubble_at') THEN
        ALTER TABLE public.user_teams ADD COLUMN synced_from_bubble_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;