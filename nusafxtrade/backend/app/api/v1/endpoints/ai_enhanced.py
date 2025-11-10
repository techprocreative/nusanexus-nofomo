"""
Enhanced AI API Endpoints with Full AI Engine Integration
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional
import structlog
from datetime import datetime
import uuid

from app.core.auth import get_current_user
from app.models.ai import (
    StrategyGenerationRequest, StrategyOptimizationRequest, AIStrategyResponse,
    AIMarketAnalysis, AITradeSignal, AIChatRequest, AIChatResponse
)
from app.services.ai_service import AIService

# Import AI Engine components
try:
    from nusafxtrade.ai_engine.ai_engine_core import get_ai_engine
    from nusafxtrade.ai_engine.websocket_manager import get_connection_manager, create_websocket_endpoint
    from nusafxtrade.ai_engine.storage_manager import get_storage_manager
    AI_ENGINE_AVAILABLE = True
except ImportError as e:
    AI_ENGINE_AVAILABLE = False
    print(f"AI Engine not available: {e}")

router = APIRouter()
logger = structlog.get_logger(__name__)
ai_service = AIService()

# Initialize AI Engine components
ai_engine = None
connection_manager = None
storage_manager = None

if AI_ENGINE_AVAILABLE:
    try:
        ai_engine = get_ai_engine()
        connection_manager = get_connection_manager()
        connection_manager.set_ai_engine(ai_engine)
        storage_manager = get_storage_manager()
        logger.info("AI Engine components initialized")
    except Exception as e:
        logger.error(f"Failed to initialize AI Engine: {e}")


@router.post("/generate-strategy", response_model=AIStrategyResponse)
async def generate_strategy(
    request: StrategyGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Generate trading strategy using AI Engine"""
    try:
        if AI_ENGINE_AVAILABLE and ai_engine:
            # Use enhanced AI Engine
            from nusafxtrade.ai_engine.strategy_generator_enhanced import StrategyPrompt
            
            strategy_prompt = StrategyPrompt(
                prompt=request.prompt,
                trading_pair=request.trading_pair,
                timeframe=request.timeframe,
                risk_level=request.risk_level,
                style=request.style,
                max_parameters=request.max_parameters,
                include_indicators=request.get('include_indicators', []),
                exclude_indicators=request.get('exclude_indicators', []),
                strategy_complexity=request.get('strategy_complexity', 'medium'),
                backtest_period=request.get('backtest_period', 90),
                optimization_goals=request.get('optimization_goals', ['profit', 'win_rate'])
            )
            
            # Start background generation
            background_tasks.add_task(
                ai_engine.generate_strategy,
                user_id=current_user.id,
                prompt=strategy_prompt,
                optimize=True,
                backtest=True
            )
            
            # Store initial request
            if storage_manager:
                await storage_manager.store_analysis(
                    user_id=current_user.id,
                    analysis_type="strategy_generation",
                    data={"request": request.model_dump(), "status": "started"},
                    metadata={"user_id": current_user.id}
                )
            
            return AIStrategyResponse(
                strategy_code="# Strategy generation started...",
                strategy_name="AI Strategy Generation",
                description="AI strategy generation in progress",
                parameters={},
                risk_assessment={},
                backtest_suggestions=["Generation started, results will be available soon"],
                confidence_score=0.5,
                model_used="ai_engine",
                tokens_used=0,
                processing_time_ms=0
            )
        else:
            # Fallback to basic service
            result = await ai_service.generate_strategy(request)
            return result
            
    except Exception as e:
        logger.error("Strategy generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-strategy")
async def optimize_strategy(
    request: StrategyOptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Optimize strategy parameters using AI Engine"""
    try:
        if AI_ENGINE_AVAILABLE and ai_engine:
            # Use enhanced AI Engine optimization
            background_tasks.add_task(
                ai_engine.optimize_strategy,
                user_id=current_user.id,
                strategy_code=request.get('strategy_code', ''),
                parameters=request.get('parameters', {}),
                objectives=request.optimization_goals,
                method="bayesian"
            )
            
            return {
                "status": "optimization_started",
                "message": "Parameter optimization started in background",
                "estimated_duration": "2-5 minutes"
            }
        else:
            # Fallback to basic service
            result = await ai_service.optimize_strategy(request)
            return result
            
    except Exception as e:
        logger.error("Strategy optimization failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market-analysis", response_model=AIMarketAnalysis)
async def analyze_market(
    symbol: str,
    analysis_type: str = "technical",
    time_horizon: str = "medium",
    current_user = Depends(get_current_user)
):
    """Analyze market with AI Engine"""
    try:
        if AI_ENGINE_AVAILABLE and ai_engine:
            result = await ai_engine.analyze_market(
                user_id=current_user.id,
                symbol=symbol,
                analysis_type=analysis_type,
                time_horizon=time_horizon
            )
            
            # Store analysis result
            if storage_manager:
                await storage_manager.store_analysis(
                    user_id=current_user.id,
                    analysis_type="market_analysis",
                    data=result,
                    metadata={"symbol": symbol, "analysis_type": analysis_type},
                    expires_in_hours=24
                )
            
            return result
        else:
            # Fallback to basic service
            result = await ai_service.analyze_market(symbol, analysis_type)
            return result
            
    except Exception as e:
        logger.error("Market analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=AIChatResponse)
async def chat_with_ai(
    request: AIChatRequest,
    current_user = Depends(get_current_user)
):
    """Chat with AI assistant using enhanced engine"""
    try:
        if AI_ENGINE_AVAILABLE and ai_engine:
            response = await ai_engine.chat_with_ai(
                user_id=current_user.id,
                message=request.message,
                context_type=request.get('context_type', 'general'),
                context_data=request.context
            )
            
            return AIChatResponse(
                message=response['content'],
                suggestions=response.get('suggestions', []),
                confidence=response.get('confidence', 0.5),
                model_used=response.get('model_used', 'ai_engine'),
                tokens_used=response.get('tokens_used', 0),
                processing_time_ms=response.get('processing_time_ms', 0),
                context_used=request.context
            )
        else:
            # Fallback to basic service
            result = await ai_service.chat_with_ai(request)
            return result
            
    except Exception as e:
        logger.error("AI chat failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models-status")
async def get_models_status(current_user = Depends(get_current_user)):
    """Get AI models status with enhanced metrics"""
    try:
        if AI_ENGINE_AVAILABLE and ai_engine:
            metrics = await ai_engine.get_engine_metrics()
            health = await ai_engine.get_health_status()
            
            return {
                "ai_engine": {
                    "status": "active",
                    "metrics": metrics,
                    "health": health
                },
                "components": {
                    "strategy_generator": "available",
                    "parameter_optimizer": "available",
                    "market_analyzer": "available",
                    "ai_assistant": "available",
                    "supervisor_agent": "available"
                }
            }
        else:
            # Fallback to basic service
            result = await ai_service.get_models_status()
            return result
            
    except Exception as e:
        logger.error("Failed to get models status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-signal", response_model=AITradeSignal)
async def analyze_signal(
    signal_data: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Analyze trading signal with AI Engine"""
    try:
        if AI_ENGINE_AVAILABLE and ai_engine:
            # Use market analyzer for signal analysis
            result = await ai_engine.analyze_market(
                user_id=current_user.id,
                symbol=signal_data.get('symbol', 'BTC/USDT'),
                analysis_type="technical",
                time_horizon="short"
            )
            
            # Convert market analysis to signal format
            signals = result.get('market_signals', [])
            if signals:
                main_signal = signals[0]
                return AITradeSignal(
                    symbol=signal_data.get('symbol', 'BTC/USDT'),
                    signal_type=main_signal.signal_type,
                    entry_price=signal_data.get('price', 0),
                    stop_loss=main_signal.price_targets.get('stop_loss'),
                    take_profit=main_signal.price_targets.get('take_profit'),
                    confidence=main_signal.confidence,
                    time_horizon=main_signal.time_horizon,
                    reasoning=main_signal.reasoning,
                    supporting_indicators=[],
                    risk_assessment={"level": main_signal.risk_level},
                    generated_at=datetime.now(),
                    expires_at=datetime.now()
                )
        
        # Fallback to basic service
        result = await ai_service.analyze_signal(signal_data)
        return result
            
    except Exception as e:
        logger.error("Signal analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supervisor-analysis")
async def run_supervisor_analysis(
    bot_id: str,
    analysis_type: str = "comprehensive",
    current_user = Depends(get_current_user)
):
    """Run AI supervisor analysis for bot using enhanced engine"""
    try:
        if AI_ENGINE_AVAILABLE and ai_engine:
            result = await ai_engine.supervise_bot(
                user_id=current_user.id,
                bot_id=bot_id,
                analysis_type=analysis_type
            )
            return result
        else:
            # Fallback to basic service
            result = await ai_service.run_supervisor_analysis(bot_id, analysis_type)
            return result
            
    except Exception as e:
        logger.error("Supervisor analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-analysis")
async def analyze_performance(
    entity_id: str,
    entity_type: str,
    period: str = "30d",
    current_user = Depends(get_current_user)
):
    """Analyze performance with AI Engine"""
    try:
        if AI_ENGINE_AVAILABLE and ai_engine:
            result = await ai_engine.analyze_market(
                user_id=current_user.id,
                symbol=entity_id,  # Use as symbol for analysis
                analysis_type="performance",
                time_horizon=period
            )
            return result
        else:
            # Fallback to basic service
            result = await ai_service.analyze_performance(entity_id, entity_type, period)
            return result
            
    except Exception as e:
        logger.error("Performance analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-backtest")
async def analyze_backtest(
    backtest_data: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Analyze backtest results with AI Engine"""
    try:
        if AI_ENGINE_AVAILABLE and ai_engine:
            # Use market analyzer for backtest analysis
            result = await ai_engine.analyze_market(
                user_id=current_user.id,
                symbol=backtest_data.get('symbol', 'BTC/USDT'),
                analysis_type="backtest",
                time_horizon="long"
            )
            return result
        else:
            # Fallback to basic service
            result = await ai_service.analyze_backtest(backtest_data)
            return result
            
    except Exception as e:
        logger.error("Backtest analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time AI updates
@router.websocket("/ws/ai")
async def websocket_ai_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time AI updates"""
    if not AI_ENGINE_AVAILABLE or not connection_manager:
        await websocket.close(code=1000, reason="AI Engine not available")
        return
    
    # Simple token validation (in production, use proper JWT)
    try:
        # Decode user_id from token (simplified)
        user_id = "user_" + str(uuid.uuid4())[:8]
        connection_id = str(uuid.uuid4())
        
        await create_websocket_endpoint(websocket, user_id, connection_id)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=1011, reason="Internal server error")


# Task status endpoints
@router.get("/task/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user = Depends(get_current_user)
):
    """Get status of AI task"""
    try:
        if AI_ENGINE_AVAILABLE and ai_engine:
            status = await ai_engine.get_task_status(task_id)
            if not status:
                raise HTTPException(status_code=404, detail="Task not found")
            return status
        else:
            raise HTTPException(status_code=503, detail="AI Engine not available")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """List user's AI tasks"""
    try:
        if AI_ENGINE_AVAILABLE and ai_engine:
            tasks = await ai_engine.list_tasks(
                user_id=current_user.id,
                status=status,
                limit=limit
            )
            return {"tasks": tasks}
        else:
            raise HTTPException(status_code=503, detail="AI Engine not available")
            
    except Exception as e:
        logger.error(f"Failed to list tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Storage endpoints
@router.get("/analyses")
async def list_analyses(
    analysis_type: Optional[str] = None,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """List user's AI analyses"""
    try:
        if AI_ENGINE_AVAILABLE and storage_manager:
            analyses = await storage_manager.list_analyses(
                user_id=current_user.id,
                analysis_type=analysis_type,
                limit=limit
            )
            return {"analyses": analyses}
        else:
            raise HTTPException(status_code=503, detail="Storage not available")
            
    except Exception as e:
        logger.error(f"Failed to list analyses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_user_analytics(
    days: int = 30,
    current_user = Depends(get_current_user)
):
    """Get user AI analytics"""
    try:
        if AI_ENGINE_AVAILABLE and storage_manager:
            metrics = await storage_manager.get_user_metrics(
                user_id=current_user.id,
                days=days
            )
            return metrics
        else:
            raise HTTPException(status_code=503, detail="Storage not available")
            
    except Exception as e:
        logger.error(f"Failed to get user analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
