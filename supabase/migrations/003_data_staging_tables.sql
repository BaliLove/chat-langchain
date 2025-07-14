-- Migration: Create data staging tables for ingestion pipeline

-- Raw data staging table
CREATE TABLE IF NOT EXISTS raw_data_staging (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source_id VARCHAR(255) UNIQUE NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'api', 'manual', 'csv', 'bubble', etc.
    data_type VARCHAR(50) NOT NULL, -- 'venue', 'event', 'product', 'training', etc.
    raw_data JSONB NOT NULL,
    processed_data JSONB,
    content_hash VARCHAR(64),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processed', 'failed', 'archived'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Vectorization tracking
CREATE TABLE IF NOT EXISTS vector_sync_status (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    staging_id UUID REFERENCES raw_data_staging(id) ON DELETE CASCADE,
    vector_store_id VARCHAR(255),
    sync_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'success', 'failed'
    sync_error TEXT,
    synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API fetch history (track what we've fetched)
CREATE TABLE IF NOT EXISTS api_fetch_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    api_endpoint VARCHAR(255) NOT NULL,
    fetch_params JSONB,
    records_fetched INTEGER DEFAULT 0,
    last_fetch_at TIMESTAMP WITH TIME ZONE,
    next_fetch_after TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_staging_source_id ON raw_data_staging(source_id);
CREATE INDEX idx_staging_status ON raw_data_staging(status);
CREATE INDEX idx_staging_data_type ON raw_data_staging(data_type);
CREATE INDEX idx_staging_updated ON raw_data_staging(updated_at);
CREATE INDEX idx_vector_sync_status ON vector_sync_status(sync_status);
CREATE INDEX idx_api_fetch_endpoint ON api_fetch_history(api_endpoint);

-- Enable Row Level Security
ALTER TABLE raw_data_staging ENABLE ROW LEVEL SECURITY;
ALTER TABLE vector_sync_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_fetch_history ENABLE ROW LEVEL SECURITY;

-- Policies for service role (full access)
CREATE POLICY "Service role has full access to staging" ON raw_data_staging
    FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Service role has full access to sync status" ON vector_sync_status
    FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Service role has full access to fetch history" ON api_fetch_history
    FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_raw_data_staging_updated_at BEFORE UPDATE
    ON raw_data_staging FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for monitoring ingestion status
CREATE OR REPLACE VIEW ingestion_status AS
SELECT 
    rds.data_type,
    rds.status,
    COUNT(*) as record_count,
    MAX(rds.updated_at) as last_updated,
    COUNT(CASE WHEN vss.sync_status = 'success' THEN 1 END) as synced_count,
    COUNT(CASE WHEN vss.sync_status = 'failed' THEN 1 END) as sync_failed_count
FROM raw_data_staging rds
LEFT JOIN vector_sync_status vss ON rds.id = vss.staging_id
GROUP BY rds.data_type, rds.status;

-- Grant permissions
GRANT ALL ON raw_data_staging TO service_role;
GRANT ALL ON vector_sync_status TO service_role;
GRANT ALL ON api_fetch_history TO service_role;
GRANT SELECT ON ingestion_status TO authenticated;