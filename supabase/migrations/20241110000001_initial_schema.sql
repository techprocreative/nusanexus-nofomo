-- NusaNexus NoFOMO - Complete Database Schema
-- MVP Database Setup for Supabase

-- Enable UUID extension (using gen_random_uuid() which is built-in to PostgreSQL 13+)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USERS TABLE (Extended from Supabase Auth)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    phone TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    plan_id UUID,
    api_keys JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- BOTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.bots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    exchange TEXT NOT NULL CHECK (exchange IN ('binance', 'bybit')),
    trading_pair TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    strategy TEXT NOT NULL,
    status TEXT DEFAULT 'stopped' CHECK (status IN ('running', 'stopped', 'paused', 'error')),
    initial_balance NUMERIC(20, 8) DEFAULT 0,
    current_balance NUMERIC(20, 8) DEFAULT 0,
    max_open_trades INTEGER DEFAULT 1,
    stake_amount NUMERIC(20, 8) DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    profit NUMERIC(20, 8) DEFAULT 0,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- STRATEGIES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    strategy_type TEXT DEFAULT 'custom' CHECK (strategy_type IN ('custom', 'ai_generated', 'marketplace', 'template')),
    code TEXT,
    parameters JSONB DEFAULT '{}',
    is_public BOOLEAN DEFAULT FALSE,
    tags TEXT[] DEFAULT '{}',
    performance_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TRADES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    bot_id UUID NOT NULL REFERENCES public.bots(id) ON DELETE CASCADE,
    trading_pair TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    trade_type TEXT DEFAULT 'market' CHECK (trade_type IN ('market', 'limit', 'stop_loss', 'take_profit')),
    amount NUMERIC(20, 8) NOT NULL,
    price NUMERIC(20, 8) NOT NULL,
    profit NUMERIC(20, 8) DEFAULT 0,
    fee NUMERIC(20, 8) DEFAULT 0,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled')),
    open_timestamp TIMESTAMP WITH TIME ZONE,
    close_timestamp TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- BACKTEST RESULTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.backtest_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    strategy_id UUID NOT NULL REFERENCES public.strategies(id) ON DELETE CASCADE,
    trading_pair TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    initial_balance NUMERIC(20, 8),
    final_balance NUMERIC(20, 8),
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate NUMERIC(5, 2) DEFAULT 0,
    total_returns NUMERIC(20, 8) DEFAULT 0,
    total_returns_percentage NUMERIC(10, 2) DEFAULT 0,
    sharpe_ratio NUMERIC(10, 4) DEFAULT 0,
    max_drawdown NUMERIC(10, 2) DEFAULT 0,
    profit_factor NUMERIC(10, 4) DEFAULT 0,
    avg_trade_duration TEXT,
    results_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- AI ANALYSES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.ai_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    analysis_type TEXT NOT NULL CHECK (analysis_type IN ('strategy_generation', 'market_analysis', 'optimization', 'signal', 'chat')),
    entity_id UUID,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    cost NUMERIC(10, 6) DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    bot_id UUID REFERENCES public.bots(id) ON DELETE CASCADE,
    level TEXT DEFAULT 'info' CHECK (level IN ('debug', 'info', 'warning', 'error', 'critical')),
    message TEXT NOT NULL,
    source TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- PLANS TABLE (SaaS Billing)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    billing_cycle TEXT DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly', 'yearly', 'lifetime')),
    features JSONB DEFAULT '{}',
    limits JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SUBSCRIPTIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES public.plans(id),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'trial')),
    start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_date TIMESTAMP WITH TIME ZONE,
    auto_renew BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INVOICES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES public.subscriptions(id),
    amount NUMERIC(10, 2) NOT NULL,
    currency TEXT DEFAULT 'IDR',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'failed', 'cancelled')),
    payment_method TEXT,
    payment_provider TEXT DEFAULT 'tripay',
    external_id TEXT,
    metadata JSONB DEFAULT '{}',
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- AUDIT LOG TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    old_data JSONB,
    new_data JSONB,
    user_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON public.users(status);

-- Bots indexes
CREATE INDEX IF NOT EXISTS idx_bots_user_id ON public.bots(user_id);
CREATE INDEX IF NOT EXISTS idx_bots_status ON public.bots(status);
CREATE INDEX IF NOT EXISTS idx_bots_exchange ON public.bots(exchange);
CREATE INDEX IF NOT EXISTS idx_bots_trading_pair ON public.bots(trading_pair);

-- Strategies indexes
CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON public.strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_strategies_type ON public.strategies(strategy_type);
CREATE INDEX IF NOT EXISTS idx_strategies_public ON public.strategies(is_public);

-- Trades indexes
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON public.trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_bot_id ON public.trades(bot_id);
CREATE INDEX IF NOT EXISTS idx_trades_status ON public.trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON public.trades(created_at);

-- Backtest results indexes
CREATE INDEX IF NOT EXISTS idx_backtest_user_id ON public.backtest_results(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_strategy_id ON public.backtest_results(strategy_id);

-- AI analyses indexes
CREATE INDEX IF NOT EXISTS idx_ai_analyses_user_id ON public.ai_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_analyses_type ON public.ai_analyses(analysis_type);

-- Logs indexes
CREATE INDEX IF NOT EXISTS idx_logs_user_id ON public.logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_bot_id ON public.logs(bot_id);
CREATE INDEX IF NOT EXISTS idx_logs_level ON public.logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON public.logs(created_at);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.backtest_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invoices ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Users can view own data" ON public.users
    FOR ALL USING (auth.uid() = id);

-- Bots policies
CREATE POLICY "Users can view own bots" ON public.bots
    FOR ALL USING (auth.uid() = user_id);

-- Strategies policies
CREATE POLICY "Users can view own strategies" ON public.strategies
    FOR SELECT USING (auth.uid() = user_id OR is_public = TRUE);

CREATE POLICY "Users can modify own strategies" ON public.strategies
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own strategies" ON public.strategies
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own strategies" ON public.strategies
    FOR DELETE USING (auth.uid() = user_id);

-- Trades policies
CREATE POLICY "Users can view own trades" ON public.trades
    FOR ALL USING (auth.uid() = user_id);

-- Backtest results policies
CREATE POLICY "Users can view own backtest results" ON public.backtest_results
    FOR ALL USING (auth.uid() = user_id);

-- AI analyses policies
CREATE POLICY "Users can view own AI analyses" ON public.ai_analyses
    FOR ALL USING (auth.uid() = user_id);

-- Logs policies
CREATE POLICY "Users can view own logs" ON public.logs
    FOR SELECT USING (auth.uid() = user_id);

-- Subscriptions policies
CREATE POLICY "Users can view own subscriptions" ON public.subscriptions
    FOR ALL USING (auth.uid() = user_id);

-- Invoices policies
CREATE POLICY "Users can view own invoices" ON public.invoices
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- TRIGGER FUNCTIONS
-- ============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bots_updated_at BEFORE UPDATE ON public.bots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON public.strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plans_updated_at BEFORE UPDATE ON public.plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON public.subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DATA FOR PLANS
-- ============================================================================

INSERT INTO public.plans (name, description, price, billing_cycle, features, limits) 
VALUES 
    (
        'Free',
        'Start trading with basic features',
        0,
        'monthly',
        '{"bots": 1, "strategies": 3, "ai_credits": 10, "support": "community"}',
        '{"max_bots": 1, "max_strategies": 3, "max_trades_per_day": 50, "ai_generations_per_month": 10}'
    ),
    (
        'Pro',
        'Advanced trading with AI features',
        299000,
        'monthly',
        '{"bots": 5, "strategies": "unlimited", "ai_credits": 100, "support": "email", "backtest": true}',
        '{"max_bots": 5, "max_strategies": 999, "max_trades_per_day": 500, "ai_generations_per_month": 100}'
    ),
    (
        'Enterprise',
        'Full access with priority support',
        999000,
        'monthly',
        '{"bots": "unlimited", "strategies": "unlimited", "ai_credits": "unlimited", "support": "priority", "backtest": true, "custom_strategies": true}',
        '{"max_bots": 999, "max_strategies": 999, "max_trades_per_day": 9999, "ai_generations_per_month": 999}'
    )
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get user trading statistics
CREATE OR REPLACE FUNCTION get_user_trading_stats(user_uuid UUID)
RETURNS TABLE(
    total_bots BIGINT,
    active_bots BIGINT,
    total_trades BIGINT,
    total_profit NUMERIC,
    win_rate NUMERIC
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM public.bots WHERE user_id = user_uuid),
        (SELECT COUNT(*) FROM public.bots WHERE user_id = user_uuid AND status = 'running'),
        (SELECT COUNT(*) FROM public.trades WHERE user_id = user_uuid),
        (SELECT COALESCE(SUM(profit), 0) FROM public.trades WHERE user_id = user_uuid),
        (SELECT 
            CASE WHEN COUNT(*) > 0 THEN 
                (COUNT(CASE WHEN profit > 0 THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC * 100)
            ELSE 0 
            END 
        FROM public.trades WHERE user_id = user_uuid
        );
END;
$$;

-- Function to clean old logs (for maintenance)
CREATE OR REPLACE FUNCTION clean_old_logs(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.logs 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

CREATE OR REPLACE VIEW bot_performance_summary AS
SELECT 
    b.id,
    b.user_id,
    b.name,
    b.exchange,
    b.trading_pair,
    b.status,
    b.initial_balance,
    b.current_balance,
    b.profit,
    COUNT(t.id) as total_trades,
    COUNT(CASE WHEN t.profit > 0 THEN 1 END) as winning_trades,
    CASE 
        WHEN COUNT(t.id) > 0 THEN 
            (COUNT(CASE WHEN t.profit > 0 THEN 1 END)::NUMERIC / COUNT(t.id)::NUMERIC * 100)
        ELSE 0 
    END as win_rate,
    COALESCE(MAX(t.created_at), b.created_at) as last_activity
FROM public.bots b
LEFT JOIN public.trades t ON b.id = t.bot_id
GROUP BY b.id, b.user_id, b.name, b.exchange, b.trading_pair, b.status, 
         b.initial_balance, b.current_balance, b.profit, b.created_at;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;
