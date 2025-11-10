-- NusaNexus NoFOMO Initial Database Schema
-- Migration: 001_initial_schema
-- Created: 2025-11-10
-- Description: Creates the complete multi-tenant database structure for NusaNexus NoFOMO

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- Users table (extends Supabase auth.users)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    subscription_plan VARCHAR(50) DEFAULT 'free',
    exchange_credentials JSONB,
    preferences JSONB DEFAULT '{}',
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bots table
CREATE TABLE bots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    exchange VARCHAR(50) NOT NULL CHECK (exchange IN ('binance', 'bybit')),
    trading_pair VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL CHECK (timeframe IN ('1m', '5m', '15m', '30m', '1h', '4h', '1d')),
    strategy VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'stopped' CHECK (status IN ('running', 'stopped', 'error', 'paused')),
    initial_balance DECIMAL(20,8) NOT NULL,
    current_balance DECIMAL(20,8) NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    profit DECIMAL(20,8) DEFAULT 0,
    profit_percentage DECIMAL(10,4) DEFAULT 0,
    max_open_trades INTEGER DEFAULT 1,
    stake_amount DECIMAL(20,8) NOT NULL,
    stop_loss DECIMAL(10,4),
    take_profit DECIMAL(10,4),
    risk_percentage DECIMAL(5,2) DEFAULT 2.0,
    is_paper_trade BOOLEAN DEFAULT true,
    last_trade_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Strategies table
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL CHECK (strategy_type IN ('custom', 'ai_generated', 'marketplace')),
    content TEXT, -- Python strategy code
    parameters JSONB DEFAULT '{}',
    performance JSONB DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    backtest_results JSONB,
    tags TEXT[],
    category VARCHAR(100),
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trades table
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_id UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exchange VARCHAR(50) NOT NULL,
    trading_pair VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell')),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('market', 'limit')),
    amount DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    fee DECIMAL(20,8) DEFAULT 0,
    profit DECIMAL(20,8) DEFAULT 0,
    profit_percentage DECIMAL(10,4) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled')),
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE,
    holding_duration INTERVAL,
    exchange_order_id VARCHAR(255),
    exchange_trade_id VARCHAR(255),
    is_paper_trade BOOLEAN DEFAULT true,
    signal_price DECIMAL(20,8),
    stop_loss_price DECIMAL(20,8),
    take_profit_price DECIMAL(20,8),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Logs table
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    log_level VARCHAR(20) NOT NULL CHECK (log_level IN ('info', 'warning', 'error', 'debug')),
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    source VARCHAR(100), -- bot_runner, api, ai_engine, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI Analyses table
CREATE TABLE ai_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL CHECK (analysis_type IN ('performance', 'risk', 'optimization', 'backtest')),
    input_data JSONB NOT NULL,
    results JSONB NOT NULL,
    recommendations TEXT[],
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    model_used VARCHAR(100),
    tokens_used INTEGER DEFAULT 0,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Backtest Results table
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trading_pair VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    initial_balance DECIMAL(20,8) NOT NULL,
    final_balance DECIMAL(20,8) NOT NULL,
    total_return DECIMAL(20,8) NOT NULL,
    total_return_percentage DECIMAL(10,4) NOT NULL,
    max_drawdown DECIMAL(10,4) NOT NULL,
    sharpe_ratio DECIMAL(8,4),
    sortino_ratio DECIMAL(8,4),
    win_rate DECIMAL(5,2) NOT NULL,
    profit_factor DECIMAL(8,4),
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    best_trade DECIMAL(20,8) NOT NULL,
    worst_trade DECIMAL(20,8) NOT NULL,
    avg_trade DECIMAL(20,8),
    max_consecutive_wins INTEGER DEFAULT 0,
    max_consecutive_losses INTEGER DEFAULT 0,
    calmar_ratio DECIMAL(8,4),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Plans table (SaaS subscription tiers)
CREATE TABLE plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    price_monthly DECIMAL(10,2) NOT NULL,
    price_yearly DECIMAL(10,2),
    features JSONB NOT NULL,
    max_bots INTEGER NOT NULL,
    max_strategies INTEGER NOT NULL,
    ai_requests_per_month INTEGER,
    backtest_minutes_per_month INTEGER DEFAULT 0,
    priority_support BOOLEAN DEFAULT false,
    custom_strategies BOOLEAN DEFAULT false,
    api_access BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Invoices table (Tripay integration)
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES plans(id) ON DELETE SET NULL,
    tripay_invoice_id VARCHAR(255) UNIQUE,
    tripay_merchant_id VARCHAR(255),
    reference_id VARCHAR(255),
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'paid', 'failed', 'expired', 'cancelled')),
    payment_method VARCHAR(100),
    payment_channel VARCHAR(100),
    transaction_id VARCHAR(255),
    description TEXT,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    customer_phone VARCHAR(50),
    expired_at TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscriptions table (track active subscriptions)
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('active', 'cancelled', 'expired', 'trial')),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    auto_renew BOOLEAN DEFAULT true,
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

-- Enable RLS on all user-related tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE backtest_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Users can view their own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON users FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Bots policies
CREATE POLICY "Users can view their own bots"
    ON bots FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own bots"
    ON bots FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own bots"
    ON bots FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own bots"
    ON bots FOR DELETE
    USING (auth.uid() = user_id);

-- Strategies policies
CREATE POLICY "Users can view their own strategies"
    ON strategies FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view public marketplace strategies"
    ON strategies FOR SELECT
    USING (is_public = true AND strategy_type = 'marketplace');

CREATE POLICY "Users can create their own strategies"
    ON strategies FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own strategies"
    ON strategies FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own strategies"
    ON strategies FOR DELETE
    USING (auth.uid() = user_id);

-- Trades policies
CREATE POLICY "Users can view trades from their own bots"
    ON trades FOR SELECT
    USING (
        user_id = auth.uid() OR
        bot_id IN (SELECT id FROM bots WHERE user_id = auth.uid())
    );

CREATE POLICY "Users can create trades for their own bots"
    ON trades FOR INSERT
    WITH CHECK (
        user_id = auth.uid() OR
        bot_id IN (SELECT id FROM bots WHERE user_id = auth.uid())
    );

CREATE POLICY "Users can update trades from their own bots"
    ON trades FOR UPDATE
    USING (
        user_id = auth.uid() OR
        bot_id IN (SELECT id FROM bots WHERE user_id = auth.uid())
    );

-- Logs policies
CREATE POLICY "Users can view logs from their own bots"
    ON logs FOR SELECT
    USING (
        user_id = auth.uid() OR
        bot_id IN (SELECT id FROM bots WHERE user_id = auth.uid()) OR
        strategy_id IN (SELECT id FROM strategies WHERE user_id = auth.uid())
    );

CREATE POLICY "Users can create logs for their own resources"
    ON logs FOR INSERT
    WITH CHECK (
        user_id = auth.uid() OR
        bot_id IN (SELECT id FROM bots WHERE user_id = auth.uid()) OR
        strategy_id IN (SELECT id FROM strategies WHERE user_id = auth.uid())
    );

-- AI Analyses policies
CREATE POLICY "Users can view their own AI analyses"
    ON ai_analyses FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own AI analyses"
    ON ai_analyses FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Backtest Results policies
CREATE POLICY "Users can view their own backtest results"
    ON backtest_results FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own backtest results"
    ON backtest_results FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Invoices policies
CREATE POLICY "Users can view their own invoices"
    ON invoices FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own invoices"
    ON invoices FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Subscriptions policies
CREATE POLICY "Users can view their own subscriptions"
    ON subscriptions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own subscriptions"
    ON subscriptions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own subscriptions"
    ON subscriptions FOR UPDATE
    USING (auth.uid() = user_id);

-- Plans table (public read access, no RLS)
ALTER TABLE plans DISABLE ROW LEVEL SECURITY;