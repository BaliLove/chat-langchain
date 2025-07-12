-- Sync users from Bubble to Supabase
-- Generated on: 2025-07-12 22:06:43

-- Insert teams

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1720587962667x853438423770595300', 'All', '')
ON CONFLICT (bubble_id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1721050466335x740739333252448300', 'Revenue', '')
ON CONFLICT (bubble_id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1721050512972x798799296083001300', 'Client Experience', '')
ON CONFLICT (bubble_id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1721050762430x540226679433855000', 'Finance', '')
ON CONFLICT (bubble_id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1725421764149x575527053408600060', 'People & Culture', '')
ON CONFLICT (bubble_id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1731539839711x361098058690723840', 'Digital', '')
ON CONFLICT (bubble_id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1731539880998x799950694335643600', 'Special Projects', '')
ON CONFLICT (bubble_id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Insert users

-- Add tom@bali.love as admin
INSERT INTO public.user_teams (
    email, 
    team_name, 
    role,
    allowed_agents,
    allowed_data_sources,
    permissions
)
VALUES (
    'tom@bali.love', 
    'Bali Love', 
    'admin',
    '["chat", "search", "analytics"]'::jsonb,
    '["public", "company_wide", "team_specific", "admin_only"]'::jsonb,
    '{"can_manage_team": true, "can_export_data": true}'::jsonb
)
ON CONFLICT (email) DO UPDATE
SET role = 'admin',
    allowed_agents = EXCLUDED.allowed_agents,
    allowed_data_sources = EXCLUDED.allowed_data_sources,
    permissions = EXCLUDED.permissions;