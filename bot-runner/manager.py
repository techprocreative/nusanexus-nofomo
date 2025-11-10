"""
NusaNexus NoFOMO - Bot Manager
Core orchestrator for bot lifecycle management and process control
"""

import os
import json
import asyncio
import logging
import signal
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from supabase import create_client, Client

from config import ConfigManager
from logger import BotLogger
from exchange import ExchangeHandler
from strategy import StrategyManager
from worker import JobWorker

logger = logging.getLogger(__name__)


class BotStatus(Enum):
    """Bot status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class BotConfig:
    """Bot configuration data structure"""
    bot_id: str
    user_id: str
    name: str
    strategy: str
    exchange: str
    pair: str
    timeframe: str
    stake_amount: float
    max_open_trades: int
    dry_run: bool
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: bool = True
    config_data: Dict[str, Any] = None


@dataclass
class BotMetrics:
    """Bot performance metrics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    profit_loss: float = 0.0
    win_rate: float = 0.0
    total_volume: float = 0.0
    avg_trade_duration: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    last_update: str = ""


class BotManager:
    """
    Core Bot Manager - orchestrates all bot operations
    
    Responsibilities:
    - Bot lifecycle management (start/stop/pause/resume)
    - Process management and monitoring
    - Resource allocation and cleanup
    - Health monitoring and alerts
    - Integration with Redis queues and Supabase
    - WebSocket real-time updates
    """
    
    def __init__(self):
        # Core components
        self.config_manager = ConfigManager()
        self.logger = BotLogger()
        self.exchange_handler = ExchangeHandler()
        self.strategy_manager = StrategyManager()
        self.worker = JobWorker()
        
        # External services
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Internal state
        self.bots: Dict[str, BotConfig] = {}
        self.bot_processes: Dict[str, asyncio.subprocess.Process] = {}
        self.bot_status: Dict[str, BotStatus] = {}
        self.bot_metrics: Dict[str, BotMetrics] = {}
        self.bot_resources: Dict[str, Dict[str, Any]] = {}
        
        # Paths
        self.base_dir = Path(__file__).parent
        self.bots_dir = self.base_dir / 'bots'
        self.configs_dir = self.base_dir / 'configs'
        self.logs_dir = self.base_dir / 'logs'
        self.strategies_dir = self.base_dir / 'strategies'
        
        # Create directories
        for dir_path in [self.bots_dir, self.configs_dir, self.logs_dir, self.strategies_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info("Bot Manager initialized")
    
    async def start_bot(self, bot_id: str, user_id: str) -> Dict[str, Any]:
        """
        Start a bot with complete setup and monitoring
        
        Args:
            bot_id: Unique bot identifier
            user_id: User who owns the bot
            
        Returns:
            Dict with operation result and bot information
        """
        try:
            # Load bot configuration
            bot_config = await self._load_bot_config(bot_id, user_id)
            if not bot_config:
                return {"success": False, "error": "Bot configuration not found"}
            
            # Check if bot is already running
            if self.bot_status.get(bot_id) == BotStatus.RUNNING:
                return {"success": True, "message": "Bot is already running", "bot_id": bot_id}
            
            # Update status to starting
            await self._update_bot_status(bot_id, BotStatus.STARTING)
            
            # Validate bot configuration
            if not await self._validate_bot_config(bot_config):
                await self._update_bot_status(bot_id, BotStatus.ERROR)
                return {"success": False, "error": "Invalid bot configuration"}
            
            # Create bot workspace
            bot_workspace = await self._create_bot_workspace(bot_id, bot_config)
            if not bot_workspace:
                await self._update_bot_status(bot_id, BotStatus.ERROR)
                return {"success": False, "error": "Failed to create bot workspace"}
            
            # Start bot process
            process = await self._start_bot_process(bot_id, bot_config)
            if not process:
                await self._update_bot_status(bot_id, BotStatus.ERROR)
                return {"success": False, "error": "Failed to start bot process"}
            
            # Store bot state
            self.bots[bot_id] = bot_config
            self.bot_processes[bot_id] = process
            self.bot_status[bot_id] = BotStatus.RUNNING
            
            # Initialize metrics
            self.bot_metrics[bot_id] = BotMetrics(last_update=datetime.now().isoformat())
            
            # Start monitoring tasks
            asyncio.create_task(self._monitor_bot_process(bot_id))
            asyncio.create_task(self._update_metrics_periodically(bot_id))
            
            # Queue job for additional setup
            await self.worker.queue_job('bot_setup', {
                'bot_id': bot_id,
                'user_id': user_id,
                'action': 'post_start'
            })
            
            # Log bot start
            await self.logger.log_bot_event(bot_id, 'bot_started', {
                'bot_id': bot_id,
                'user_id': user_id,
                'strategy': bot_config.strategy,
                'exchange': bot_config.exchange,
                'pair': bot_config.pair
            })
            
            logger.info(f"Bot {bot_id} started successfully")
            return {
                "success": True, 
                "message": "Bot started successfully", 
                "bot_id": bot_id,
                "status": "running",
                "pid": process.pid
            }
            
        except Exception as e:
            logger.error(f"Failed to start bot {bot_id}: {str(e)}")
            await self._update_bot_status(bot_id, BotStatus.ERROR)
            await self.logger.log_bot_error(bot_id, 'start_failed', str(e))
            return {"success": False, "error": str(e)}
    
    async def stop_bot(self, bot_id: str, user_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Stop a bot with graceful shutdown
        
        Args:
            bot_id: Bot identifier
            user_id: User identifier
            force: Force kill if graceful shutdown fails
            
        Returns:
            Dict with operation result
        """
        try:
            if bot_id not in self.bot_status:
                return {"success": False, "error": "Bot not found"}
            
            if self.bot_status[bot_id] == BotStatus.STOPPED:
                return {"success": True, "message": "Bot is already stopped"}
            
            await self._update_bot_status(bot_id, BotStatus.STOPPING)
            
            # Stop bot process
            if bot_id in self.bot_processes:
                process = self.bot_processes[bot_id]
                
                if force:
                    process.terminate()
                else:
                    # Send graceful shutdown signal
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=30)
                    except asyncio.TimeoutExpired:
                        # Force kill if graceful shutdown fails
                        process.kill()
                        await process.wait()
            
            # Cleanup resources
            await self._cleanup_bot_resources(bot_id)
            
            # Update status
            await self._update_bot_status(bot_id, BotStatus.STOPPED)
            
            # Remove from active tracking
            if bot_id in self.bot_processes:
                del self.bot_processes[bot_id]
            if bot_id in self.bot_metrics:
                del self.bot_metrics[bot_id]
            
            # Log bot stop
            await self.logger.log_bot_event(bot_id, 'bot_stopped', {
                'bot_id': bot_id,
                'user_id': user_id,
                'force': force
            })
            
            logger.info(f"Bot {bot_id} stopped successfully")
            return {"success": True, "message": "Bot stopped successfully"}
            
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {str(e)}")
            await self._update_bot_status(bot_id, BotStatus.ERROR)
            return {"success": False, "error": str(e)}
    
    async def pause_bot(self, bot_id: str, user_id: str) -> Dict[str, Any]:
        """Pause a running bot"""
        try:
            if bot_id not in self.bot_status or self.bot_status[bot_id] != BotStatus.RUNNING:
                return {"success": False, "error": "Bot is not running"}
            
            # For now, we'll just update the status
            # In a full implementation, you might want to send pause signals
            await self._update_bot_status(bot_id, BotStatus.PAUSED)
            
            # Pause any monitoring tasks if needed
            await self.logger.log_bot_event(bot_id, 'bot_paused', {
                'bot_id': bot_id,
                'user_id': user_id
            })
            
            return {"success": True, "message": "Bot paused successfully"}
            
        except Exception as e:
            logger.error(f"Failed to pause bot {bot_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def resume_bot(self, bot_id: str, user_id: str) -> Dict[str, Any]:
        """Resume a paused bot"""
        try:
            if bot_id not in self.bot_status or self.bot_status[bot_id] != BotStatus.PAUSED:
                return {"success": False, "error": "Bot is not paused"}
            
            await self._update_bot_status(bot_id, BotStatus.RUNNING)
            
            await self.logger.log_bot_event(bot_id, 'bot_resumed', {
                'bot_id': bot_id,
                'user_id': user_id
            })
            
            return {"success": True, "message": "Bot resumed successfully"}
            
        except Exception as e:
            logger.error(f"Failed to resume bot {bot_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_bot_status(self, bot_id: str) -> Dict[str, Any]:
        """
        Get comprehensive bot status including process info and metrics
        
        Returns:
            Dict with complete bot status information
        """
        try:
            if bot_id not in self.bot_status:
                return {"status": "not_found", "bot_id": bot_id}
            
            status = self.bot_status[bot_id]
            result = {
                "bot_id": bot_id,
                "status": status.value,
                "last_update": datetime.now().isoformat()
            }
            
            # Add process information
            if bot_id in self.bot_processes:
                process = self.bot_processes[bot_id]
                result["process"] = {
                    "pid": process.pid,
                    "running": process.returncode is None
                }
            
            # Add metrics
            if bot_id in self.bot_metrics:
                result["metrics"] = asdict(self.bot_metrics[bot_id])
            
            # Add configuration
            if bot_id in self.bots:
                config = self.bots[bot_id]
                result["config"] = asdict(config)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get bot status for {bot_id}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_all_bots_status(self) -> List[Dict[str, Any]]:
        """Get status of all managed bots"""
        try:
            status_list = []
            for bot_id in self.bot_status.keys():
                status = await self.get_bot_status(bot_id)
                status_list.append(status)
            return status_list
            
        except Exception as e:
            logger.error(f"Failed to get all bots status: {str(e)}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check for the bot manager
        
        Returns:
            Dict with health status and diagnostics
        """
        try:
            running_bots = len([b for b in self.bot_status.values() if b == BotStatus.RUNNING])
            error_bots = len([b for b in self.bot_status.values() if b == BotStatus.ERROR])
            
            # Check external service health
            redis_healthy = False
            supabase_healthy = False
            
            try:
                self.redis_client.ping()
                redis_healthy = True
            except Exception:
                pass
            
            try:
                self.supabase.table('health_check').select('*').limit(1).execute()
                supabase_healthy = True
            except Exception:
                pass
            
            # System resource check
            import psutil
            system_metrics = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
            
            return {
                "status": "healthy" if error_bots == 0 else "degraded",
                "timestamp": datetime.now().isoformat(),
                "bots": {
                    "total": len(self.bot_status),
                    "running": running_bots,
                    "error": error_bots
                },
                "services": {
                    "redis": "connected" if redis_healthy else "disconnected",
                    "supabase": "connected" if supabase_healthy else "disconnected"
                },
                "system": system_metrics
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _load_bot_config(self, bot_id: str, user_id: str) -> Optional[BotConfig]:
        """Load bot configuration from database"""
        try:
            result = self.supabase.table('bots').select('*').eq('id', bot_id).eq('user_id', user_id).execute()
            
            if not result.data:
                return None
            
            bot_data = result.data[0]
            return BotConfig(
                bot_id=bot_data['id'],
                user_id=bot_data['user_id'],
                name=bot_data['name'],
                strategy=bot_data['strategy'],
                exchange=bot_data['exchange'],
                pair=bot_data.get('trading_pair', 'BTC/USDT'),
                timeframe=bot_data.get('timeframe', '1h'),
                stake_amount=float(bot_data.get('stake_amount', 100)),
                max_open_trades=int(bot_data.get('max_open_trades', 1)),
                dry_run=bot_data.get('is_paper_trade', True),
                stop_loss=bot_data.get('stop_loss'),
                take_profit=bot_data.get('take_profit'),
                config_data=bot_data.get('config_data', {})
            )
            
        except Exception as e:
            logger.error(f"Failed to load bot config {bot_id}: {str(e)}")
            return None
    
    async def _validate_bot_config(self, config: BotConfig) -> bool:
        """Validate bot configuration"""
        try:
            # Basic validation
            if not config.bot_id or not config.user_id:
                return False
            
            if not config.strategy or not config.exchange:
                return False
            
            if config.stake_amount <= 0:
                return False
            
            # Validate exchange configuration
            if not await self.exchange_handler.validate_exchange_config(config.exchange):
                return False
            
            # Validate strategy
            if not await self.strategy_manager.validate_strategy(config.strategy):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Bot config validation failed: {str(e)}")
            return False
    
    async def _create_bot_workspace(self, bot_id: str, config: BotConfig) -> Optional[Path]:
        """Create isolated workspace for bot"""
        try:
            bot_dir = self.bots_dir / bot_id
            bot_dir.mkdir(exist_ok=True)
            
            # Create subdirectories
            (bot_dir / 'data').mkdir(exist_ok=True)
            (bot_dir / 'logs').mkdir(exist_ok=True)
            (bot_dir / 'user_data').mkdir(exist_ok=True)
            
            # Create config file
            config_path = await self.config_manager.create_freqtrade_config(bot_id, config)
            if not config_path:
                return None
            
            return bot_dir
            
        except Exception as e:
            logger.error(f"Failed to create bot workspace for {bot_id}: {str(e)}")
            return None
    
    async def _start_bot_process(self, bot_id: str, config: BotConfig) -> Optional[asyncio.subprocess.Process]:
        """Start bot process"""
        try:
            bot_dir = self.bots_dir / bot_id
            config_path = bot_dir / 'config.json'
            
            # Prepare environment
            env = os.environ.copy()
            env['FREQTRADE__DATABASE__URL'] = f"sqlite:///{bot_dir}/trades.db"
            env['FREQTRADE__LOGLEVEL'] = 'INFO'
            
            # Prepare command
            cmd = [
                'freqtrade', 'trade',
                '--config', str(config_path),
                '--strategy-path', str(self.strategies_dir),
                '--logfile', str(bot_dir / 'logs' / f'{bot_id}.log')
            ]
            
            # Start process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(bot_dir),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            logger.info(f"Started bot process {bot_id} with PID {process.pid}")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start bot process {bot_id}: {str(e)}")
            return None
    
    async def _monitor_bot_process(self, bot_id: str):
        """Monitor bot process health and output"""
        try:
            while bot_id in self.bot_status and self.bot_status[bot_id] in [BotStatus.RUNNING, BotStatus.STARTING]:
                if bot_id not in self.bot_processes:
                    break
                
                process = self.bot_processes[bot_id]
                
                # Check if process is still running
                if process.returncode is not None:
                    # Process has terminated
                    if self.bot_status[bot_id] == BotStatus.RUNNING:
                        await self._update_bot_status(bot_id, BotStatus.ERROR)
                        await self.logger.log_bot_error(bot_id, 'process_terminated', f"Exit code: {process.returncode}")
                    
                    # Cleanup
                    del self.bot_processes[bot_id]
                    break
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except Exception as e:
            logger.error(f"Bot monitoring failed for {bot_id}: {str(e)}")
            await self._update_bot_status(bot_id, BotStatus.ERROR)
    
    async def _update_metrics_periodically(self, bot_id: str):
        """Update bot metrics periodically"""
        try:
            while bot_id in self.bot_status and self.bot_status[bot_id] == BotStatus.RUNNING:
                # Update metrics from database
                await self._update_bot_metrics(bot_id)
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
        except Exception as e:
            logger.error(f"Metrics update failed for {bot_id}: {str(e)}")
    
    async def _update_bot_metrics(self, bot_id: str):
        """Update bot metrics from database"""
        try:
            # Get recent trades
            trades = self.supabase.table('trades').select('*').eq('bot_id', bot_id).order('created_at', desc=True).limit(100).execute()
            
            if not trades.data:
                return
            
            # Calculate metrics
            total_trades = len(trades.data)
            winning_trades = len([t for t in trades.data if t.get('profit_ratio', 0) > 0])
            losing_trades = total_trades - winning_trades
            
            profit_loss = sum([t.get('profit_ratio', 0) for t in trades.data])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Update metrics
            if bot_id in self.bot_metrics:
                self.bot_metrics[bot_id].total_trades = total_trades
                self.bot_metrics[bot_id].winning_trades = winning_trades
                self.bot_metrics[bot_id].losing_trades = losing_trades
                self.bot_metrics[bot_id].profit_loss = profit_loss
                self.bot_metrics[bot_id].win_rate = win_rate
                self.bot_metrics[bot_id].last_update = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Failed to update metrics for {bot_id}: {str(e)}")
    
    async def _update_bot_status(self, bot_id: str, status: BotStatus):
        """Update bot status in database and memory"""
        try:
            self.bot_status[bot_id] = status
            
            # Update in database
            self.supabase.table('bots').update({
                'status': status.value,
                'updated_at': datetime.now().isoformat()
            }).eq('id', bot_id).execute()
            
            # Publish to Redis for real-time updates
            await self._publish_status_update(bot_id, status)
            
        except Exception as e:
            logger.error(f"Failed to update bot status for {bot_id}: {str(e)}")
    
    async def _publish_status_update(self, bot_id: str, status: BotStatus):
        """Publish status update to Redis for real-time notifications"""
        try:
            message = {
                "type": "bot_status_update",
                "bot_id": bot_id,
                "status": status.value,
                "timestamp": datetime.now().isoformat()
            }
            
            self.redis_client.publish('bot_updates', json.dumps(message))
            
        except Exception as e:
            logger.error(f"Failed to publish status update for {bot_id}: {str(e)}")
    
    async def _cleanup_bot_resources(self, bot_id: str):
        """Cleanup all resources for a bot"""
        try:
            # Remove from tracking
            if bot_id in self.bots:
                del self.bots[bot_id]
            if bot_id in self.bot_status:
                del self.bot_status[bot_id]
            if bot_id in self.bot_resources:
                del self.bot_resources[bot_id]
            
            # Clean up files
            bot_dir = self.bots_dir / bot_id
            if bot_dir.exists():
                import shutil
                shutil.rmtree(bot_dir)
            
        except Exception as e:
            logger.error(f"Failed to cleanup resources for {bot_id}: {str(e)}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """Graceful shutdown of bot manager"""
        try:
            logger.info("Bot Manager shutting down...")
            
            # Stop all running bots
            bot_ids = list(self.bot_status.keys())
            for bot_id in bot_ids:
                if self.bot_status[bot_id] in [BotStatus.RUNNING, BotStatus.STARTING]:
                    await self.stop_bot(bot_id, "system", force=True)
            
            # Stop worker
            if self.worker:
                await self.worker.stop()
            
            logger.info("Bot Manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")


# Global bot manager instance
bot_manager: Optional[BotManager] = None


def get_bot_manager() -> BotManager:
    """Get bot manager instance"""
    global bot_manager
    if bot_manager is None:
        bot_manager = BotManager()
    return bot_manager


if __name__ == "__main__":
    # Run bot manager as standalone service
    async def main():
        manager = BotManager()
        
        try:
            # Start health check service
            while True:
                health = await manager.health_check()
                logger.info(f"Bot Manager Health: {health}")
                await asyncio.sleep(60)  # Health check every minute
                
        except KeyboardInterrupt:
            logger.info("Shutting down Bot Manager...")
            await manager.shutdown()
    
    asyncio.run(main())
