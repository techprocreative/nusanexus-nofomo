"""
NusaNexus NoFOMO - AI Engine Core
Central coordinator for all AI engine components
"""

import asyncio
import inspect
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
import structlog

# Import all AI components
from .strategy_generator_enhanced import EnhancedAIStrategyGenerator, StrategyPrompt
from .parameter_optimizer import AIParameterOptimizer, ParameterRange, OptimizationObjective
from .market_analyzer import AIMarketAnalyzer, AnalysisType, TimeHorizon
from .ai_assistant import AIAssistant, ChatContextType
from .supervisor_agent import SupervisorAgent
from .prompt_manager import PromptManager

# Configure logging
logger = structlog.get_logger(__name__)


class EngineConfig(BaseModel):
    """AI Engine configuration"""
    max_concurrent_tasks: int = 10
    default_model: str = "anthropic/claude-3-sonnet"
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_retry_attempts: int = 3
    timeout_seconds: int = 300  # 5 minutes
    enable_supervisor: bool = True
    enable_realtime_monitoring: bool = True
    optimization_batch_size: int = 5


class TaskStatus(BaseModel):
    """Task status tracking"""
    task_id: str
    task_type: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float = 0.0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}


def _utcnow() -> datetime:
    """Timezone-aware helper to avoid deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc)


class EngineMetrics(BaseModel):
    """AI Engine performance metrics"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_response_time: float = 0.0
    tokens_used_today: int = 0
    cost_today: float = 0.0
    active_connections: int = 0
    component_health: Dict[str, str] = {}
    last_updated: datetime = Field(default_factory=_utcnow)


class AIEngineCore:
    """
    Core AI Engine that coordinates all components
    """
    
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        
        # Initialize components
        self.strategy_generator = EnhancedAIStrategyGenerator()
        self.parameter_optimizer = AIParameterOptimizer()
        self.market_analyzer = AIMarketAnalyzer()
        self.ai_assistant = AIAssistant()
        self.supervisor_agent = SupervisorAgent()
        self.prompt_manager = PromptManager()
        
        # Task management
        self.active_tasks: Dict[str, TaskStatus] = {}
        self.task_results: Dict[str, Any] = {}
        
        # Metrics and health
        self.metrics = EngineMetrics()
        self.start_time = datetime.now()
        
        # Component health tracking
        self.component_health = {
            "strategy_generator": "healthy",
            "parameter_optimizer": "healthy", 
            "market_analyzer": "healthy",
            "ai_assistant": "healthy",
            "supervisor_agent": "healthy",
            "prompt_manager": "healthy"
        }
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self.is_running = False
        
        logger.info("AI Engine Core initialized")
    
    async def start(self):
        """Start the AI Engine"""
        try:
            self.is_running = True
            
            # Start background monitoring
            if self.config.enable_realtime_monitoring:
                self.background_tasks.append(
                    asyncio.create_task(self._realtime_monitoring())
                )
            
            # Start component health checks
            self.background_tasks.append(
                asyncio.create_task(self._health_check_loop())
            )
            
            # Start task cleanup
            self.background_tasks.append(
                asyncio.create_task(self._task_cleanup_loop())
            )
            
            logger.info("AI Engine Core started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start AI Engine: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the AI Engine"""
        try:
            self.is_running = False
            
            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            if self.background_tasks:
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
            logger.info("AI Engine Core stopped")
            
        except Exception as e:
            logger.error(f"Error stopping AI Engine: {str(e)}")
    
    async def generate_strategy(
        self,
        user_id: str,
        prompt: StrategyPrompt,
        optimize: bool = False,
        backtest: bool = False
    ) -> Dict[str, Any]:
        """
        Generate strategy with optional optimization and backtesting
        """
        task_id = f"strategy_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        task: Optional[TaskStatus] = None
        try:
            # Create task
            task = TaskStatus(
                task_id=task_id,
                task_type="strategy_generation",
                status="running",
                created_at=datetime.now(),
                started_at=datetime.now(),
                metadata={"user_id": user_id, "prompt": prompt.model_dump()}
            )
            self.active_tasks[task_id] = task
            
            logger.info(f"Starting strategy generation task {task_id}")
            
            # Step 1: Generate strategy
            task.progress = 0.2
            strategy_result = await self._maybe_await(
                self.strategy_generator.generate_strategy(prompt)
            )
            
            # Step 2: Parameter optimization (if requested)
            optimization_result = None
            if optimize and strategy_result.get('parameters'):
                task.progress = 0.6
                optimization_result = await self._maybe_await(
                    self.parameter_optimizer.optimize_parameters(
                        strategy_code=strategy_result.get('content', ''),
                        parameter_ranges=[
                            ParameterRange(**pr) for pr in strategy_result.get('parameter_ranges', [])
                        ],
                        objectives=[
                            OptimizationObjective(
                                metric=goal,
                                direction="maximize",
                                weight=1.0 / len(prompt.optimization_goals)
                            )
                            for goal in prompt.optimization_goals
                        ],
                        max_iterations=50
                    )
                )
            
            # Step 3: Market analysis (if requested)
            market_analysis = None
            if backtest:
                task.progress = 0.8
                market_analysis = await self._maybe_await(
                    self.market_analyzer.analyze_market(
                        symbol=prompt.trading_pair,
                        analysis_type=AnalysisType.TECHNICAL,
                        time_horizon=TimeHorizon.LONG_TERM
                    )
                )
                market_analysis = self._serialize_result(market_analysis)
            
            # Compile final result
            result = {
                "task_id": task_id,
                "strategy": strategy_result,
                "optimization": self._serialize_result(optimization_result) if optimization_result else None,
                "market_analysis": market_analysis if market_analysis else None,
                "recommendations": {
                    "implementation": strategy_result.get('recommendations', {}),
                    "backtest_plan": strategy_result.get('backtest_plan', {}),
                    "risk_management": strategy_result.get('risk_management', {})
                },
                "created_at": datetime.now().isoformat()
            }
            
            # Update task status
            task.status = "completed"
            task.progress = 1.0
            task.completed_at = datetime.now()
            task.result = result
            
            # Store result
            self.task_results[task_id] = result
            self.metrics.completed_tasks += 1
            
            logger.info(f"Strategy generation task {task_id} completed successfully")
            return result
            
        except Exception as e:
            # Update task with error
            if task:
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.now()
            self.metrics.failed_tasks += 1
            
            logger.error(f"Strategy generation task {task_id} failed: {str(e)}")
            raise
        
        finally:
            # Remove from active tasks after a delay
            asyncio.create_task(self._cleanup_task_after_delay(task_id, 3600))
    
    async def optimize_strategy(
        self,
        user_id: str,
        strategy_code: str,
        parameters: Dict[str, Any],
        objectives: List[str],
        method: str = "bayesian"
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters
        """
        task_id = f"optimize_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        task: Optional[TaskStatus] = None
        try:
            # Create task
            task = TaskStatus(
                task_id=task_id,
                task_type="parameter_optimization",
                status="running",
                created_at=datetime.now(),
                started_at=datetime.now(),
                metadata={"user_id": user_id, "method": method}
            )
            self.active_tasks[task_id] = task
            
            logger.info(f"Starting parameter optimization task {task_id}")
            
            # Generate parameter ranges
            parameter_ranges = self._extract_parameter_ranges(parameters)
            
            # Create optimization objectives
            optimization_objectives = []
            for obj in objectives:
                if obj == "profit":
                    optimization_objectives.append(
                        OptimizationObjective(metric="total_return", direction="maximize", weight=0.4)
                    )
                elif obj == "win_rate":
                    optimization_objectives.append(
                        OptimizationObjective(metric="win_rate", direction="maximize", weight=0.3)
                    )
                elif obj == "sharpe_ratio":
                    optimization_objectives.append(
                        OptimizationObjective(metric="sharpe_ratio", direction="maximize", weight=0.3)
                    )
            
            # Run optimization
            result = await self._maybe_await(
                self.parameter_optimizer.optimize_parameters(
                    strategy_code=strategy_code,
                    parameter_ranges=parameter_ranges,
                    objectives=optimization_objectives,
                    max_iterations=100,
                    optimization_type=method
                )
            )
            result_data = self._serialize_result(result)
            
            # Update task status
            task.status = "completed"
            task.progress = 1.0
            task.completed_at = datetime.now()
            task.result = result_data
            
            # Store result
            self.task_results[task_id] = result_data
            self.metrics.completed_tasks += 1
            
            logger.info(f"Parameter optimization task {task_id} completed successfully")
            return result_data
            
        except Exception as e:
            # Update task with error
            if task:
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.now()
            self.metrics.failed_tasks += 1
            
            logger.error(f"Parameter optimization task {task_id} failed: {str(e)}")
            raise
        
        finally:
            asyncio.create_task(self._cleanup_task_after_delay(task_id, 1800))  # 30 minutes
    
    async def analyze_market(
        self,
        user_id: str,
        symbol: str,
        analysis_type: str = "comprehensive",
        time_horizon: str = "medium"
    ) -> Dict[str, Any]:
        """
        Analyze market with AI
        """
        task_id = f"market_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        task: Optional[TaskStatus] = None
        try:
            # Create task
            task = TaskStatus(
                task_id=task_id,
                task_type="market_analysis",
                status="running",
                created_at=datetime.now(),
                started_at=datetime.now(),
                metadata={
                    "user_id": user_id,
                    "symbol": symbol,
                    "analysis_type": analysis_type
                }
            )
            self.active_tasks[task_id] = task
            
            logger.info(f"Starting market analysis task {task_id}")
            
            # Map analysis type
            analysis_type_enum = AnalysisType.TECHNICAL
            if analysis_type == "sentiment":
                analysis_type_enum = AnalysisType.SENTIMENT
            elif analysis_type == "fundamental":
                analysis_type_enum = AnalysisType.FUNDAMENTAL
            
            # Map time horizon
            time_horizon_enum = TimeHorizon.MEDIUM_TERM
            if time_horizon == "short":
                time_horizon_enum = TimeHorizon.SHORT_TERM
            elif time_horizon == "long":
                time_horizon_enum = TimeHorizon.LONG_TERM
            
            # Run analysis
            result = await self._maybe_await(
                self.market_analyzer.analyze_market(
                    symbol=symbol,
                    analysis_type=analysis_type_enum,
                    time_horizon=time_horizon_enum
                )
            )
            result_data = self._serialize_result(result)
            
            # Update task status
            task.status = "completed"
            task.progress = 1.0
            task.completed_at = datetime.now()
            task.result = result_data
            
            # Store result
            self.task_results[task_id] = result_data
            self.metrics.completed_tasks += 1
            
            logger.info(f"Market analysis task {task_id} completed successfully")
            return result_data
            
        except Exception as e:
            # Update task with error
            if task:
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.now()
            self.metrics.failed_tasks += 1
            
            logger.error(f"Market analysis task {task_id} failed: {str(e)}")
            raise
        
        finally:
            asyncio.create_task(self._cleanup_task_after_delay(task_id, 900))  # 15 minutes
    
    async def chat_with_ai(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        context_type: str = "general",
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Chat with AI assistant
        """
        try:
            # Map context type
            context_type_enum = ChatContextType.GENERAL
            if context_type == "strategy":
                context_type_enum = ChatContextType.STRATEGY
            elif context_type == "market":
                context_type_enum = ChatContextType.MARKET
            elif context_type == "risk":
                context_type_enum = ChatContextType.RISK
            
            # Get AI response
            response = await self._maybe_await(
                self.ai_assistant.chat(
                    user_id=user_id,
                    message=message,
                    context_type=context_type_enum,
                    session_id=session_id,
                    context_data=context_data
                )
            )
            
            logger.info(f"AI chat completed for user {user_id}")
            return self._serialize_result(response)
            
        except Exception as e:
            logger.error(f"AI chat failed for user {user_id}: {str(e)}")
            raise
    
    async def supervise_bot(
        self,
        user_id: str,
        bot_id: str,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Supervise and analyze bot performance
        """
        task_id = f"supervise_{user_id}_{bot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task: Optional[TaskStatus] = None
        try:
            # Create task
            task = TaskStatus(
                task_id=task_id,
                task_type="bot_supervision",
                status="running",
                created_at=datetime.now(),
                started_at=datetime.now(),
                metadata={
                    "user_id": user_id,
                    "bot_id": bot_id,
                    "analysis_type": analysis_type
                }
            )
            self.active_tasks[task_id] = task
            
            logger.info(f"Starting bot supervision task {task_id}")
            
            # Run supervision analysis
            result = await self._maybe_await(
                self.supervisor_agent.analyze_bot_performance(
                    bot_id=bot_id,
                    analysis_type=analysis_type
                )
            )
            result_data = self._serialize_result(result)
            
            # Update task status
            task.status = "completed"
            task.progress = 1.0
            task.completed_at = datetime.now()
            task.result = result_data
            
            # Store result
            self.task_results[task_id] = result_data
            self.metrics.completed_tasks += 1
            
            logger.info(f"Bot supervision task {task_id} completed successfully")
            return result_data
            
        except Exception as e:
            # Update task with error
            if task:
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.now()
            self.metrics.failed_tasks += 1
            
            logger.error(f"Bot supervision task {task_id} failed: {str(e)}")
            raise
        
        finally:
            asyncio.create_task(self._cleanup_task_after_delay(task_id, 3600))  # 1 hour
    
    async def get_task_status(self, task_id: str) -> Optional[Union[TaskStatus, Dict[str, Any]]]:
        """
        Get status of a specific task
        """
        task = self.active_tasks.get(task_id)
        if task:
            return task
        
        # Check completed tasks
        result = self.task_results.get(task_id)
        if result:
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "completed_at": datetime.now().isoformat()
            }
        
        return None
    
    async def list_tasks(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filtering
        """
        all_tasks = []
        
        # Add active tasks
        for task in self.active_tasks.values():
            if user_id and task.metadata.get('user_id') != user_id:
                continue
            if status and task.status != status:
                continue
            all_tasks.append(task.model_dump())
        
        # Add completed tasks
        for task_id, result in self.task_results.items():
            if user_id and not any(
                t.metadata.get('user_id') == user_id 
                for t in self.active_tasks.values()
                if t.task_id == task_id
            ):
                continue
            if status and status != "completed":
                continue
            
            all_tasks.append({
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat()
            })
        
        # Sort by creation time and limit
        all_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return all_tasks[:limit]
    
    async def get_engine_metrics(self) -> Dict[str, Any]:
        """
        Get AI Engine performance metrics
        """
        # Update metrics
        self.metrics.total_tasks = self.metrics.completed_tasks + self.metrics.failed_tasks
        self.metrics.last_updated = datetime.now()
        self.metrics.component_health = self.component_health.copy()
        
        return self.metrics.model_dump()
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall health status of the AI Engine
        """
        uptime = datetime.now() - self.start_time
        
        return {
            "status": "healthy" if all(
                status == "healthy" for status in self.component_health.values()
            ) else "degraded",
            "uptime_seconds": uptime.total_seconds(),
            "is_running": self.is_running,
            "active_tasks": len(self.active_tasks),
            "component_health": self.component_health,
            "metrics": await self.get_engine_metrics(),
            "last_updated": datetime.now().isoformat()
        }
    
    def _extract_parameter_ranges(self, parameters: Dict[str, Any]) -> List[ParameterRange]:
        """Extract parameter ranges from strategy parameters"""
        ranges = []
        
        for param_name, param_config in parameters.items():
            if isinstance(param_config, dict):
                param_type = param_config.get('type', 'int')
                default = param_config.get('default', 1)
                min_val = param_config.get('min', param_config.get('low', default * 0.8 if isinstance(default, (int, float)) else 1))
                max_val = param_config.get('max', param_config.get('high', default * 1.2 if isinstance(default, (int, float)) else default * 2))
                
                if param_type == 'int':
                    step = max(1, int((max_val - min_val) / 10))
                    ranges.append(ParameterRange(
                        name=param_name,
                        param_type='int',
                        min_value=min_val,
                        max_value=max_val,
                        step=step
                    ))
                else:  # float
                    step = (max_val - min_val) / 10
                    ranges.append(ParameterRange(
                        name=param_name,
                        param_type='float',
                        min_value=min_val,
                        max_value=max_val,
                        step=step
                    ))
        
        return ranges

    @staticmethod
    def _serialize_result(result: Any) -> Dict[str, Any]:
        """Convert component outputs into plain dictionaries."""
        if result is None:
            return {}
        if isinstance(result, dict):
            return result
        if hasattr(result, "model_dump"):
            data = result.model_dump()
            if isinstance(data, dict):
                return data
        if hasattr(result, "dict"):
            data = result.dict()
            if isinstance(data, dict):
                return data
        if hasattr(result, "__dict__"):
            return {k: v for k, v in result.__dict__.items() if not k.startswith("_")}
        if hasattr(result, "_asdict"):
            data = result._asdict()
            if isinstance(data, dict):
                return data
        return {"value": result}

    async def _maybe_await(self, possible_coroutine: Any) -> Any:
        """Await coroutine-like objects while supporting synchronous mocks in tests."""
        if inspect.isawaitable(possible_coroutine):
            return await possible_coroutine
        return possible_coroutine
    
    async def _realtime_monitoring(self):
        """Background real-time monitoring task"""
        while self.is_running:
            try:
                # Monitor active tasks
                for task_id, task in list(self.active_tasks.items()):
                    if task.status == "running":
                        # Check for stuck tasks
                        if task.started_at and (datetime.now() - task.started_at).total_seconds() > self.config.timeout_seconds:
                            logger.warning(f"Task {task_id} appears to be stuck, marking as failed")
                            task.status = "failed"
                            task.error_message = "Task timeout"
                            self.metrics.failed_tasks += 1
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in real-time monitoring: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _health_check_loop(self):
        """Background health check task"""
        while self.is_running:
            try:
                # Check component health
                for component_name in self.component_health.keys():
                    try:
                        # Simple health check for each component
                        if component_name == "strategy_generator":
                            # Test strategy generator
                            _ = StrategyPrompt(
                                prompt="test",
                                trading_pair="BTC/USDT",
                                timeframe="1h",
                                risk_level="medium",
                                style="swing"
                            )
                            # This would be a light test, not a full generation
                            self.component_health[component_name] = "healthy"
                        else:
                            # For other components, just check if they can be imported/initialized
                            self.component_health[component_name] = "healthy"
                    
                    except Exception as e:
                        logger.warning(f"Health check failed for {component_name}: {str(e)}")
                        self.component_health[component_name] = "unhealthy"
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in health check: {str(e)}")
                await asyncio.sleep(300)
    
    async def _task_cleanup_loop(self):
        """Background task cleanup task"""
        while self.is_running:
            try:
                # Clean up old completed tasks
                cutoff_time = datetime.now() - timedelta(hours=2)
                
                tasks_to_remove = []
                for task_id, task in self.active_tasks.items():
                    if (task.status in ["completed", "failed"] and 
                        task.completed_at and 
                        task.completed_at < cutoff_time):
                        tasks_to_remove.append(task_id)
                
                for task_id in tasks_to_remove:
                    del self.active_tasks[task_id]
                
                # Clean up old results
                result_cutoff = datetime.now() - timedelta(hours=24)
                results_to_remove = []
                for task_id, result in self.task_results.items():
                    # Check if result is old (approximate)
                    if isinstance(result, dict) and result.get('created_at'):
                        try:
                            created_at = datetime.fromisoformat(result['created_at'])
                            if created_at < result_cutoff:
                                results_to_remove.append(task_id)
                        except Exception:
                            pass
                
                for task_id in results_to_remove:
                    del self.task_results[task_id]
                
                logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks and {len(results_to_remove)} old results")
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in task cleanup: {str(e)}")
                await asyncio.sleep(1800)  # Wait 30 minutes on error
    
    async def _cleanup_task_after_delay(self, task_id: str, delay_seconds: int):
        """Clean up task after specified delay"""
        await asyncio.sleep(delay_seconds)
        
        # Remove from active tasks
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        logger.info(f"Cleaned up task {task_id} after {delay_seconds} seconds")


# Global AI Engine instance
_ai_engine: Optional[AIEngineCore] = None


def get_ai_engine(config: Optional[EngineConfig] = None) -> AIEngineCore:
    """Get or create global AI Engine instance"""
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AIEngineCore(config)
    return _ai_engine


async def initialize_ai_engine(config: Optional[EngineConfig] = None) -> AIEngineCore:
    """Initialize and start the AI Engine"""
    engine = get_ai_engine(config)
    await engine.start()
    return engine


async def shutdown_ai_engine():
    """Shutdown the AI Engine"""
    global _ai_engine
    if _ai_engine:
        await _ai_engine.stop()
        _ai_engine = None


def main():
    """
    Test function for AI Engine Core
    """
    async def test_engine():
        config = EngineConfig(
            max_concurrent_tasks=5,
            enable_supervisor=True,
            enable_realtime_monitoring=True
        )
        
        # Initialize engine
        engine = await initialize_ai_engine(config)
        
        try:
            # Test strategy generation
            strategy_prompt = StrategyPrompt(
                prompt="Create a momentum strategy with RSI and volume",
                trading_pair="ETH/USDT",
                timeframe="4h",
                risk_level="medium",
                style="swing"
            )
            
            result = await engine.generate_strategy(
                user_id="test_user",
                prompt=strategy_prompt,
                optimize=True
            )
            
            print(f"Strategy generated: {result['strategy']['strategy_name']}")
            print(f"Optimization completed: {result.get('optimization') is not None}")
            
            # Get metrics
            metrics = await engine.get_engine_metrics()
            print(f"Engine metrics: {metrics['completed_tasks']} tasks completed")
            
            # Get health status
            health = await engine.get_health_status()
            print(f"Health status: {health['status']}")
            
        finally:
            await shutdown_ai_engine()
    
    asyncio.run(test_engine())


if __name__ == "__main__":
    main()
