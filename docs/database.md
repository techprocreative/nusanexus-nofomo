# Database Schema - NusaNexus NoFOMO

## Overview

NusaNexus NoFOMO uses Supabase PostgreSQL with Row Level Security (RLS) for multi-tenant data isolation. The database is designed to support AI-powered crypto trading bots with comprehensive tracking, analytics, and SaaS subscription management.

## Architecture

### Multi-Tenant Design
- **Row Level Security (RLS)**: Enabled on all user data tables
- **User Isolation**: Each user can only access their own data
- **Public Resources**: Marketplace strategies are shared but still tracked by user
- **Secure API Keys**: Exchange credentials are stored encrypted

### Core Features
- **Bot Lifecycle Management**: Complete bot configuration and status tracking
- **Trade Execution**: Real-time trade recording and performance metrics
- **AI Integration**: Strategy generation and performance analysis
- **SaaS Billing**: Tripay payment integration with subscription management
- **Performance Analytics**: Comprehensive backtesting and performance metrics

## Database Schema

### Users Table
Extended user profile data that complements Supabase Auth:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    subscription_plan VARCHAR(50) DEFAULT 'free',
    exchange_credentials JSONB, -- Encrypted API keys
    preferences JSONB DEFAULT '{}',
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Key Features:**
- Links to Supabase Auth users (ID matches auth.uid())
- Stores encrypted exchange API credentials
- User preferences and settings
- Subscription plan tracking

### Bots Table
Trading bot configuration and real-time status:

```sql
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
```

**Key Features:**
- Exchange integration (Binance, Bybit)
- Real-time performance tracking
- Risk management parameters
- Paper/live trading support

### Strategies Table
Custom and AI-generated trading strategies:

```sql
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
```

**Key Features:**
- Three strategy types: custom, AI-generated, marketplace
- Strategy verification system
- Performance metrics storage
- Public marketplace for sharing strategies

### Trades Table
Individual trade execution records:

```sql
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
```

**Key Features:**
- Complete trade lifecycle tracking
- Profit/loss calculation
- Exchange order correlation
- Paper/live trade distinction

### Logs Table
Execution logs and AI interactions:

```sql
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
```

**Key Features:**
- Multi-source logging (bot runner, API, AI engine)
- Contextual information in JSONB
- Log level filtering

### AI Analyses Table
AI-generated strategy analyses and recommendations:

```sql
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
```

**Key Features:**
- AI analysis tracking
- Confidence scoring
- Token usage monitoring
- Multiple analysis types

### Backtest Results Table
Strategy backtesting results and performance metrics:

```sql
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
```

**Key Features:**
- Comprehensive performance metrics
- Risk-adjusted returns
- Trade statistics
- Multiple timeframe support

### Plans Table (SaaS)
Subscription tiers and features:

```sql
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
```

**Key Features:**
- Flexible feature configuration
- Usage limits enforcement
- Annual/monthly pricing
- Public plan catalog

### Invoices Table (Tripay Integration)
Payment transaction tracking:

```sql
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
```

**Key Features:**
- Tripay payment integration
- Invoice lifecycle tracking
- Customer information storage

### Subscriptions Table
Active subscription management:

```sql
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
```

**Key Features:**
- Subscription lifecycle management
- Auto-renewal support
- Trial period tracking

## Row Level Security (RLS) Policies

### Users Policies
```sql
CREATE POLICY "Users can view their own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id);
```

### Bots Policies
```sql
CREATE POLICY "Users can view their own bots"
    ON bots FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own bots"
    ON bots FOR INSERT
    WITH CHECK (auth.uid() = user_id);
```

### Strategies Policies
```sql
CREATE POLICY "Users can view their own strategies"
    ON strategies FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view public marketplace strategies"
    ON strategies FOR SELECT
    USING (is_public = true AND strategy_type = 'marketplace');
```

## Performance Indexes

### Critical Indexes
```sql
-- Bots indexes
CREATE INDEX idx_bots_user_id ON bots(user_id);
CREATE INDEX idx_bots_status ON bots(status);
CREATE INDEX idx_bots_exchange ON bots(exchange);

-- Trades indexes
CREATE INDEX idx_trades_bot_id ON trades(bot_id);
CREATE INDEX idx_trades_entry_time ON trades(entry_time);
CREATE INDEX idx_trades_user_date ON trades(user_id, entry_time);

-- Strategies indexes
CREATE INDEX idx_strategies_user_id ON strategies(user_id);
CREATE INDEX idx_strategies_marketplace ON strategies(is_public, strategy_type, is_verified) 
    WHERE is_public = true AND strategy_type = 'marketplace';
```

## Database Functions

### Bot Statistics Update
```sql
CREATE OR REPLACE FUNCTION update_bot_statistics()
RETURNS TRIGGER AS $$
-- Automatically updates bot performance metrics when trades change
$$;
```

### Bot Limits Validation
```sql
CREATE OR REPLACE FUNCTION validate_bot_limits()
RETURNS TRIGGER AS $$
-- Enforces subscription plan limits on bot creation
$$;
```

### Trading Performance Analytics
```sql
CREATE OR REPLACE FUNCTION get_user_trading_performance(user_uuid UUID, days_back INTEGER DEFAULT 30)
RETURNS TABLE (...)
-- Provides comprehensive trading performance metrics
$$;
```

## Views for Common Queries

### Bot Performance Summary
```sql
CREATE OR REPLACE VIEW bot_performance_summary AS
SELECT 
    b.*,
    CASE 
        WHEN b.total_trades > 0 THEN 
            ROUND((b.winning_trades::DECIMAL / b.total_trades * 100), 2)
        ELSE 0 
    END as win_rate_percentage,
    u.email as user_email,
    u.full_name as user_name
FROM bots b
JOIN users u ON u.id = b.user_id;
```

### Strategy Marketplace
```sql
CREATE OR REPLACE VIEW strategy_marketplace AS
SELECT 
    s.*,
    u.full_name as author_name,
    COALESCE(AVG(br.total_return_percentage), 0) as avg_return_percentage,
    COUNT(br.id) as backtest_count
FROM strategies s
JOIN users u ON u.id = s.user_id
LEFT JOIN backtest_results br ON br.strategy_id = s.id
WHERE s.is_public = true 
    AND s.strategy_type = 'marketplace'
    AND s.is_verified = true
GROUP BY s.id, s.name, s.description, s.strategy_type, s.risk_level, 
         s.category, s.tags, s.backtest_results, s.created_at, u.full_name;
```

## Security Best Practices

1. **Row Level Security (RLS)**: Enabled on all user data tables
2. **API Key Encryption**: Exchange API keys stored encrypted using AES-256
3. **JWT Authentication**: Supabase Auth for user management
4. **Input Validation**: All inputs validated with Pydantic models
5. **Audit Logging**: All important actions logged with timestamps
6. **Subscription Limits**: Database functions enforce plan limits
7. **Data Isolation**: Complete user data isolation via RLS policies

## Migration Files

The database schema is managed through migration files:

1. **001_initial_schema.sql**: Core table creation
2. **002_indexes_and_triggers.sql**: Performance optimization
3. **003_sample_data.sql**: Development and testing data

## Setup Process

### 1. Environment Setup
```bash
# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"
```

### 2. Database Setup
```bash
# Run the setup script
python nusafxtrade/backend/scripts/setup_database.py

# Or manually apply migrations in Supabase SQL Editor
# Upload and execute the migration files in order
```

### 3. Verification
```bash
# Verify database setup
python nusafxtrade/backend/scripts/setup_database.py --skip-verification false
```

## Sample Data

The `003_sample_data.sql` migration includes:
- 3 subscription plans (Free, Pro, Enterprise)
- 3 sample users with different subscription levels
- 3 sample strategies (AI-generated, marketplace, custom)
- Sample bots with different configurations
- Trade records for testing
- AI analysis examples
- Backtest results
- System logs
- Payment invoices

## Development Guidelines

1. **Always use UUIDs** for primary keys
2. **Enable RLS** on all user tables
3. **Use proper indexes** for frequently queried columns
4. **Validate data** with check constraints
5. **Use triggers** for automatic calculations
6. **Store timestamps** with timezone information
7. **Use JSONB** for flexible data structures
8. **Document changes** in migration files

## Troubleshooting

### Common Issues

1. **RLS Policy Errors**: Ensure auth.uid() is properly set
2. **Permission Denied**: Check RLS policies for table access
3. **Index Missing**: Verify indexes for performance-critical queries
4. **Function Not Found**: Ensure migration files are applied in order

### Performance Optimization

1. **Monitor slow queries** using Supabase dashboard
2. **Add indexes** for new query patterns
3. **Use views** for complex, frequently-used queries
4. **Archive old data** using cleanup functions
5. **Monitor storage** usage and optimize data types

## API Integration

The database schema is designed to work seamlessly with:

- **Supabase Client**: JavaScript/TypeScript client for frontend
- **PostgREST**: Automatic REST API generation
- **Supabase Realtime**: Real-time subscriptions
- **FastAPI**: Python backend with asyncpg
- **SQLAlchemy**: ORM integration for complex queries

## Monitoring and Maintenance

### Automated Tasks
- Log cleanup (old logs are automatically removed)
- Bot statistics updates (trigger-based)
- Subscription expiry notifications
- Performance metric calculations

### Manual Maintenance
- Regular backup verification
- Index performance monitoring
- Query optimization
- Storage usage analysis

This comprehensive database schema provides a solid foundation for the NusaNexus NoFOMO AI-powered crypto trading platform, ensuring scalability, security, and performance for all features outlined in the blueprint.