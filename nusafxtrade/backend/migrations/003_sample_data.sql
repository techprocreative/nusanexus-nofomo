-- NusaNexus NoFOMO Sample Data for Development
-- Migration: 003_sample_data
-- Created: 2025-11-10
-- Description: Sample data for development and testing

-- =============================================================================
-- SAMPLE SUBSCRIPTION PLANS
-- =============================================================================

INSERT INTO plans (id, name, description, price_monthly, price_yearly, features, max_bots, max_strategies, ai_requests_per_month, backtest_minutes_per_month, priority_support, custom_strategies, api_access, sort_order) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Free', 'Perfect for getting started with automated trading', 0.00, 0.00, '{
    "features": [
        "1 active bot",
        "5 custom strategies",
        "Basic backtesting (100 trades)",
        "Community support",
        "Paper trading",
        "Basic market data"
    ],
    "limitations": [
        "No AI strategy generation",
        "No real trading",
        "Limited technical indicators"
    ]
}', 1, 5, 0, 100, false, false, false, 1),

('550e8400-e29b-41d4-a716-446655440002', 'Pro', 'Ideal for serious traders who want more control', 29.99, 299.99, '{
    "features": [
        "5 active bots",
        "50 custom strategies",
        "Unlimited backtesting",
        "AI strategy generator",
        "Real trading on testnet",
        "Advanced technical indicators",
        "Email support",
        "Strategy optimization",
        "Risk management tools"
    ],
    "benefits": [
        "25% savings with annual billing",
        "Priority processing",
        "Advanced analytics"
    ]
}', 5, 50, 100, 1000, false, true, true, 2),

('550e8400-e29b-41d4-a716-446655440003', 'Enterprise', 'For professional traders and institutions', 99.99, 999.99, '{
    "features": [
        "Unlimited bots",
        "Unlimited strategies",
        "Custom AI model training",
        "Real trading (live markets)",
        "Dedicated account manager",
        "24/7 priority support",
        "API access with rate limits",
        "White-label options",
        "Custom integrations",
        "Advanced risk management",
        "Portfolio optimization",
        "Multi-exchange support"
    ],
    "services": [
        "Custom strategy development",
        "Performance consulting",
        "Risk assessment",
        "Market analysis"
    ]
}', -1, -1, 1000, 10000, true, true, true, 3);

-- =============================================================================
-- SAMPLE USERS (These would normally come from Supabase Auth)
-- =============================================================================

INSERT INTO users (id, email, full_name, subscription_plan, preferences, is_active) VALUES
('660e8400-e29b-41d4-a716-446655440001', 'john.doe@example.com', 'John Doe', 'free', '{
    "timezone": "UTC",
    "notifications": {
        "email": true,
        "webhook": false
    },
    "dashboard": {
        "default_view": "performance",
        "chart_theme": "dark"
    }
}', true),

('660e8400-e29b-41d4-a716-446655440002', 'jane.smith@example.com', 'Jane Smith', 'pro', '{
    "timezone": "America/New_York",
    "notifications": {
        "email": true,
        "webhook": true,
        "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    },
    "dashboard": {
        "default_view": "bots",
        "chart_theme": "light"
    }
}', true),

('660e8400-e29b-41d4-a716-446655440003', 'admin@nusanexus.com', 'Admin User', 'enterprise', '{
    "timezone": "UTC",
    "notifications": {
        "email": true,
        "webhook": true
    },
    "admin": {
        "can_manage_all_users": true,
        "can_view_all_strategies": true
    }
}', true);

-- =============================================================================
-- SAMPLE SUBSCRIPTIONS
-- =============================================================================

INSERT INTO subscriptions (id, user_id, plan_id, status, started_at, expires_at, auto_renew) VALUES
('770e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'active', NOW(), NOW() + INTERVAL '30 days', true),
('770e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', 'active', NOW() - INTERVAL '15 days', NOW() + INTERVAL '15 days', true),
('770e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', 'active', NOW() - INTERVAL '60 days', NOW() + INTERVAL '30 days', true);

-- =============================================================================
-- SAMPLE STRATEGIES (Marketplace)
-- =============================================================================

INSERT INTO strategies (id, user_id, name, description, strategy_type, content, parameters, performance, is_public, is_verified, risk_level, category) VALUES

-- AI-Generated RSI Strategy
('880e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440003', 
 'AI RSI Overbought/Oversold', 
 'AI-generated strategy using RSI indicator for buy/sell signals. Optimized for trending markets with clear overbought/oversold levels.',
 'ai_generated',
 'class AIRSIOverboughtOversold(Strategy):
    """
    AI-Generated RSI Strategy
    Buys when RSI crosses above 30 (oversold recovery)
    Sells when RSI crosses below 70 (overbought reversal)
    """
    
    def populate_indicators(self, metadata: dict, dataframe: DataFrame) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe
    
    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] < 30) &  # Oversold
                (dataframe["volume"] > 0)  # Make sure Volume is not 0
            ),
            "buy",
        ] = 1
        return dataframe
    
    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] > 70) &  # Overbought
                (dataframe["volume"] > 0)  # Make sure Volume is not 0
            ),
            "sell",
        ] = 1
        return dataframe',
 '{"rsi_period": 14, "rsi_overbought": 70, "rsi_oversold": 30, "volume_filter": true}',
 '{"total_trades": 245, "win_rate": 68.5, "profit_factor": 1.85, "max_drawdown": 8.2, "sharpe_ratio": 1.42}',
 true, true, 'medium', 'oscillator'),

-- EMA Crossover Strategy
('880e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440003',
 'Classic EMA Crossover',
 'Traditional EMA crossover strategy using 12 and 26 period EMAs. Simple yet effective for trending markets.',
 'marketplace',
 'class ClassicEMACrossover(Strategy):
    """
    Classic EMA Crossover Strategy
    Buy when EMA12 crosses above EMA26
    Sell when EMA12 crosses below EMA26
    """
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema12"] = ta.EMA(dataframe, timeperiod=12)
        dataframe["ema26"] = ta.EMA(dataframe, timeperiod=26)
        return dataframe
    
    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["ema12"] > dataframe["ema26"]) &  # EMA12 above EMA26
                (dataframe["volume"] > 0)
            ),
            "buy",
        ] = 1
        return dataframe
    
    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["ema12"] < dataframe["ema26"]) &  # EMA12 below EMA26
                (dataframe["volume"] > 0)
            ),
            "sell",
        ] = 1
        return dataframe',
 '{"ema_fast": 12, "ema_slow": 26, "volume_filter": true}',
 '{"total_trades": 189, "win_rate": 62.4, "profit_factor": 1.67, "max_drawdown": 12.1, "sharpe_ratio": 1.28}',
 true, true, 'low', 'trend'),

-- Custom Bollinger Bands Strategy
('880e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440001',
 'Bollinger Bands Mean Reversion',
 'Mean reversion strategy using Bollinger Bands. Buys oversold conditions and sells overbought conditions.',
 'custom',
 'class BollingerBandsMeanReversion(Strategy):
    """
    Bollinger Bands Mean Reversion Strategy
    Buys when price touches lower band and RSI confirms oversold
    Sells when price touches upper band and RSI confirms overbought
    """
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bollinger = ta.BBANDS(dataframe, timeperiod=20, std_dev=2)
        dataframe["bb_lower"] = bollinger["bb_lowerband"]
        dataframe["bb_middle"] = bollinger["bb_middleband"]
        dataframe["bb_upper"] = bollinger["bb_upperband"]
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe
    
    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"] <= dataframe["bb_lower"]) &  # Price at lower band
                (dataframe["rsi"] < 35) &  # RSI oversold
                (dataframe["volume"] > 0)
            ),
            "buy",
        ] = 1
        return dataframe
    
    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"] >= dataframe["bb_upper"]) &  # Price at upper band
                (dataframe["rsi"] > 65) &  # RSI overbought
                (dataframe["volume"] > 0)
            ),
            "sell",
        ] = 1
        return dataframe',
 '{"bb_period": 20, "bb_std": 2, "rsi_oversold": 35, "rsi_overbought": 65, "volume_filter": true}',
 '{"total_trades": 156, "win_rate": 71.2, "profit_factor": 2.1, "max_drawdown": 6.8, "sharpe_ratio": 1.65}',
 true, true, 'medium', 'mean_reversion');

-- =============================================================================
-- SAMPLE BOTS
-- =============================================================================

INSERT INTO bots (id, user_id, name, exchange, trading_pair, timeframe, strategy, status, initial_balance, current_balance, total_trades, winning_trades, profit, profit_percentage, stake_amount, max_open_trades, is_paper_trade, last_trade_at) VALUES

-- John Doe's Free Bot
('990e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 'BTC RSI Bot', 'binance', 'BTC/USDT', '1h', 'AIRSIOverboughtOversold', 'stopped', 100.0, 103.45, 12, 8, 3.45, 3.45, 10.0, 1, true, NOW() - INTERVAL '2 hours'),

-- Jane Smith's Pro Bots
('990e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440002', 'ETH EMA Cross', 'binance', 'ETH/USDT', '15m', 'ClassicEMACrossover', 'running', 1000.0, 1078.32, 45, 28, 78.32, 7.83, 50.0, 2, true, NOW() - INTERVAL '5 minutes'),

('990e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440002', 'ADA Bollinger', 'bybit', 'ADA/USDT', '5m', 'BollingerBandsMeanReversion', 'running', 500.0, 523.67, 67, 48, 23.67, 4.73, 25.0, 1, true, NOW() - INTERVAL '1 minute'),

-- Admin's Enterprise Bot
('990e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440003', 'Multi-Asset Portfolio', 'binance', 'BTC/USDT', '1h', 'AIRSIOverboughtOversold', 'running', 10000.0, 11245.89, 234, 156, 1245.89, 12.46, 200.0, 5, false, NOW() - INTERVAL '30 seconds');

-- =============================================================================
-- SAMPLE TRADES
-- =============================================================================

INSERT INTO trades (id, bot_id, user_id, exchange, trading_pair, side, order_type, amount, price, fee, profit, profit_percentage, status, entry_time, exit_time, holding_duration, is_paper_trade, signal_price) VALUES

-- Sample trades for John Doe's Bot
('aa0e8400-e29b-41d4-a716-446655440001', '990e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 'binance', 'BTC/USDT', 'buy', 'market', 0.001, 43250.00, 0.065, 0, 0, 'open', NOW() - INTERVAL '1 hour', NULL, NULL, true, 43200.00),

('aa0e8400-e29b-41d4-a716-446655440002', '990e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 'binance', 'BTC/USDT', 'buy', 'limit', 0.001, 42800.00, 0.064, 1.25, 2.89, 'closed', NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days 4 hours', INTERVAL '20 hours', true, 42800.00),

-- Sample trades for Jane Smith's ETH Bot
('aa0e8400-e29b-41d4-a716-446655440003', '990e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440002', 'binance', 'ETH/USDT', 'buy', 'market', 0.5, 2180.50, 1.09, 0, 0, 'open', NOW() - INTERVAL '15 minutes', NULL, NULL, true, 2175.00),

('aa0e8400-e29b-41d4-a716-446655440004', '990e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440002', 'binance', 'ETH/USDT', 'buy', 'limit', 0.5, 2150.00, 1.08, 15.75, 4.65, 'closed', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '30 minutes', INTERVAL '1 hour 30 minutes', true, 2150.00),

-- Sample trades for Admin's Bot
('aa0e8400-e29b-41d4-a716-446655440005', '990e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440003', 'binance', 'BTC/USDT', 'buy', 'market', 0.01, 43250.00, 0.65, 125.50, 2.89, 'closed', NOW() - INTERVAL '1 day', NOW() - INTERVAL '12 hours', INTERVAL '12 hours', false, 43200.00),

('aa0e8400-e29b-41d4-a716-446655440006', '990e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440003', 'binance', 'BTC/USDT', 'sell', 'limit', 0.01, 44500.00, 0.67, -8.25, -0.64, 'closed', NOW() - INTERVAL '6 hours', NOW() - INTERVAL '3 hours', INTERVAL '3 hours', false, 44550.00);

-- =============================================================================
-- SAMPLE AI ANALYSES
-- =============================================================================

INSERT INTO ai_analyses (id, user_id, bot_id, strategy_id, analysis_type, input_data, results, recommendations, confidence_score, model_used, tokens_used) VALUES

('bb0e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', '990e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 'performance', '{
    "bot_id": "990e8400-e29b-41d4-a716-446655440001",
    "timeframe": "30d",
    "metrics": ["win_rate", "profit_factor", "max_drawdown"]
}', '{
    "win_rate": 66.67,
    "profit_factor": 1.85,
    "max_drawdown": 8.2,
    "avg_trade_duration": "2.5h",
    "best_performing_pair": "BTC/USDT",
    "risk_level": "medium"
}', ARRAY[
    'Consider increasing position size slightly given strong performance',
    'Monitor BTC market volatility during high-impact news',
    'Current strategy is performing well, maintain current parameters'
], 0.89, 'gpt-4', 245),

('bb0e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440002', '990e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440002', 'optimization', '{
    "bot_id": "990e8400-e29b-41d4-a716-446655440002",
    "current_parameters": {"ema_fast": 12, "ema_slow": 26},
    "optimization_target": "profit_factor"
}', '{
    "current_profit_factor": 1.67,
    "optimized_parameters": {"ema_fast": 10, "ema_slow": 22},
    "projected_improvement": "12.5%",
    "backtest_period": "90d"
}', ARRAY[
    'Try EMA(10,22) parameters for better trend following',
    'Consider adding volume confirmation to reduce false signals',
    'Monitor performance for 2 weeks before permanent changes'
], 0.92, 'gpt-4', 312);

-- =============================================================================
-- SAMPLE BACKTEST RESULTS
-- =============================================================================

INSERT INTO backtest_results (id, strategy_id, user_id, trading_pair, timeframe, start_date, end_date, initial_balance, final_balance, total_return, total_return_percentage, max_drawdown, sharpe_ratio, sortino_ratio, win_rate, profit_factor, total_trades, winning_trades, losing_trades, best_trade, worst_trade, avg_trade, max_consecutive_wins, max_consecutive_losses) VALUES

('cc0e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440003', 'BTC/USDT', '1h', '2024-01-01 00:00:00+00', '2024-03-31 23:59:59+00', 10000.0, 11850.50, 1850.50, 18.51, 8.2, 1.42, 1.68, 68.5, 1.85, 245, 168, 77, 125.30, -45.60, 7.55, 8, 3),

('cc0e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440003', 'ETH/USDT', '15m', '2024-01-01 00:00:00+00', '2024-03-31 23:59:59+00', 5000.0, 5834.25, 834.25, 16.69, 12.1, 1.28, 1.45, 62.4, 1.67, 189, 118, 71, 67.80, -23.40, 4.41, 6, 2),

('cc0e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440001', 'ADA/USDT', '5m', '2024-02-01 00:00:00+00', '2024-04-30 23:59:59+00', 1000.0, 1206.80, 206.80, 20.68, 6.8, 1.65, 1.92, 71.2, 2.1, 156, 111, 45, 18.90, -8.50, 1.33, 12, 1);

-- =============================================================================
-- SAMPLE LOGS
-- =============================================================================

INSERT INTO logs (id, user_id, bot_id, strategy_id, log_level, message, context, source, created_at) VALUES

('dd0e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', '990e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 'info', 'Bot started successfully', '{"bot_id": "990e8400-e29b-41d4-a716-446655440001", "strategy": "AIRSIOverboughtOversold"}', 'bot_runner', NOW() - INTERVAL '2 days'),

('dd0e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440001', '990e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 'info', 'Buy signal detected for BTC/USDT', '{"pair": "BTC/USDT", "price": 43250.00, "rsi": 28.5}', 'bot_runner', NOW() - INTERVAL '1 hour'),

('dd0e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440002', '990e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440002', 'info', 'Trade executed successfully', '{"side": "buy", "amount": 0.5, "price": 2180.50}', 'exchange_connector', NOW() - INTERVAL '15 minutes'),

('dd0e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440002', '990e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440002', 'info', 'AI analysis completed', '{"analysis_id": "bb0e8400-e29b-41d4-a716-446655440002", "confidence": 0.92}', 'ai_engine', NOW() - INTERVAL '5 minutes'),

('dd0e8400-e29b-41d4-a716-446655440005', '660e8400-e29b-41d4-a716-446655440003', '990e8400-e29b-41d4-a716-446655440004', '880e8400-e29b-41d4-a716-446655440001', 'warning', 'High volatility detected', '{"volatility_score": 8.5, "recommendation": "reduce_position_size"}', 'risk_manager', NOW() - INTERVAL '30 minutes');

-- =============================================================================
-- SAMPLE INVOICES
-- =============================================================================

INSERT INTO invoices (id, user_id, plan_id, tripay_invoice_id, amount, status, payment_method, transaction_id, customer_name, customer_email, created_at, updated_at) VALUES

('ee0e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', 'TRX-' || extract(epoch from now())::bigint, 29.99, 'paid', 'Credit Card', 'TXN-123456789', 'Jane Smith', 'jane.smith@example.com', NOW() - INTERVAL '15 days', NOW() - INTERVAL '15 days'),

('ee0e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', 'TRX-' || (extract(epoch from now())::bigint + 1), 99.99, 'paid', 'Bank Transfer', 'TXN-987654321', 'Admin User', 'admin@nusanexus.com', NOW() - INTERVAL '60 days', NOW() - INTERVAL '60 days');

-- =============================================================================
-- UPDATE USER SUBSCRIPTION PLANS
-- =============================================================================

-- Update users to reflect their actual subscription plans
UPDATE users SET subscription_plan = 'pro' WHERE email = 'jane.smith@example.com';
UPDATE users SET subscription_plan = 'enterprise' WHERE email = 'admin@nusanexus.com';