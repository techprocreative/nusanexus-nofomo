"""
Backtest Pydantic models for NusaNexus NoFOMO
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from .common import SideType, TimeFrame


# Backtest Configuration
class BacktestConfig(BaseModel):
    trading_pair: str
    timeframe: TimeFrame
    start_date: datetime
    end_date: datetime
    initial_balance: float = Field(..., gt=0)
    commission: float = Field(0.001, ge=0.0, le=0.1)  # 0.1% default
    slippage: float = Field(0.001, ge=0.0, le=0.1)  # 0.1% default
    stake_amount: float = Field(..., gt=0)
    max_open_trades: int = Field(1, ge=1, le=10)
    stop_loss: Optional[float] = Field(None, ge=0, le=100)
    take_profit: Optional[float] = Field(None, ge=0, le=1000)
    enable_stop_loss: bool = True
    enable_take_profit: bool = True
    strategy_config: Optional[Dict[str, Any]] = None


# Backtest Result Response
class BacktestResultResponse(BaseModel):
    id: str
    strategy_id: str
    user_id: str
    trading_pair: str
    timeframe: TimeFrame
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    total_return: float
    total_return_percentage: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    win_rate: float
    profit_factor: Optional[float] = None
    total_trades: int
    winning_trades: int
    losing_trades: int
    best_trade: float
    worst_trade: float
    avg_trade: Optional[float] = None
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    calmar_ratio: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


# Backtest Performance Metrics
class BacktestPerformance(BaseModel):
    returns: Dict[str, Any]  # daily, monthly, yearly returns
    drawdown: Dict[str, Any]  # max drawdown, average drawdown, etc.
    risk_metrics: Dict[str, Any]  # sharpe, sortino, calmar ratios
    trading_metrics: Dict[str, Any]  # win rate, profit factor, etc.
    time_metrics: Dict[str, Any]  # avg holding time, time in market, etc.
    exposure: Dict[str, Any]  # market exposure, diversification, etc.


# Backtest Trade Details
class BacktestTrade(BaseModel):
    trade_id: str
    entry_time: datetime
    exit_time: Optional[datetime]
    symbol: str
    side: SideType
    amount: float
    entry_price: float
    exit_price: Optional[float]
    profit: float
    profit_percentage: float
    fee: float
    hold_time: Optional[float]  # in hours
    trade_number: int
    balance_after: float


# Backtest Chart Data
class BacktestChartData(BaseModel):
    timestamps: List[datetime]
    equity: List[float]
    balance: List[float]
    profit_loss: List[float]
    drawdown: List[float]
    trades: List[Dict[str, Any]]
    signals: Optional[List[Dict[str, Any]]] = None


# Backtest Comparison
class BacktestComparison(BaseModel):
    baseline_result_id: str
    comparison_result_id: str
    metric_comparison: Dict[str, Any]
    performance_difference: Dict[str, Any]
    risk_difference: Dict[str, Any]
    trading_difference: Dict[str, Any]
    conclusion: str
    recommendation: str


# Backtest Optimization Request
class BacktestOptimizationRequest(BaseModel):
    strategy_id: str
    trading_pair: str
    timeframe: TimeFrame
    parameter_ranges: Dict[str, Any]  # {"param1": [min, max], "param2": [min, max]}
    optimization_metric: str = Field("total_return", regex="^(total_return|sharpe_ratio|win_rate|profit_factor)$")
    max_iterations: int = Field(100, ge=10, le=1000)
    parallelism: int = Field(1, ge=1, le=8)


# Backtest Optimization Result
class BacktestOptimizationResult(BaseModel):
    optimization_id: str
    strategy_id: str
    best_parameters: Dict[str, Any]
    best_score: float
    optimization_results: List[Dict[str, Any]]
    convergence_data: Dict[str, Any]
    confidence_interval: Optional[Dict[str, float]] = None
    created_at: datetime


# Backtest Report
class BacktestReport(BaseModel):
    result_id: str
    strategy_name: str
    period: str
    executive_summary: str
    performance_summary: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    detailed_analysis: Dict[str, Any]
    charts: List[Dict[str, Any]]  # Chart configurations
    recommendations: List[str]
    conclusion: str
