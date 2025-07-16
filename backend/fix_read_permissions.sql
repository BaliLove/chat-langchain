-- Fix RLS policies to allow anonymous reads of prompts

-- Drop existing read policy
DROP POLICY IF EXISTS "Allow authenticated users to read prompts" ON prompts;

-- Create new policy that allows all reads (including anonymous)
CREATE POLICY "Allow all to read prompts" ON prompts
    FOR SELECT USING (true);

-- Also fix sync status reads
DROP POLICY IF EXISTS "Allow authenticated users to read sync status" ON prompt_sync_status;

CREATE POLICY "Allow all to read sync status" ON prompt_sync_status
    FOR SELECT USING (true);