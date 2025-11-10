"""
Bot Pydantic models for NusaNexus NoFOMO
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from .common import BotStatus, ExchangeType, TimeFrame


# Base Bot Model
class BotBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    exchange: ExchangeType
    trading_pair: str = Field(..., min_length=3, max_length=20)
    timeframe: TimeFrame
    strategy: str = Field(..., min_length=1, max_length=255)
    initial_balance: float = Field(..., gt=0)
    max_open_trades: int = Field(1, ge=1, le=10)
    stake_amount: float = Field(..., gt=0)
    stop_loss: Optional[float] = Field(None, ge=0, le=100)
    take_profit: Optional[float] = Field(None, ge=0, le=1000)
    risk_percentage: float = Field(2.0, ge=0.1, le=100.0)
    is_paper_trade: bool = True


# Bot Response Model
class BotResponse(BotBase):
    id: str
    user_id: str
    status: BotStatus
    current_balance: float
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    profit: float = 0.0
    profit_percentage: float = 0.0
    last_trade_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Bot Creation Model
class BotCreate(BotBase):
    pass


# Bot Update Model
class BotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    strategy: Optional[str] = Field(None, min_length=1, max_length=255)
    max_open_trades: Optional[int] = Field(None, ge=1, le=10)
    stake_amount: Optional[float] = Field(None, gt=0)
    stop_loss: Optional[float] = Field(None, ge=0, le=100)
    take_profit: Optional[float] = Field(None, ge=0, le=1000)
    risk_percentage: Optional[float] = Field(None, ge=0.1, le=100.0)
    is_paper_trade: Optional[bool] = None


# Bot Statistics
class BotStatistics(BaseModel):
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_profit: float = 0.0
    total_profit_percentage: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    avg_trade: float = 0.0
    avg_holding_time: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0


# Bot Performance Summary
class BotPerformance(BaseModel):
    bot_id: str
    bot_name: str
    total_return: float
    total_return_percentage: float
    total_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    last_updated: datetime


# Bot Control Actions
class BotAction(BaseModel):
    action: str = Field(..., regex="^(start|stop|pause|resume|reset)$")


# Bot Configuration
class BotConfig(BaseModel):
    exchange_config: Dict[str, Any]
    strategy_params: Dict[str, Any]
    risk_management: Dict[str, Any]
    notification_settings: Dict[str, bool] = Field(default_factory=lambda: {
        "trade_executed": True,
        "stop_loss_triggered": True,
        "take_profit_reached": True,
        "bot_error": True,
        "daily_summary": True
    })


# Bot List Response
class BotListResponse(BaseModel):
    bots: List[BotResponse]
    total: int
    stats: BotStatistics


# Bot Analytics
class BotAnalytics(BaseModel):
    bot_id: str
    period: str  # daily, weekly, monthly
    trades_count: int
    profit_loss: float
    profit_percentage: float
    win_rate: float
    best_trade: float
    worst_trade: float
    avg_trade_duration: float
    trades: List[Dict[str, Any]]
