-- Temporarily disable RLS for initial data load
ALTER TABLE prompts DISABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_sync_status DISABLE ROW LEVEL SECURITY;

-- Or alternatively, create policies that allow anon role to insert during initial setup
-- This is less secure but allows the sync to work with anon key

-- Drop existing policies
DROP POLICY IF EXISTS "Allow authenticated users to read prompts" ON prompts;
DROP POLICY IF EXISTS "Allow service role to manage prompts" ON prompts;
DROP POLICY IF EXISTS "Allow authenticated users to read sync status" ON prompt_sync_status;
DROP POLICY IF EXISTS "Allow service role to manage sync status" ON prompt_sync_status;

-- Create more permissive policies for initial setup
CREATE POLICY "Allow all to read prompts" ON prompts
    FOR SELECT USING (true);

CREATE POLICY "Allow all to insert prompts" ON prompts
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow all to update prompts" ON prompts
    FOR UPDATE USING (true);

CREATE POLICY "Allow all to manage sync status" ON prompt_sync_status
    FOR ALL USING (true);

-- Re-enable RLS
ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_sync_status ENABLE ROW LEVEL SECURITY;