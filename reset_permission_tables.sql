-- WARNING: This will DROP and recreate the permission tables
-- Only use this if you're sure you want to reset the permission system

-- First, check if there's any data you want to keep
SELECT COUNT(*) as user_count FROM public.user_teams;
SELECT COUNT(*) as team_count FROM public.teams;

-- If you're sure you want to proceed, uncomment the lines below:

/*
-- Drop existing objects
DROP VIEW IF EXISTS public.user_permissions CASCADE;
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;
DROP TABLE IF EXISTS public.user_teams CASCADE;
DROP TABLE IF EXISTS public.teams CASCADE;

-- Now run the original migration
-- Copy and paste the contents of create_permission_tables.sql here
*/