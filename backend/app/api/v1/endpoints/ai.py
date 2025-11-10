"""
AI strategy generation endpoints for NusaNexus NoFOMO
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from app.core.auth import get_current_user
from app.core.database import get_db_client
from app.services.ai_service import get_ai_service
from app.models.ai import (
    AIAnalysisResponse, StrategyGenerationRequest, StrategyOptimizationRequest,
    AIStrategyResponse, AIPerformanceAnalysis, AIMarketAnalysis,
    AITradeSignal, AIChatRequest, AIChatResponse
)
from app.models.common import APIResponse
from app.models.user import UserResponse

logger = structlog.get_logger()
router = APIRouter()


@router.post("/generate-strategy", response_model=AIStrategyResponse)
async def generate_strategy(
    request: StrategyGenerationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate trading strategy using AI
    """
    try:
        ai_service = get_ai_service()
        
        # Generate strategy with AI
        response = await ai_service.generate_strategy(request)
        
        return response
        
    except Exception as e:
        logger.error("AI strategy generation failed", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate strategy with AI"
        )


@router.post("/optimize-strategy", response_model=APIResponse)
async def optimize_strategy(
    request: StrategyOptimizationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Optimize strategy parameters using AI
    """
    try:
        ai_service = get_ai_service()
        
        # Verify strategy belongs to user
        db_client = get_db_client()
        strategy = db_client.get_strategy_by_id(request.strategy_id)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
        
        if strategy.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Run optimization
        optimization_result = await ai_service.optimize_strategy(request)
        
        return APIResponse(
            success=True,
            message="Strategy optimization completed",
            data=optimization_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("AI strategy optimization failed", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize strategy with AI"
        )


@router.get("/supervisor/{bot_id}", response_model=List[AIAnalysisResponse])
async def get_supervisor_analysis(
    bot_id: str,
    analysis_type: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get AI supervisor analysis for bot
    """
    try:
        db_client = get_db_client()
        
        # Verify bot belongs to user
        bot = db_client.get_bot_by_id(bot_id, current_user.id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Get AI analyses for the bot
        # This would need to be implemented in the database client
        analyses = []
        
        # Filter by analysis type if specified
        if analysis_type:
            analyses = [a for a in analyses if a.get("analysis_type") == analysis_type]
        
        return [AIAnalysisResponse(**analysis) for analysis in analyses]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get supervisor analysis", bot_id=bot_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch supervisor analysis"
        )


@router.post("/supervisor/analyze", response_model=APIResponse)
async def run_supervisor_analysis(
    bot_id: str,
    analysis_type: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Run AI supervisor analysis for bot
    """
    try:
        ai_service = get_ai_service()
        db_client = get_db_client()
        
        # Verify bot belongs to user
        bot = db_client.get_bot_by_id(bot_id, current_user.id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Run AI analysis
        analysis = await ai_service.run_supervisor_analysis(bot_id, analysis_type)
        
        # Save analysis to database
        analysis_data = {
            "user_id": current_user.id,
            "bot_id": bot_id,
            "analysis_type": analysis_type,
            "input_data": {"bot_id": bot_id},
            "results": analysis,
            "recommendations": analysis.get("recommendations", []),
            "confidence_score": analysis.get("confidence_score", 0.0),
            "model_used": "supervisor",
            "processing_time_ms": analysis.get("processing_time_ms", 0),
            "created_at": datetime.utcnow().isoformat()
        }
        
        created_analysis = db_client.create_ai_analysis(analysis_data)
        
        return APIResponse(
            success=True,
            message="Supervisor analysis completed",
            data=created_analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Supervisor analysis failed", bot_id=bot_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run supervisor analysis"
        )


@router.get("/market-analysis", response_model=AIMarketAnalysis)
async def get_market_analysis(
    symbol: str,
    analysis_type: str = "comprehensive"
):
    """
    Get AI-powered market analysis
    """
    try:
        ai_service = get_ai_service()
        
        # Get market analysis
        analysis = await ai_service.analyze_market(symbol, analysis_type)
        
        return analysis
        
    except Exception as e:
        logger.error("Market analysis failed", symbol=symbol, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze market"
        )


@router.post("/signal-analysis", response_model=AITradeSignal)
async def analyze_signal(
    signal_data: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Analyze trading signal with AI
    """
    try:
        ai_service = get_ai_service()
        
        # Validate required signal data
        required_fields = ["symbol", "signal_type", "price", "timeframe"]
        for field in required_fields:
            if field not in signal_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Analyze signal
        analysis = await ai_service.analyze_signal(signal_data)
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Signal analysis failed", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze signal"
        )


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    request: AIChatRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    AI chat assistant for trading questions
    """
    try:
        ai_service = get_ai_service()
        
        # Get chat response
        response = await ai_service.chat_with_ai(request)
        
        return response
        
    except Exception as e:
        logger.error("AI chat failed", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI response"
        )


@router.get("/performance-analysis/{entity_id}", response_model=AIPerformanceAnalysis)
async def get_performance_analysis(
    entity_id: str,
    entity_type: str,  # "bot" or "strategy"
    analysis_period: str = "30d",
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get AI-powered performance analysis
    """
    try:
        ai_service = get_ai_service()
        
        # Verify entity belongs to user based on type
        db_client = get_db_client()
        
        if entity_type == "bot":
            entity = db_client.get_bot_by_id(entity_id, current_user.id)
        elif entity_type == "strategy":
            entity = db_client.get_strategy_by_id(entity_id)
            if not entity or entity.get("user_id") != current_user.id:
                entity = None
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid entity type. Must be 'bot' or 'strategy'"
            )
        
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_type.capitalize()} not found"
            )
        
        # Run performance analysis
        analysis = await ai_service.analyze_performance(entity_id, entity_type, analysis_period)
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Performance analysis failed", entity_id=entity_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze performance"
        )


@router.get("/models/status")
async def get_ai_models_status():
    """
    Get status of AI models and services
    """
    try:
        ai_service = get_ai_service()
        
        # Get model status
        status = await ai_service.get_models_status()
        
        return status
        
    except Exception as e:
        logger.error("Failed to get AI models status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch AI models status"
        )


@router.post("/backtest-analysis", response_model=APIResponse)
async def analyze_backtest(
    backtest_data: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Analyze backtest results with AI
    """
    try:
        ai_service = get_ai_service()
        
        # Validate backtest data
        required_fields = ["strategy_name", "trading_pair", "results"]
        for field in required_fields:
            if field not in backtest_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Analyze backtest results
        analysis = await ai_service.analyze_backtest(backtest_data)
        
        return APIResponse(
            success=True,
            message="Backtest analysis completed",
            data=analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Backtest analysis failed", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze backtest results"
        )


@router.get("/usage-stats")
async def get_ai_usage_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get AI usage statistics for current user
    """
    try:
        # Get user's AI analyses
        # This would need to be implemented in the database client
        analyses = []
        
        # Calculate usage statistics
        total_requests = len(analyses)
        total_tokens = sum(a.get("tokens_used", 0) for a in analyses)
        successful_requests = len([a for a in analyses if a.get("confidence_score", 0) > 0.7])
        
        return {
            "user_id": current_user.id,
            "total_requests": total_requests,
            "total_tokens_used": total_tokens,
            "successful_requests": successful_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0.0,
            "analysis_types": list(set(a.get("analysis_type", "unknown") for a in analyses)),
            "last_usage": analyses[0].get("created_at") if analyses else None
        }
        
    except Exception as e:
        logger.error("Failed to get AI usage stats", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch AI usage statistics"
        )
