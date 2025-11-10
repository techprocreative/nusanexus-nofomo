-- NusaNexus NoFOMO Indexes and Triggers
-- Migration: 002_indexes_and_triggers
-- Created: 2025-11-10
-- Description: Performance indexes, triggers, and database functions

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription_plan ON users(subscription_plan);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = true;

-- Bots indexes
CREATE INDEX idx_bots_user_id ON bots(user_id);
CREATE INDEX idx_bots_status ON bots(status);
CREATE INDEX idx_bots_exchange ON bots(exchange);
CREATE INDEX idx_bots_trading_pair ON bots(trading_pair);
CREATE INDEX idx_bots_strategy ON bots(strategy);
CREATE INDEX idx_bots_created_at ON bots(created_at);
CREATE INDEX idx_bots_last_trade_at ON bots(last_trade_at) WHERE last_trade_at IS NOT NULL;
CREATE INDEX idx_bots_user_status ON bots(user_id, status);

-- Strategies indexes
CREATE INDEX idx_strategies_user_id ON strategies(user_id);
CREATE INDEX idx_strategies_type ON strategies(strategy_type);
CREATE INDEX idx_strategies_public ON strategies(is_public) WHERE is_public = true;
CREATE INDEX idx_strategies_verified ON strategies(is_verified) WHERE is_verified = true;
CREATE INDEX idx_strategies_category ON strategies(category) WHERE category IS NOT NULL;
CREATE INDEX idx_strategies_risk_level ON strategies(risk_level) WHERE risk_level IS NOT NULL;
CREATE INDEX idx_strategies_created_at ON strategies(created_at);
CREATE INDEX idx_strategies_user_type ON strategies(user_id, strategy_type);

-- Composite index for marketplace strategies
CREATE INDEX idx_strategies_marketplace ON strategies(is_public, strategy_type, is_verified) 
    WHERE is_public = true AND strategy_type = 'marketplace';

-- Trades indexes
CREATE INDEX idx_trades_bot_id ON trades(bot_id);
CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_entry_time ON trades(entry_time);
CREATE INDEX idx_trades_exit_time ON trades(exit_time) WHERE exit_time IS NOT NULL;
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_exchange ON trades(exchange);
CREATE INDEX idx_trades_trading_pair ON trades(trading_pair);
CREATE INDEX idx_trades_side ON trades(side);
CREATE INDEX idx_trades_created_at ON trades(created_at);
CREATE INDEX idx_trades_bot_status ON trades(bot_id, status);
CREATE INDEX idx_trades_user_date ON trades(user_id, entry_time);
CREATE INDEX idx_trades_profit ON trades(profit) WHERE profit != 0;

-- Logs indexes
CREATE INDEX idx_logs_bot_id ON logs(bot_id) WHERE bot_id IS NOT NULL;
CREATE INDEX idx_logs_user_id ON logs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_logs_strategy_id ON logs(strategy_id) WHERE strategy_id IS NOT NULL;
CREATE INDEX idx_logs_level ON logs(log_level);
CREATE INDEX idx_logs_created_at ON logs(created_at);
CREATE INDEX idx_logs_source ON logs(source) WHERE source IS NOT NULL;
CREATE INDEX idx_logs_user_level ON logs(user_id, log_level) WHERE user_id IS NOT NULL;
CREATE INDEX idx_logs_bot_level ON logs(bot_id, log_level) WHERE bot_id IS NOT NULL;

-- AI Analyses indexes
CREATE INDEX idx_ai_analyses_user_id ON ai_analyses(user_id);
CREATE INDEX idx_ai_analyses_bot_id ON ai_analyses(bot_id) WHERE bot_id IS NOT NULL;
CREATE INDEX idx_ai_analyses_strategy_id ON ai_analyses(strategy_id) WHERE strategy_id IS NOT NULL;
CREATE INDEX idx_ai_analyses_type ON ai_analyses(analysis_type);
CREATE INDEX idx_ai_analyses_created_at ON ai_analyses(created_at);
CREATE INDEX idx_ai_analyses_model ON ai_analyses(model_used) WHERE model_used IS NOT NULL;

-- Backtest Results indexes
CREATE INDEX idx_backtest_results_strategy_id ON backtest_results(strategy_id);
CREATE INDEX idx_backtest_results_user_id ON backtest_results(user_id);
CREATE INDEX idx_backtest_results_trading_pair ON backtest_results(trading_pair);
CREATE INDEX idx_backtest_results_timeframe ON backtest_results(timeframe);
CREATE INDEX idx_backtest_results_start_date ON backtest_results(start_date);
CREATE INDEX idx_backtest_results_end_date ON backtest_results(end_date);
CREATE INDEX idx_backtest_results_created_at ON backtest_results(created_at);
CREATE INDEX idx_backtest_results_user_strategy ON backtest_results(user_id, strategy_id);

-- Invoices indexes
CREATE INDEX idx_invoices_user_id ON invoices(user_id);
CREATE INDEX idx_invoices_tripay_id ON invoices(tripay_invoice_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_plan_id ON invoices(plan_id);
CREATE INDEX idx_invoices_created_at ON invoices(created_at);
CREATE INDEX idx_invoices_user_status ON invoices(user_id, status);
CREATE INDEX idx_invoices_expired_at ON invoices(expired_at) WHERE expired_at IS NOT NULL;

-- Subscriptions indexes
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_plan_id ON subscriptions(plan_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_started_at ON subscriptions(started_at);
CREATE INDEX idx_subscriptions_expires_at ON subscriptions(expires_at);
CREATE INDEX idx_subscriptions_user_status ON subscriptions(user_id, status);
CREATE INDEX idx_subscriptions_active ON subscriptions(user_id, status) WHERE status = 'active';

-- Plans indexes
CREATE INDEX idx_plans_active ON plans(is_active) WHERE is_active = true;
CREATE INDEX idx_plans_price ON plans(price_monthly);
CREATE INDEX idx_plans_sort_order ON plans(sort_order);

-- =============================================================================
-- TRIGGERS AND FUNCTIONS
-- =============================================================================

-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to calculate trade holding duration
CREATE OR REPLACE FUNCTION calculate_holding_duration()
RETURNS TRIGGER AS $$
BEGIN
    -- Only calculate if both entry and exit times are available
    IF NEW.exit_time IS NOT NULL AND NEW.entry_time IS NOT NULL THEN
        NEW.holding_duration = NEW.exit_time - NEW.entry_time;
    ELSE
        NEW.holding_duration = NULL;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to update bot statistics
CREATE OR REPLACE FUNCTION update_bot_statistics()
RETURNS TRIGGER AS $$
DECLARE
    bot_uuid UUID;
    total_trades_count INTEGER;
    winning_trades_count INTEGER;
    total_profit DECIMAL(20,8);
    current_profit_percentage DECIMAL(10,4);
BEGIN
    -- Determine which bot_id to use based on the operation
    IF TG_OP = 'INSERT' THEN
        bot_uuid = NEW.bot_id;
    ELSIF TG_OP = 'UPDATE' THEN
        bot_uuid = NEW.bot_id;
    ELSIF TG_OP = 'DELETE' THEN
        bot_uuid = OLD.bot_id;
    END IF;

    -- Update bot statistics only for closed trades
    WITH trade_stats AS (
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE profit > 0) as winning,
            COALESCE(SUM(profit), 0) as total_profit,
            CASE 
                WHEN b.initial_balance > 0 THEN 
                    (COALESCE(SUM(profit), 0) / b.initial_balance) * 100 
                ELSE 0 
            END as profit_pct
        FROM bots b
        LEFT JOIN trades t ON t.bot_id = b.id AND t.status = 'closed'
        WHERE b.id = bot_uuid
        GROUP BY b.id, b.initial_balance
    )
    UPDATE bots 
    SET 
        total_trades = COALESCE(trade_stats.total, 0),
        winning_trades = COALESCE(trade_stats.winning, 0),
        losing_trades = COALESCE(trade_stats.total, 0) - COALESCE(trade_stats.winning, 0),
        profit = COALESCE(trade_stats.total_profit, 0),
        profit_percentage = COALESCE(trade_stats.profit_pct, 0),
        last_trade_at = (
            SELECT MAX(entry_time) 
            FROM trades 
            WHERE bot_id = bot_uuid AND status = 'closed'
        )
    FROM trade_stats
    WHERE bots.id = bot_uuid;

    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

-- Function to validate bot limits based on subscription plan
CREATE OR REPLACE FUNCTION validate_bot_limits()
RETURNS TRIGGER AS $$
DECLARE
    current_bot_count INTEGER;
    plan_limits JSONB;
    max_bots INTEGER;
    plan_name TEXT;
BEGIN
    -- Get user's current bot count and plan limits
    SELECT 
        COUNT(b.id) as bot_count,
        p.features,
        p.max_bots,
        p.name
    INTO current_bot_count, plan_limits, max_bots, plan_name
    FROM users u
    LEFT JOIN subscriptions s ON s.user_id = u.id AND s.status = 'active'
    LEFT JOIN plans p ON p.id = s.plan_id
    LEFT JOIN bots b ON b.user_id = u.id
    WHERE u.id = NEW.user_id
    GROUP BY u.id, p.features, p.max_bots, p.name;

    -- If user has an active subscription, check limits
    IF max_bots IS NOT NULL AND max_bots > 0 THEN
        -- For new bots, check if limit would be exceeded
        IF TG_OP = 'INSERT' THEN
            IF current_bot_count >= max_bots THEN
                RAISE EXCEPTION 'Bot limit reached. Your % plan allows maximum % bots.', 
                    plan_name, max_bots;
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to clean up old logs (for maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS void AS $$
BEGIN
    -- Delete logs older than 90 days for completed bots
    DELETE FROM logs 
    WHERE created_at < NOW() - INTERVAL '90 days'
    AND (
        bot_id IS NULL OR 
        bot_id IN (
            SELECT id FROM bots 
            WHERE status IN ('stopped', 'error', 'paused') 
            AND updated_at < NOW() - INTERVAL '7 days'
        )
    );
    
    -- Delete logs older than 180 days for active users with many logs
    DELETE FROM logs 
    WHERE created_at < NOW() - INTERVAL '180 days'
    AND user_id IN (
        SELECT user_id 
        FROM logs 
        GROUP BY user_id 
        HAVING COUNT(*) > 10000
    );
END;
$$ language 'plpgsql';

-- =============================================================================
-- CREATE TRIGGERS
-- =============================================================================

-- Triggers for updated_at columns
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bots_updated_at
    BEFORE UPDATE ON bots
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at
    BEFORE UPDATE ON strategies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trades_updated_at
    BEFORE UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plans_updated_at
    BEFORE UPDATE ON plans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers for trade calculations
CREATE TRIGGER calculate_trade_holding_duration
    BEFORE INSERT OR UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION calculate_holding_duration();

-- Triggers for bot statistics updates
CREATE TRIGGER update_bot_stats_on_trade_insert
    AFTER INSERT ON trades
    FOR EACH ROW
    EXECUTE FUNCTION update_bot_statistics();

CREATE TRIGGER update_bot_stats_on_trade_update
    AFTER UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION update_bot_statistics();

CREATE TRIGGER update_bot_stats_on_trade_delete
    AFTER DELETE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION update_bot_statistics();

-- Trigger for bot limits validation
CREATE TRIGGER validate_bot_limit_on_insert
    BEFORE INSERT ON bots
    FOR EACH ROW
    EXECUTE FUNCTION validate_bot_limits();

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Bot performance summary view
CREATE OR REPLACE VIEW bot_performance_summary AS
SELECT 
    b.id,
    b.user_id,
    b.name,
    b.exchange,
    b.trading_pair,
    b.timeframe,
    b.strategy,
    b.status,
    b.initial_balance,
    b.current_balance,
    b.total_trades,
    b.winning_trades,
    b.losing_trades,
    b.profit,
    b.profit_percentage,
    b.created_at,
    b.last_trade_at,
    CASE 
        WHEN b.total_trades > 0 THEN 
            ROUND((b.winning_trades::DECIMAL / b.total_trades * 100), 2)
        ELSE 0 
    END as win_rate_percentage,
    u.email as user_email,
    u.full_name as user_name
FROM bots b
JOIN users u ON u.id = b.user_id;

-- Strategy marketplace view
CREATE OR REPLACE VIEW strategy_marketplace AS
SELECT 
    s.id,
    s.name,
    s.description,
    s.strategy_type,
    s.risk_level,
    s.category,
    s.tags,
    s.backtest_results,
    s.created_at,
    u.full_name as author_name,
    -- Calculate average performance from backtest results
    COALESCE(
        AVG(
            (br.total_return_percentage)::DECIMAL
        ), 0
    ) as avg_return_percentage,
    COUNT(br.id) as backtest_count
FROM strategies s
JOIN users u ON u.id = s.user_id
LEFT JOIN backtest_results br ON br.strategy_id = s.id
WHERE s.is_public = true 
    AND s.strategy_type = 'marketplace'
    AND s.is_verified = true
GROUP BY s.id, s.name, s.description, s.strategy_type, s.risk_level, 
         s.category, s.tags, s.backtest_results, s.created_at, u.full_name;

-- Active subscriptions view
CREATE OR REPLACE VIEW active_subscriptions_summary AS
SELECT 
    s.id,
    s.user_id,
    s.plan_id,
    s.status,
    s.started_at,
    s.expires_at,
    s.auto_renew,
    p.name as plan_name,
    p.price_monthly,
    p.max_bots,
    p.max_strategies,
    p.ai_requests_per_month,
    u.email as user_email,
    u.full_name as user_name,
    -- Calculate days remaining
    GREATEST(0, s.expires_at::DATE - CURRENT_DATE) as days_remaining,
    -- Check if within renewal warning period (7 days)
    CASE 
        WHEN s.expires_at <= NOW() + INTERVAL '7 days' THEN true
        ELSE false
    END as near_expiry
FROM subscriptions s
JOIN plans p ON p.id = s.plan_id
JOIN users u ON u.id = s.user_id
WHERE s.status = 'active';

-- =============================================================================
-- ANALYTICS FUNCTIONS
-- =============================================================================

-- Function to get user's trading performance
CREATE OR REPLACE FUNCTION get_user_trading_performance(user_uuid UUID, days_back INTEGER DEFAULT 30)
RETURNS TABLE (
    total_trades BIGINT,
    winning_trades BIGINT,
    losing_trades BIGINT,
    total_profit NUMERIC,
    total_fees NUMERIC,
    win_rate NUMERIC,
    avg_profit_per_trade NUMERIC,
    best_trade NUMERIC,
    worst_trade NUMERIC,
    total_return_percentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(t.id) as total_trades,
        COUNT(t.id) FILTER (WHERE t.profit > 0) as winning_trades,
        COUNT(t.id) FILTER (WHERE t.profit < 0) as losing_trades,
        COALESCE(SUM(t.profit), 0) as total_profit,
        COALESCE(SUM(t.fee), 0) as total_fees,
        CASE 
            WHEN COUNT(t.id) > 0 THEN 
                ROUND((COUNT(t.id) FILTER (WHERE t.profit > 0)::NUMERIC / COUNT(t.id) * 100), 2)
            ELSE 0 
        END as win_rate,
        CASE 
            WHEN COUNT(t.id) > 0 THEN 
                ROUND(COALESCE(SUM(t.profit), 0) / COUNT(t.id), 8)
            ELSE 0 
        END as avg_profit_per_trade,
        COALESCE(MAX(t.profit), 0) as best_trade,
        COALESCE(MIN(t.profit), 0) as worst_trade,
        -- Calculate total return percentage based on initial balance
        CASE 
            WHEN u.exchange_credentials ? 'initial_balance' THEN
                ROUND((COALESCE(SUM(t.profit), 0) / 
                      (u.exchange_credentials->>'initial_balance')::NUMERIC * 100), 4)
            ELSE 0 
        END as total_return_percentage
    FROM users u
    LEFT JOIN trades t ON t.user_id = u.id 
        AND t.entry_time >= NOW() - INTERVAL '1 day' * days_back
        AND t.status = 'closed'
    WHERE u.id = user_uuid
    GROUP BY u.id, u.exchange_credentials;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;