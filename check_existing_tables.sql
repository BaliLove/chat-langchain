-- Check what permission tables already exist

-- Check tables
SELECT 
    table_name,
    CASE 
        WHEN rowsecurity THEN 'RLS Enabled'
        ELSE 'RLS Disabled'
    END as rls_status
FROM information_schema.tables t
LEFT JOIN pg_tables pt ON t.table_name = pt.tablename AND t.table_schema = pt.schemaname
WHERE table_schema = 'public' 
AND table_name IN ('teams', 'user_teams', 'user_permissions');

-- Check columns in user_teams table
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'user_teams'
ORDER BY ordinal_position;

-- Check existing indexes
SELECT 
    indexname,
    tablename
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('teams', 'user_teams')
ORDER BY tablename, indexname;

-- Check existing policies
SELECT 
    schemaname,
    tablename,
    policyname,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('teams', 'user_teams')
ORDER BY tablename, policyname;

-- Count existing data
SELECT 
    'teams' as table_name,
    COUNT(*) as row_count
FROM public.teams
UNION ALL
SELECT 
    'user_teams' as table_name,
    COUNT(*) as row_count
FROM public.user_teams;