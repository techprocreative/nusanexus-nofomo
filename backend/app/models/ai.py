"""
AI Pydantic models for NusaNexus NoFOMO
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from .common import AnalysisType, RiskLevel, SideType, StrategyType, TimeFrame


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

# AI Analysis Base Model
class AIAnalysisBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    analysis_type: AnalysisType
    input_data: Dict[str, Any]
    results: Dict[str, Any]
    recommendations: List[str] = Field(default_factory=list)
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    model_used: Optional[str] = None
    tokens_used: int = 0
    processing_time_ms: Optional[int] = None


# AI Analysis Response Model
class AIAnalysisResponse(AIAnalysisBase):
    id: str
    user_id: str
    bot_id: Optional[str] = None
    strategy_id: Optional[str] = None
    created_at: datetime


# Strategy Generation Request
class StrategyGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=2000)
    trading_pair: str = Field(..., min_length=3, max_length=20)
    timeframe: TimeFrame
    risk_level: RiskLevel = RiskLevel.MEDIUM
    strategy_type: StrategyType = StrategyType.AI_GENERATED
    style: str = Field("conservative", regex="^(conservative|balanced|aggressive)$")
    max_parameters: int = Field(10, ge=1, le=50)
    include_stop_loss: bool = True
    include_take_profit: bool = True


# Strategy Optimization Request
class StrategyOptimizationRequest(BaseModel):
    strategy_id: str
    trading_pair: str
    timeframe: TimeFrame
    optimization_goals: List[str] = Field(default_factory=lambda: ["profit", "win_rate", "drawdown"])
    parameter_constraints: Optional[Dict[str, Any]] = None
    max_iterations: int = Field(100, ge=10, le=1000)
    sample_size: int = Field(1000, ge=100, le=10000)


# AI Model Configuration
class AIModelConfig(BaseModel):
    model_name: str = "anthropic/claude-3-sonnet"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(4000, ge=100, le=8000)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(0.0, ge=0.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=0.0, le=2.0)


# AI Strategy Response
class AIStrategyResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    strategy_code: str
    strategy_name: str
    description: str
    parameters: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    backtest_suggestions: List[str]
    confidence_score: float
    model_used: str
    tokens_used: int
    processing_time_ms: int


# AI Performance Analysis
class AIPerformanceAnalysis(BaseModel):
    entity_id: str  # bot_id or strategy_id
    entity_type: str  # "bot" or "strategy"
    analysis_period: str  # "7d", "30d", "90d", "1y"
    performance_metrics: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    recommendations: List[str]
    confidence_score: float
    next_analysis_date: datetime


# AI Market Analysis
class AIMarketAnalysis(BaseModel):
    symbol: str
    analysis_type: str  # "sentiment", "technical", "fundamental"
    indicators: Dict[str, Any]
    signals: Dict[str, Any]
    predictions: Dict[str, Any]
    confidence_level: float
    time_horizon: str
    market_conditions: Dict[str, Any]
    key_levels: Dict[str, Any]
    risk_factors: List[str]


# AI Trade Signal
class AITradeSignal(BaseModel):
    symbol: str
    signal_type: SideType
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: float
    time_horizon: str
    reasoning: str
    supporting_indicators: List[str]
    risk_assessment: Dict[str, Any]
    generated_at: datetime
    expires_at: datetime


# AI Chat Request
class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = None
    model_config: Optional[AIModelConfig] = None
    include_chart_data: bool = False


# AI Chat Response
class AIChatResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    message: str
    suggestions: List[str] = Field(default_factory=list)
    confidence: float
    model_used: str
    tokens_used: int
    processing_time_ms: int
    context_used: Optional[Dict[str, Any]] = None


# AI Analysis Queue
class AIAnalysisQueue(BaseModel):
    user_id: str
    job_type: str  # "strategy_generation", "optimization", "analysis"
    priority: int = Field(1, ge=1, le=10)
    payload: Dict[str, Any]
    estimated_duration: int  # seconds
    created_at: datetime = Field(default_factory=_utcnow)


# AI Model Status
class AIModelStatus(BaseModel):
    model_name: str
    status: str  # "active", "busy", "maintenance", "error"
    avg_response_time: float
    success_rate: float
    total_requests: int
    daily_requests: int
    queue_length: int
    last_health_check: datetime
