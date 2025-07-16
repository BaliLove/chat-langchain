-- Create prompt caching tables for efficient LangSmith data management

-- Main prompts table
CREATE TABLE prompts (
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
    langsmith_updated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Version history table
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    template TEXT NOT NULL,
    changes TEXT,
    modified_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(prompt_id, version)
);

-- Analytics table for usage tracking
CREATE TABLE prompt_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    team TEXT,
    usage_count INTEGER NOT NULL DEFAULT 0,
    avg_response_time INTEGER, -- in milliseconds
    success_rate DECIMAL(5,2), -- percentage
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(prompt_id, date, team)
);

-- Examples table for recent successful uses
CREATE TABLE prompt_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    team TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Context tags for team-specific filtering
CREATE TABLE prompt_context_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    team TEXT NOT NULL,
    tag TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(prompt_id, team, tag)
);

-- Sync status table to track LangSmith sync
CREATE TABLE prompt_sync_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_sync_status TEXT, -- 'success', 'error', 'in_progress'
    error_message TEXT,
    prompts_synced INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_prompts_team ON prompts(team);
CREATE INDEX idx_prompts_category ON prompts(category);
CREATE INDEX idx_prompts_type ON prompts(type);
CREATE INDEX idx_prompts_updated_at ON prompts(updated_at);

CREATE INDEX idx_prompt_versions_prompt_id ON prompt_versions(prompt_id);
CREATE INDEX idx_prompt_versions_version ON prompt_versions(version);

CREATE INDEX idx_prompt_analytics_prompt_id ON prompt_analytics(prompt_id);
CREATE INDEX idx_prompt_analytics_date ON prompt_analytics(date);
CREATE INDEX idx_prompt_analytics_team ON prompt_analytics(team);

CREATE INDEX idx_prompt_examples_prompt_id ON prompt_examples(prompt_id);
CREATE INDEX idx_prompt_examples_timestamp ON prompt_examples(timestamp);
CREATE INDEX idx_prompt_examples_team ON prompt_examples(team);

CREATE INDEX idx_prompt_context_tags_prompt_id ON prompt_context_tags(prompt_id);
CREATE INDEX idx_prompt_context_tags_team ON prompt_context_tags(team);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_prompts_updated_at
    BEFORE UPDATE ON prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_analytics_updated_at
    BEFORE UPDATE ON prompt_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_sync_status_updated_at
    BEFORE UPDATE ON prompt_sync_status
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) policies
ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_examples ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_context_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_sync_status ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read all prompts
CREATE POLICY "Allow authenticated users to read prompts" ON prompts
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read prompt versions" ON prompt_versions
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read prompt analytics" ON prompt_analytics
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read prompt examples" ON prompt_examples
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read prompt context tags" ON prompt_context_tags
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated users to read sync status" ON prompt_sync_status
    FOR SELECT TO authenticated USING (true);

-- Allow service role to manage all data (for sync operations)
CREATE POLICY "Allow service role to manage prompts" ON prompts
    FOR ALL TO service_role USING (true);

CREATE POLICY "Allow service role to manage prompt versions" ON prompt_versions
    FOR ALL TO service_role USING (true);

CREATE POLICY "Allow service role to manage prompt analytics" ON prompt_analytics
    FOR ALL TO service_role USING (true);

CREATE POLICY "Allow service role to manage prompt examples" ON prompt_examples
    FOR ALL TO service_role USING (true);

CREATE POLICY "Allow service role to manage prompt context tags" ON prompt_context_tags
    FOR ALL TO service_role USING (true);

CREATE POLICY "Allow service role to manage sync status" ON prompt_sync_status
    FOR ALL TO service_role USING (true);