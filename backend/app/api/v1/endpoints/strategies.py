"""
Strategy management endpoints for NusaNexus NoFOMO
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import ast
import structlog

from app.core.auth import get_current_user
from app.core.database import get_db_client
from app.models.strategy import (
    StrategyResponse, StrategyCreate, StrategyListResponse,
    StrategyMarketplaceItem, StrategyPerformance
)
from app.models.user import UserResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=StrategyListResponse)
async def get_strategies(
    page: int = 1,
    limit: int = 20,
    strategy_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all strategies for current user with pagination and filtering
    """
    try:
        db_client = get_db_client()
        
        # Get user strategies
        strategies = db_client.get_user_strategies(current_user.id)
        
        # Apply filters
        if strategy_type:
            strategies = [s for s in strategies if s.get("strategy_type") == strategy_type]
        if is_public is not None:
            strategies = [s for s in strategies if s.get("is_public") == is_public]
        
        # Calculate pagination
        total = len(strategies)
        start = (page - 1) * limit
        end = start + limit
        paginated_strategies = strategies[start:end]
        
        # Convert to response models
        strategy_responses = [StrategyResponse(**strategy) for strategy in paginated_strategies]
        
        # Calculate performance summary
        total_strategies = len(strategies)
        avg_performance = {
            "strategy_id": "summary",
            "total_returns": sum(s.get("performance", {}).get("total_return", 0) for s in strategies) / max(total_strategies, 1),
            "total_returns_percentage": sum(s.get("performance", {}).get("total_return_percentage", 0) for s in strategies) / max(total_strategies, 1),
            "sharpe_ratio": sum(s.get("performance", {}).get("sharpe_ratio", 0) for s in strategies) / max(total_strategies, 1),
            "max_drawdown": sum(s.get("performance", {}).get("max_drawdown", 0) for s in strategies) / max(total_strategies, 1),
            "win_rate": sum(s.get("performance", {}).get("win_rate", 0) for s in strategies) / max(total_strategies, 1),
            "profit_factor": sum(s.get("performance", {}).get("profit_factor", 0) for s in strategies) / max(total_strategies, 1),
            "total_trades": sum(s.get("performance", {}).get("total_trades", 0) for s in strategies),
            "avg_trade_duration": sum(s.get("performance", {}).get("avg_trade_duration", 0) for s in strategies) / max(total_strategies, 1),
            "backtest_count": sum(s.get("backtest_results", {}).get("total_trades", 0) for s in strategies),
            "last_tested": None
        }
        
        response = StrategyListResponse(
            strategies=strategy_responses,
            total=total,
            performance_summary=StrategyPerformance(**avg_performance)
        )
        
        return response
        
    except Exception as e:
        logger.error("Failed to get strategies", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch strategies"
        )


@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create new strategy
    """
    try:
        db_client = get_db_client()
        
        # Validate strategy code if provided
        if strategy_data.content:
            validation = _validate_strategy_code(strategy_data.content)
            if not validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid strategy code: {', '.join(validation['errors'])}"
                )
        
        # Prepare strategy data
        strategy_record = {
            "user_id": current_user.id,
            "name": strategy_data.name,
            "description": strategy_data.description,
            "strategy_type": strategy_data.strategy_type,
            "content": strategy_data.content,
            "parameters": strategy_data.parameters or {},
            "performance": {},
            "is_public": strategy_data.is_public,
            "is_verified": False,
            "tags": strategy_data.tags or [],
            "category": strategy_data.category,
            "risk_level": strategy_data.risk_level,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Create strategy in database
        created_strategy = db_client.create_strategy(strategy_record)
        
        if not created_strategy:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create strategy"
            )
        
        logger.info("Strategy created", strategy_id=created_strategy["id"], user_id=current_user.id)
        
        return StrategyResponse(**created_strategy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create strategy", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create strategy"
        )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get specific strategy
    """
    try:
        db_client = get_db_client()
        
        # Get strategy
        strategy = db_client.get_strategy_by_id(strategy_id)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
        
        # Check if user can access this strategy
        if strategy.get("user_id") != current_user.id and not strategy.get("is_public"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return StrategyResponse(**strategy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get strategy", strategy_id=strategy_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch strategy"
        )


@router.get("/marketplace/", response_model=List[StrategyMarketplaceItem])
async def get_marketplace_strategies(
    page: int = 1,
    limit: int = 20,
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    sort_by: str = "created_at"
):
    """
    Get public marketplace strategies
    """
    try:
        db_client = get_db_client()
        
        # Get marketplace strategies
        strategies = db_client.get_marketplace_strategies()
        
        # Apply filters
        if category:
            strategies = [s for s in strategies if s.get("category") == category]
        if risk_level:
            strategies = [s for s in strategies if s.get("risk_level") == risk_level]
        
        # Sort strategies
        reverse = sort_by.startswith('-')
        sort_field = sort_by.lstrip('-')
        strategies.sort(key=lambda x: x.get(sort_field, 0), reverse=reverse)
        
        # Calculate pagination
        start = (page - 1) * limit
        end = start + limit
        paginated_strategies = strategies[start:end]
        
        # Convert to marketplace items
        marketplace_items = [
            StrategyMarketplaceItem(
                id=strategy["id"],
                name=strategy["name"],
                description=strategy["description"],
                strategy_type=strategy["strategy_type"],
                risk_level=strategy["risk_level"],
                category=strategy["category"],
                tags=strategy.get("tags", []),
                performance=strategy.get("performance", {}),
                user_count=1,  # Placeholder
                rating=4.5,  # Placeholder
                is_verified=strategy.get("is_verified", False),
                created_at=strategy["created_at"]
            )
            for strategy in paginated_strategies
        ]
        
        return marketplace_items
        
    except Exception as e:
        logger.error("Failed to get marketplace strategies", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch marketplace strategies"
        )


# Helper functions
def _validate_strategy_code(code: str) -> Dict[str, Any]:
    """
    Validate strategy code for syntax and structure
    """
    errors = []
    warnings = []
    
    try:
        # Parse the code
        tree = ast.parse(code)
        
        # Check for required imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                else:
                    imports.append(node.module or "")
        
        if "freqtrade" not in str(imports):
            warnings.append("Consider importing from freqtrade.strategy")
        
        # Check for strategy class
        strategy_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if any(base.id == "IStrategy" for base in node.bases 
                       if isinstance(base, ast.Name) and base.id == "IStrategy"):
                    strategy_classes.append(node.name)
        
        if not strategy_classes:
            errors.append("No strategy class inheriting from IStrategy found")
        
        # Check for required methods
        required_methods = ["populate_indicators"]
        for strategy_class in strategy_classes:
            method_names = [n.name for n in strategy_class.body if isinstance(n, ast.FunctionDef)]
            
            for method in required_methods:
                if method not in method_names:
                    errors.append(f"Missing required method: {method}")
        
        # Check for indicators method
        for strategy_class in strategy_classes:
            method_names = [n.name for n in strategy_class.body if isinstance(n, ast.FunctionDef)]
            if "populate_indicators" not in method_names:
                warnings.append("Consider implementing populate_indicators method")
        
    except SyntaxError as e:
        errors.append(f"Syntax error: {e.msg}")
    except Exception as e:
        errors.append(f"Parse error: {str(e)}")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "syntax_check": len(errors) == 0,
        "dependency_check": len([e for e in errors if "import" in e]) == 0,
        "config_validation": True
    }
