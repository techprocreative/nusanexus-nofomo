# NusaNexus NoFOMO - API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Endpoints](#endpoints)
6. [WebSocket API](#websocket-api)
7. [Examples](#examples)

## Overview

The NusaNexus NoFOMO API provides comprehensive endpoints for managing trading bots, strategies, AI features, and user data. All endpoints are versioned and follow RESTful conventions.

### Base URL
```
Production: https://nusafx-backend.onrender.com/api/v1
Staging: https://staging-backend.onrender.com/api/v1
Development: http://localhost:8000/api/v1
```

### API Version
Current version: `v1`

## Authentication

### JWT Token Authentication

All protected endpoints require a valid JWT token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

1. **Register User**
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

2. **Login**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

3. **Response**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

## Rate Limiting

### Rate Limits by Endpoint

- **Authentication**: 5 requests per minute
- **API General**: 60 requests per minute
- **Trading**: 10 requests per minute
- **AI Requests**: 3 requests per minute

### Rate Limit Headers

All responses include rate limit information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1640995200
```

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  },
  "timestamp": "2025-11-10T03:19:00Z",
  "request_id": "req_123456789"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

## Endpoints

### Authentication

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "string",
  "password": "string",
  "full_name": "string"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid",
    "email": "string",
    "full_name": "string"
  }
}
```

#### POST /auth/login
Authenticate user and get access token.

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "string",
    "full_name": "string"
  }
}
```

#### POST /auth/refresh
Refresh access token.

**Response:**
```json
{
  "access_token": "string",
  "expires_in": 3600
}
```

### User Management

#### GET /users/me
Get current user profile.

**Response:**
```json
{
  "id": "uuid",
  "email": "string",
  "full_name": "string",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "subscription": {
    "plan": "free|pro|premium",
    "expires_at": "timestamp"
  }
}
```

#### PUT /users/me
Update user profile.

**Request Body:**
```json
{
  "full_name": "string",
  "settings": {
    "notifications": true,
    "risk_tolerance": "low|medium|high"
  }
}
```

### Trading Bots

#### GET /bots
List user's trading bots.

**Query Parameters:**
- `page` (int): Page number
- `limit` (int): Items per page (max 100)
- `status` (string): Filter by status
- `pair` (string): Filter by trading pair

**Response:**
```json
{
  "bots": [
    {
      "id": "uuid",
      "name": "string",
      "trading_pair": "BTC/USDT",
      "strategy": "rsi_macd",
      "status": "running|stopped|paused",
      "created_at": "timestamp",
      "updated_at": "timestamp",
      "stats": {
        "total_trades": 10,
        "win_rate": 0.7,
        "total_profit": 150.50,
        "max_drawdown": -5.2
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 50,
    "pages": 3
  }
}
```

#### POST /bots
Create a new trading bot.

**Request Body:**
```json
{
  "name": "My BTC Bot",
  "trading_pair": "BTC/USDT",
  "strategy": "rsi_macd",
  "parameters": {
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "stop_loss": 0.02,
    "take_profit": 0.04
  },
  "exchange": "binance|bybit",
  "initial_balance": 1000
}
```

**Response:**
```json
{
  "bot": {
    "id": "uuid",
    "name": "My BTC Bot",
    "status": "created",
    "created_at": "timestamp"
  }
}
```

#### GET /bots/{bot_id}
Get bot details.

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "trading_pair": "BTC/USDT",
  "strategy": "rsi_macd",
  "status": "running",
  "parameters": {
    "rsi_period": 14,
    "rsi_oversold": 30
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

#### PUT /bots/{bot_id}
Update bot configuration.

**Request Body:**
```json
{
  "name": "Updated Bot Name",
  "parameters": {
    "rsi_period": 21
  }
}
```

#### DELETE /bots/{bot_id}
Delete a bot.

**Response:**
```json
{
  "message": "Bot deleted successfully"
}
```

#### POST /bots/{bot_id}/start
Start a bot.

**Response:**
```json
{
  "message": "Bot started successfully",
  "status": "running"
}
```

#### POST /bots/{bot_id}/stop
Stop a bot.

**Response:**
```json
{
  "message": "Bot stopped successfully",
  "status": "stopped"
}
```

### Trading

#### GET /trades
Get bot trading history.

**Query Parameters:**
- `bot_id` (uuid): Filter by bot
- `start_date` (timestamp): Filter from date
- `end_date` (timestamp): Filter to date
- `pair` (string): Filter by trading pair
- `type` (string): Filter by trade type

**Response:**
```json
{
  "trades": [
    {
      "id": "uuid",
      "bot_id": "uuid",
      "pair": "BTC/USDT",
      "type": "buy|sell",
      "amount": 0.001,
      "price": 45000.00,
      "profit_loss": 25.50,
      "timestamp": "timestamp",
      "exchange_order_id": "string"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1000,
    "pages": 20
  }
}
```

#### GET /trades/{trade_id}
Get trade details.

#### GET /trading/pairs
Get available trading pairs.

**Response:**
```json
{
  "pairs": [
    {
      "symbol": "BTC/USDT",
      "base_asset": "BTC",
      "quote_asset": "USDT",
      "status": "active",
      "min_trade_amount": 0.001,
      "max_trade_amount": 100,
      "price_precision": 2,
      "amount_precision": 6
    }
  ]
}
```

### AI Strategies

#### POST /ai/generate-strategy
Generate AI-powered trading strategy.

**Request Body:**
```json
{
  "trading_pair": "BTC/USDT",
  "market_conditions": "bullish|bearish|sideways",
  "risk_tolerance": "low|medium|high",
  "timeframe": "1h|4h|1d",
  "additional_context": "Market is showing strong momentum with high volume"
}
```

**Response:**
```json
{
  "strategy": {
    "id": "uuid",
    "name": "AI Generated Strategy",
    "description": "Optimized strategy based on market analysis",
    "parameters": {
      "indicators": [
        {
          "name": "RSI",
          "period": 14,
          "oversold": 30,
          "overbought": 70
        }
      ],
      "entry_conditions": [
        {
          "type": "indicator",
          "indicator": "RSI",
          "condition": "below",
          "value": 30
        }
      ],
      "exit_conditions": [
        {
          "type": "profit",
          "value": 0.05
        }
      ]
    },
    "backtest_results": {
      "total_trades": 150,
      "win_rate": 0.73,
      "profit_factor": 2.1,
      "max_drawdown": 0.08,
      "sharpe_ratio": 1.85
    }
  }
}
```

#### POST /ai/analyze-market
Analyze market conditions for a trading pair.

**Request Body:**
```json
{
  "trading_pair": "BTC/USDT",
  "timeframe": "1h",
  "analysis_depth": "basic|detailed"
}
```

**Response:**
```json
{
  "analysis": {
    "trading_pair": "BTC/USDT",
    "current_price": 45000.00,
    "trend": "bullish|bearish|sideways",
    "volatility": "low|medium|high",
    "support_levels": [44000, 43500],
    "resistance_levels": [46000, 47000],
    "rsi": 65.5,
    "macd": {
      "macd": 150.25,
      "signal": 125.10,
      "histogram": 25.15
    },
    "recommendation": {
      "action": "buy|sell|hold",
      "confidence": 0.75,
      "reason": "Strong bullish momentum with RSI oversold bounce"
    }
  }
}
```

### Backtesting

#### POST /backtest
Run backtest on a strategy.

**Request Body:**
```json
{
  "strategy_id": "uuid",
  "trading_pair": "BTC/USDT",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z",
  "initial_balance": 10000,
  "commission": 0.001
}
```

**Response:**
```json
{
  "backtest_id": "uuid",
  "status": "running|completed|failed",
  "progress": 0.75,
  "results": {
    "total_trades": 250,
    "winning_trades": 175,
    "losing_trades": 75,
    "win_rate": 0.70,
    "total_return": 0.45,
    "annualized_return": 0.38,
    "max_drawdown": 0.12,
    "sharpe_ratio": 1.65,
    "profit_factor": 2.1,
    "trades": [
      {
        "entry_time": "2024-03-15T10:30:00Z",
        "exit_time": "2024-03-15T14:45:00Z",
        "pair": "BTC/USDT",
        "type": "buy",
        "amount": 0.2,
        "entry_price": 45000,
        "exit_price": 46500,
        "profit_loss": 30.00
      }
    ]
  }
}
```

#### GET /backtest/{backtest_id}
Get backtest results.

### Health & Status

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T03:19:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "exchanges": "healthy"
  }
}
```

#### GET /status
Detailed system status.

**Response:**
```json
{
  "status": "operational",
  "uptime": 86400,
  "version": "1.0.0",
  "metrics": {
    "active_bots": 45,
    "total_users": 1234,
    "api_requests_per_minute": 150
  }
}
```

## WebSocket API

### Connection

Connect to WebSocket for real-time updates:

```javascript
const ws = new WebSocket('wss://nusafx-backend.onrender.com/ws');

// Authenticate
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));
```

### Message Format

```json
{
  "type": "message_type",
  "data": {},
  "timestamp": "2025-11-10T03:19:00Z"
}
```

### Message Types

#### bot_status
Bot status updates.

```json
{
  "type": "bot_status",
  "data": {
    "bot_id": "uuid",
    "status": "running|stopped|paused",
    "timestamp": "timestamp"
  }
}
```

#### trade_executed
Trade execution notifications.

```json
{
  "type": "trade_executed",
  "data": {
    "bot_id": "uuid",
    "trade": {
      "id": "uuid",
      "pair": "BTC/USDT",
      "type": "buy",
      "amount": 0.001,
      "price": 45000.00,
      "timestamp": "timestamp"
    }
  }
}
```

#### market_update
Real-time market price updates.

```json
{
  "type": "market_update",
  "data": {
    "pair": "BTC/USDT",
    "price": 45000.00,
    "change_24h": 0.025,
    "volume": 1234567.89,
    "timestamp": "timestamp"
  }
}
```

## Examples

### Complete Bot Creation Flow

1. **Register User**
```bash
curl -X POST https://nusafx-backend.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'
```

2. **Login**
```bash
curl -X POST https://nusafx-backend.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

3. **Create Bot**
```bash
curl -X POST https://nusafx-backend.onrender.com/api/v1/bots \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My BTC Bot",
    "trading_pair": "BTC/USDT",
    "strategy": "rsi_macd",
    "parameters": {
      "rsi_period": 14,
      "rsi_oversold": 30,
      "rsi_overbought": 70
    }
  }'
```

4. **Start Bot**
```bash
curl -X POST https://nusafx-backend.onrender.com/api/v1/bots/bot-uuid/start \
  -H "Authorization: Bearer your-jwt-token"
```

### JavaScript Client Example

```javascript
class NusaFXClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async request(endpoint, options = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  async getBots() {
    return this.request('/bots');
  }

  async createBot(botData) {
    return this.request('/bots', {
      method: 'POST',
      body: JSON.stringify(botData)
    });
  }

  async startBot(botId) {
    return this.request(`/bots/${botId}/start`, {
      method: 'POST'
    });
  }
}

// Usage
const client = new NusaFXClient(
  'https://nusafx-backend.onrender.com/api/v1',
  'your-jwt-token'
);

client.getBots().then(bots => {
  console.log('Your bots:', bots);
});
```

## SDK Examples

### Python SDK

```python
from nusafx import NusaFXClient

client = NusaFXClient(
    base_url='https://nusafx-backend.onrender.com/api/v1',
    token='your-jwt-token'
)

# Get bots
bots = client.get_bots()
for bot in bots['bots']:
    print(f"Bot: {bot['name']} - Status: {bot['status']}")

# Create bot
bot = client.create_bot({
    'name': 'My Python Bot',
    'trading_pair': 'ETH/USDT',
    'strategy': 'rsi_macd',
    'parameters': {'rsi_period': 14}
})

# Start bot
client.start_bot(bot['bot']['id'])
```

## Changelog

### v1.0.0 (2025-11-10)
- Initial API release
- Authentication and user management
- Trading bot CRUD operations
- AI strategy generation
- Backtesting functionality
- WebSocket real-time updates