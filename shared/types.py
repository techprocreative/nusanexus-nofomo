"""
Shared types and interfaces for NusaNexus NoFOMO
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


# Enums
class BotStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
    PAUSED = "paused"


class ExchangeType(str, Enum):
    BINANCE = "binance"
    BYBIT = "bybit"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class SideType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class StrategyType(str, Enum):
    CUSTOM = "custom"
    AI_GENERATED = "ai_generated"
    MARKETPLACE = "marketplace"


class TimeFrame(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


# Core Models
class User(BaseModel):
    id: str
    email: str
    full_name: str
    subscription_plan: str
    created_at: datetime
    updated_at: datetime


class ExchangeCredentials(BaseModel):
    exchange: ExchangeType
    api_key_encrypted: str
    api_secret_encrypted: str
    is_testnet: bool = False


class Bot(BaseModel):
    id: str
    user_id: str
    name: str
    exchange: ExchangeType
    trading_pair: str
    timeframe: TimeFrame
    strategy: str
    status: BotStatus
    initial_balance: float
    current_balance: float
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    profit: float = 0.0
    profit_percentage: float = 0.0
    max_open_trades: int = 1
    stake_amount: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class Strategy(BaseModel):
    id: str
    user_id: str
    name: str
    description: str
    strategy_type: StrategyType
    content: str
    parameters: Dict[str, Any]
    performance: Dict[str, Any]
    is_public: bool = False
    created_at: datetime
    updated_at: datetime


class Trade(BaseModel):
    id: str
    bot_id: str
    exchange: ExchangeType
    trading_pair: str
    side: SideType
    order_type: OrderType
    amount: float
    price: float
    fee: float
    profit: float
    profit_percentage: float
    status: TradeStatus
    entry_time: datetime
    exit_time: Optional[datetime] = None
    exchange_order_id: Optional[str] = None
    exchange_trade_id: Optional[str] = None
    is_paper_trade: bool = False


class AIAnalysis(BaseModel):
    id: str
    bot_id: Optional[str]
    analysis_type: str
    input_data: Dict[str, Any]
    results: Dict[str, Any]
    recommendations: List[str]
    confidence_score: float
    created_at: datetime


class BacktestResult(BaseModel):
    id: str
    strategy_id: str
    trading_pair: str
    timeframe: TimeFrame
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    total_return: float
    total_return_percentage: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    best_trade: float
    worst_trade: float
    profit_factor: float
    created_at: datetime


# API Models
class BotCreate(BaseModel):
    name: str
    exchange: ExchangeType
    trading_pair: str
    timeframe: TimeFrame
    strategy: str
    initial_balance: float
    stake_amount: float
    max_open_trades: int = 1


class BotUpdate(BaseModel):
    name: Optional[str] = None
    strategy: Optional[str] = None
    max_open_trades: Optional[int] = None
    stake_amount: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class StrategyCreate(BaseModel):
    name: str
    description: str
    strategy_type: StrategyType
    content: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_public: bool = False


class StrategyPrompt(BaseModel):
    prompt: str
    trading_pair: str
    timeframe: TimeFrame
    risk_level: str
    style: str


class ExchangeConnectionRequest(BaseModel):
    exchange: ExchangeType
    api_key: str
    api_secret: str
    is_testnet: bool = False


# WebSocket Models
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime


class BotStatusUpdate(WebSocketMessage):
    type: str = "bot_status"
    data: Dict[str, Any] = {}


class TradeUpdate(WebSocketMessage):
    type: str = "trade_update"
    data: Dict[str, Any] = {}


class MarketDataUpdate(WebSocketMessage):
    type: str = "market_data"
    data: Dict[str, Any] = {}


# Error Models
class APIError(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationError(BaseModel):
    error: str
    field: str
    message: str


# Pagination Models
class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 20
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "desc"


class PaginatedResponse(BaseModel):
    data: List[Any]
    total: int
    page: int
    limit: int
    total_pages: int