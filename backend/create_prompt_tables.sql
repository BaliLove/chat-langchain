-- Create prompt caching tables for LangSmith data

-- Main prompts table
CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    template TEXT NOT NULL,
    team TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'prompt',
    category TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_modified_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    context_tags JSONB DEFAULT '{}'::jsonb
);

-- Sync status table
CREATE TABLE IF NOT EXISTS prompt_sync_status (
    id SERIAL PRIMARY KEY,
    last_sync_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    sync_status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    prompts_synced INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_prompts_team ON prompts(team);
CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category);
CREATE INDEX IF NOT EXISTS idx_prompts_active ON prompts(is_active);

-- Enable RLS
ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_sync_status ENABLE ROW LEVEL SECURITY;

-- Allow all authenticated users to read prompts
CREATE POLICY "Allow authenticated users to read prompts" ON prompts
    FOR SELECT USING (auth.role() = 'authenticated');

-- Allow service role to manage prompts (for sync)
CREATE POLICY "Allow service role to manage prompts" ON prompts
    FOR ALL USING (auth.role() = 'service_role');

-- Allow all authenticated users to read sync status
CREATE POLICY "Allow authenticated users to read sync status" ON prompt_sync_status
    FOR SELECT USING (auth.role() = 'authenticated');

-- Allow service role to manage sync status
CREATE POLICY "Allow service role to manage sync status" ON prompt_sync_status
    FOR ALL USING (auth.role() = 'service_role');