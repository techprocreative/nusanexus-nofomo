-- NusaNexus NoFOMO - Supabase Production Configuration
-- Database setup and optimization for production

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create optimized indexes for better performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users (created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_status ON users (status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bots_user_id ON trading_bots (user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bots_status ON trading_bots (status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bots_created_at ON trading_bots (created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bots_pair ON trading_bots (trading_pair);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trades_bot_id ON trades (bot_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trades_timestamp ON trades (timestamp);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trades_type ON trades (trade_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trades_pair ON trades (pair);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategies_user_id ON strategies (user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategies_name ON strategies (name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategies_type ON strategies (strategy_type);

-- Full-text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategies_search ON strategies USING gin (
    to_tsvector('english', name || ' ' || description)
);

-- Optimize table statistics
ANALYZE;

-- Set up connection pooling parameters
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.max = 10000;
ALTER SYSTEM SET pg_stat_statements.track = all;

-- Memory and performance settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Checkpoint and WAL settings
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET max_wal_size = '1GB';
ALTER SYSTEM SET min_wal_size = '80MB';

-- Query planner settings
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET constraint_exclusion = 'partition';

-- Autovacuum settings for production
ALTER SYSTEM SET autovacuum = on;
ALTER SYSTEM SET autovacuum_max_workers = 3;
ALTER SYSTEM SET autovacuum_naptime = '1min';

-- Log settings
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries taking > 1s
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;
ALTER SYSTEM SET log_temp_files = 0;

-- Reload configuration
SELECT pg_reload_conf();

-- Create application-specific views for better performance
CREATE OR REPLACE VIEW bot_performance_summary AS
SELECT 
    b.id,
    b.user_id,
    b.name,
    b.trading_pair,
    b.status,
    COUNT(t.id) as total_trades,
    COALESCE(SUM(t.profit_loss), 0) as total_profit_loss,
    COALESCE(AVG(t.profit_loss), 0) as avg_profit_loss,
    MAX(t.timestamp) as last_trade_time,
    CASE 
        WHEN COUNT(t.id) > 0 THEN 
            (COUNT(CASE WHEN t.profit_loss > 0 THEN 1 END) * 100.0 / COUNT(t.id))
        ELSE 0 
    END as win_rate
FROM trading_bots b
LEFT JOIN trades t ON b.id = t.bot_id
GROUP BY b.id, b.user_id, b.name, b.trading_pair, b.status;

-- Create function to get user trading statistics
CREATE OR REPLACE FUNCTION get_user_trading_stats(user_uuid UUID)
RETURNS TABLE(
    total_bots BIGINT,
    active_bots BIGINT,
    total_trades BIGINT,
    total_profit_loss NUMERIC,
    win_rate NUMERIC,
    best_performing_pair TEXT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM trading_bots WHERE user_id = user_uuid) as total_bots,
        (SELECT COUNT(*) FROM trading_bots WHERE user_id = user_uuid AND status = 'running') as active_bots,
        (SELECT COUNT(*) FROM trades t JOIN trading_bots b ON t.bot_id = b.id WHERE b.user_id = user_uuid) as total_trades,
        (SELECT COALESCE(SUM(t.profit_loss), 0) FROM trades t JOIN trading_bots b ON t.bot_id = b.id WHERE b.user_id = user_uuid) as total_profit_loss,
        (SELECT 
            CASE WHEN COUNT(t.id) > 0 THEN 
                (COUNT(CASE WHEN t.profit_loss > 0 THEN 1 END) * 100.0 / COUNT(t.id))
            ELSE 0 
            END 
        FROM trades t JOIN trading_bots b ON t.bot_id = b.id WHERE b.user_id = user_uuid
        ) as win_rate,
        (SELECT b.trading_pair 
        FROM trades t 
        JOIN trading_bots b ON t.bot_id = b.id 
        WHERE b.user_id = user_uuid 
        GROUP BY b.trading_pair 
        ORDER BY SUM(t.profit_loss) DESC 
        LIMIT 1) as best_performing_pair;
END;
$$;

-- Create RLS (Row Level Security) policies
-- Users can only see their own data
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE trading_bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE backtest_results ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view own data" ON users
    FOR ALL USING (auth.uid() = id);

CREATE POLICY "Users can view own bots" ON trading_bots
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view trades of own bots" ON trades
    FOR ALL USING (EXISTS (
        SELECT 1 FROM trading_bots b 
        WHERE b.id = bot_id AND b.user_id = auth.uid()
    ));

CREATE POLICY "Users can view own strategies" ON strategies
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own backtest results" ON backtest_results
    FOR ALL USING (EXISTS (
        SELECT 1 FROM strategies s 
        WHERE s.id = strategy_id AND s.user_id = auth.uid()
    ));

-- Create database triggers for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        table_name,
        operation,
        old_data,
        new_data,
        user_id,
        timestamp
    ) VALUES (
        TG_TABLE_NAME,
        TG_OP,
        to_jsonb(OLD),
        to_jsonb(NEW),
        auth.uid(),
        NOW()
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to sensitive tables
CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_trading_bots AFTER INSERT OR UPDATE OR DELETE ON trading_bots
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_trades AFTER INSERT OR UPDATE OR DELETE ON trades
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Performance monitoring view
CREATE OR REPLACE VIEW performance_stats AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
    most_common_vals,
    histogram_bounds
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;