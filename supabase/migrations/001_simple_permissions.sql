-- Create teams table
CREATE TABLE IF NOT EXISTS public.teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bubble_id TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create user_teams table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.user_teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    bubble_user_id TEXT UNIQUE,
    team_id UUID REFERENCES public.teams(id),
    team_name TEXT, -- denormalized for quick access
    role TEXT DEFAULT 'member' CHECK (role IN ('admin', 'manager', 'member')),
    allowed_agents JSONB DEFAULT '["chat", "search"]'::jsonb,
    allowed_data_sources JSONB DEFAULT '["public", "company_wide"]'::jsonb,
    permissions JSONB DEFAULT '{}'::jsonb, -- flexible permissions object
    synced_from_bubble_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create indexes for better performance
CREATE INDEX idx_user_teams_email ON public.user_teams(email);
CREATE INDEX idx_user_teams_user_id ON public.user_teams(user_id);
CREATE INDEX idx_user_teams_team_id ON public.user_teams(team_id);
CREATE INDEX idx_teams_bubble_id ON public.teams(bubble_id);

-- Enable Row Level Security (RLS)
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_teams ENABLE ROW LEVEL SECURITY;

-- Create policies for teams table
CREATE POLICY "Teams viewable by authenticated users" ON public.teams
    FOR SELECT USING (auth.role() = 'authenticated');

-- Create policies for user_teams table
CREATE POLICY "Users can view their own team data" ON public.user_teams
    FOR SELECT USING (auth.uid() = user_id OR email = auth.jwt() ->> 'email');

CREATE POLICY "Service role can manage all user_teams" ON public.user_teams
    FOR ALL USING (auth.role() = 'service_role');

-- Create function to automatically link auth.users to user_teams
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
            'Bali Love', -- default team
            'member',
            '["chat", "search"]'::jsonb,
            '["public", "company_wide"]'::jsonb
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new user signups
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Create view for easy access to user permissions
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