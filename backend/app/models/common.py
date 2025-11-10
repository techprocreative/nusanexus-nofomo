"""
Common Pydantic models for NusaNexus NoFOMO
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


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


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LogLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"


class AnalysisType(str, Enum):
    PERFORMANCE = "performance"
    RISK = "risk"
    OPTIMIZATION = "optimization"
    BACKTEST = "backtest"


# API Response Models
class APIResponse(BaseModel):
    success: bool = True
    message: str = "Success"
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Pagination Models
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")


class PaginatedResponse(BaseModel):
    data: List[Any]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool


# WebSocket Models
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=_utcnow)


class BotStatusUpdate(WebSocketMessage):
    type: str = "bot_status"
    data: Dict[str, Any] = {}


class TradeUpdate(WebSocketMessage):
    type: str = "trade_update"
    data: Dict[str, Any] = {}


class MarketDataUpdate(WebSocketMessage):
    type: str = "market_data"
    data: Dict[str, Any] = {}


# Health Check Models
class HealthStatus(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=_utcnow)
    version: str
    services: Dict[str, str]


class DatabaseHealth(BaseModel):
    status: str
    response_time_ms: float
    connected_clients: int


class RedisHealth(BaseModel):
    status: str
    response_time_ms: float
    connected_clients: int


class ExchangeHealth(BaseModel):
    status: str
    response_time_ms: float
    exchanges: Dict[str, str]
