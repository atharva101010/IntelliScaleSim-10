-- Migration script to add Load Testing tables
-- Run this with psql or pgAdmin

-- Create load_tests table
CREATE TABLE IF NOT EXISTS load_tests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    container_id INTEGER NOT NULL REFERENCES containers(id) ON DELETE CASCADE,
    
    -- Test configuration
    target_url VARCHAR NOT NULL,
    total_requests INTEGER NOT NULL CHECK (total_requests BETWEEN 1 AND 1000),
    concurrency INTEGER NOT NULL CHECK (concurrency BETWEEN 1 AND 50),
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds BETWEEN 10 AND 60),
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    
    -- Results
    requests_sent INTEGER DEFAULT 0,
    requests_completed INTEGER DEFAULT 0,
    requests_failed INTEGER DEFAULT 0,
    
    -- Response time statistics (milliseconds)
    avg_response_time_ms FLOAT,
    min_response_time_ms FLOAT,
    max_response_time_ms FLOAT,
    
    -- Resource usage peaks
    peak_cpu_percent FLOAT,
    peak_memory_mb FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create indexes for load_tests
CREATE INDEX IF NOT EXISTS idx_load_tests_user_id ON load_tests(user_id);
CREATE INDEX IF NOT EXISTS idx_load_tests_container_id ON load_tests(container_id);
CREATE INDEX IF NOT EXISTS idx_load_tests_status ON load_tests(status);

-- Create load_test_metrics table
CREATE TABLE IF NOT EXISTS load_test_metrics (
    id SERIAL PRIMARY KEY,
    load_test_id INTEGER NOT NULL REFERENCES load_tests(id) ON DELETE CASCADE,
    
    -- Timestamp of this metric snapshot
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Container resource metrics
    cpu_percent FLOAT NOT NULL,
    memory_mb FLOAT NOT NULL,
    
    -- Request progress at this timestamp
    requests_completed INTEGER DEFAULT 0,
    requests_failed INTEGER DEFAULT 0,
    active_requests INTEGER DEFAULT 0
);

-- Create indexes for load_test_metrics
CREATE INDEX IF NOT EXISTS idx_load_test_metrics_load_test_id ON load_test_metrics(load_test_id);
CREATE INDEX IF NOT EXISTS idx_load_test_metrics_timestamp ON load_test_metrics(timestamp);

-- Verify tables were created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('load_tests', 'load_test_metrics');
