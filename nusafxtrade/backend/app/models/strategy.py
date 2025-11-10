"""
Strategy Pydantic models for NusaNexus NoFOMO
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from .common import RiskLevel, StrategyType


# Base Strategy Model
class StrategyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    strategy_type: StrategyType
    content: Optional[str] = None  # Python strategy code
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False
    is_verified: bool = False
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM


# Strategy Response Model
class StrategyResponse(StrategyBase):
    id: str
    user_id: str
    performance: Dict[str, Any] = Field(default_factory=dict)
    backtest_results: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


# Strategy Creation Model
class StrategyCreate(StrategyBase):
    pass


# Strategy Update Model
class StrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    risk_level: Optional[RiskLevel] = None


# Strategy Marketplace Item
class StrategyMarketplaceItem(BaseModel):
    id: str
    name: str
    description: str
    strategy_type: StrategyType
    risk_level: RiskLevel
    category: str
    tags: List[str]
    performance: Dict[str, Any]
    user_count: int
    rating: float
    is_verified: bool
    created_at: datetime


# Strategy Performance
class StrategyPerformance(BaseModel):
    strategy_id: str
    total_returns: float
    total_returns_percentage: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: float
    backtest_count: int
    last_tested: Optional[datetime] = None


# Strategy Validation
class StrategyValidation(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    syntax_check: bool = True
    dependency_check: bool = True
    config_validation: bool = True


# Strategy Code Upload
class StrategyFileUpload(BaseModel):
    filename: str
    content: str
    strategy_type: StrategyType
    validate_only: bool = False


# Strategy Parameters
class StrategyParameters(BaseModel):
    parameters: Dict[str, Any]
    constraints: Optional[Dict[str, Any]] = None
    default_values: Optional[Dict[str, Any]] = None


# Strategy Search
class StrategySearch(BaseModel):
    query: Optional[str] = None
    strategy_type: Optional[StrategyType] = None
    risk_level: Optional[RiskLevel] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_verified: Optional[bool] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


# Strategy List Response
class StrategyListResponse(BaseModel):
    strategies: List[StrategyResponse]
    total: int
    performance_summary: StrategyPerformance


# Strategy Analysis
class StrategyAnalysis(BaseModel):
    strategy_id: str
    analysis_type: str  # performance, risk, optimization
    results: Dict[str, Any]
    recommendations: List[str]
    confidence_score: float
    created_at: datetime


# Strategy Comparison
class StrategyComparison(BaseModel):
    strategies: List[Dict[str, Any]]
    comparison_metrics: List[str]
    results: Dict[str, Any]
    best_performers: List[str]
    risk_assessment: Dict[str, Any]
