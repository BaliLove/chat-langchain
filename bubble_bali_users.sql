-- Bubble to Supabase sync
-- Generated: 2025-07-12 22:09:44.658817

-- Insert teams

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1720587962667x853438423770595300', 'All', '')
ON CONFLICT (bubble_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1721050466335x740739333252448300', 'Revenue', '')
ON CONFLICT (bubble_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1721050512972x798799296083001300', 'Client Experience', '')
ON CONFLICT (bubble_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1721050762430x540226679433855000', 'Finance', '')
ON CONFLICT (bubble_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO public.teams (bubble_id, name, description)
VALUES ('1725421764149x575527053408600060', 'People & Culture', '')
ON CONFLICT (bubble_id) DO UPDATE SET name = EXCLUDED.name;

-- Insert users

-- User: Tom Hay (tom@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'tom@bali.love', '1665057490662x869948921559859200', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Talitha Graziano (talitha@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'talitha@bali.love', '1665071758539x863306934722732400', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Michele  Yoga  (michele@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'michele@bali.love', '1665093512423x266110174612502750', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Bagus Gutrana (bagus@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'bagus@bali.love', '1665104206100x361072671784520300', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Dewi Sucandra (dewi@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'dewi@bali.love', '1665105690750x391513219662731140', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Atha Adinatha (atha@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'atha@bali.love', '1665105875884x694309257321365900', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Planning  Bali.Love (planning@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'planning@bali.love', '1669167411712x537744801470644540', 'Bali Love', 'member', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Nessa Silitonga (nessa@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'nessa@bali.love', '1670378094683x820105337172333000', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Lily Go (lily@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'lily@bali.love', '1672269558997x650259603718563100', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Maria Dinatha (maria@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'maria@bali.love', '1673835812446x133699842573991040', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Diah Nurul Hidayati (diah@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'diah@bali.love', '1675046171524x156615452772767900', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Junni Andriani (junni_notworking@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'junni_notworking@bali.love', '1675046175290x884908015347970700', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Ryan Munen (ryan@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'ryan@bali.love', '1677644283974x891177532116251800', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Bram Pardede (bram@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'bram@bali.love', '1677808483762x223753968919161440', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Dewita Putri (dewita@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'dewita@bali.love', '1677808581414x791709482689659400', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Ary Sugiartha (ary@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'ary@bali.love', '1677808631198x823716521989077600', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Lauren Harris (lauren@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'lauren@bali.love', '1677992102827x314289559200954240', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Yunita Ariani (yunita@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'yunita@bali.love', '1678172586584x992419742335801600', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Abdullah Muhammad  (abdul@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'abdul@bali.love', '1679883432312x469717067755337500', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- User: Bali.Love Notifications (notifications@bali.love)
INSERT INTO public.user_teams (
    email, bubble_user_id, team_name, role, synced_from_bubble_at
)
VALUES (
    'notifications@bali.love', '1680218558377x253351199594366700', 'Bali Love', 'admin', NOW()
)
ON CONFLICT (email) DO UPDATE SET
    bubble_user_id = EXCLUDED.bubble_user_id,
    synced_from_bubble_at = NOW();

-- Plus 42 more users...

-- Ensure tom@bali.love is admin
UPDATE public.user_teams 
SET role = 'admin',
    allowed_agents = '["chat", "search", "analytics"]'::jsonb,
    allowed_data_sources = '["public", "company_wide", "team_specific", "admin_only"]'::jsonb,
    permissions = '{"can_manage_team": true, "can_export_data": true}'::jsonb
WHERE email = 'tom@bali.love';