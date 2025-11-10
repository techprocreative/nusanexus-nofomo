"""
NusaNexus NoFOMO - Bot Runner Main Entry Point
Enhanced bot runner with complete architecture integration
"""

import os
import sys
import json
import asyncio
import logging
import signal
from pathlib import Path

# Add bot runner modules to path
sys.path.insert(0, str(Path(__file__).parent))

from manager import BotManager
from config import ConfigManager
from logger import BotLogger
from exchange import ExchangeHandler
from strategy import StrategyManager
from worker import JobWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NusaNexusBotRunner:
    """
    Enhanced NusaNexus NoFOMO Bot Runner
    
    Main orchestrator for the complete bot runner system
    Integrates all components: BotManager, Worker, Logger, Config, Exchange, Strategy
    """
    
    def __init__(self):
        self.bot_manager = None
        self.job_worker = None
        self.config_manager = None
        self.logger = None
        self.exchange_handler = None
        self.strategy_manager = None
        self.is_running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info("NusaNexus Bot Runner initializing...")
    
    async def initialize(self):
        """Initialize all components"""
        try:
            # Initialize core components
            self.config_manager = ConfigManager()
            self.logger = BotLogger()
            self.exchange_handler = ExchangeHandler()
            self.strategy_manager = StrategyManager()
            
            # Initialize job worker
            self.job_worker = JobWorker()
            await self.job_worker.start()
            
            # Initialize bot manager
            self.bot_manager = BotManager()
            
            # Log successful initialization
            await self.logger.log_system_event('bot_runner_initialized', {
                'version': '1.0.0',
                'components_initialized': [
                    'bot_manager',
                    'job_worker', 
                    'config_manager',
                    'logger',
                    'exchange_handler',
                    'strategy_manager'
                ]
            })
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot runner: {str(e)}")
            raise
    
    async def start(self):
        """Start the bot runner system"""
        try:
            if self.is_running:
                logger.warning("Bot runner is already running")
                return
            
            # Initialize if not already done
            if not self.bot_manager:
                await self.initialize()
            
            self.is_running = True
            logger.info("Starting NusaNexus Bot Runner")
            
            # Log startup event
            await self.logger.log_system_event('bot_runner_started', {
                'timestamp': asyncio.get_event_loop().time(),
                'environment': os.getenv('ENVIRONMENT', 'development')
            })
            
            # Start background tasks
            asyncio.create_task(self._periodic_health_check())
            asyncio.create_task(self._monitor_system_resources())
            asyncio.create_task(self._process_websocket_events())
            
            logger.info("NusaNexus Bot Runner started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start bot runner: {str(e)}")
            await self.logger.log_system_event('bot_runner_start_failed', {
                'error': str(e),
                'error_type': type(e).__name__
            })
            raise
    
    async def stop(self):
        """Stop the bot runner system"""
        try:
            if not self.is_running:
                logger.warning("Bot runner is not running")
                return
            
            self.is_running = False
            logger.info("Stopping NusaNexus Bot Runner")
            
            # Log shutdown event
            await self.logger.log_system_event('bot_runner_shutdown', {
                'timestamp': asyncio.get_event_loop().time()
            })
            
            # Stop all bots gracefully
            if self.bot_manager:
                await self.bot_manager.shutdown()
            
            # Stop job worker
            if self.job_worker:
                await self.job_worker.stop()
            
            logger.info("NusaNexus Bot Runner stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during bot runner shutdown: {str(e)}")
    
    async def get_status(self) -> dict:
        """Get comprehensive bot runner status"""
        try:
            status = {
                'is_running': self.is_running,
                'timestamp': asyncio.get_event_loop().time(),
                'components': {}
            }
            
            # Bot manager status
            if self.bot_manager:
                status['components']['bot_manager'] = await self.bot_manager.health_check()
            
            # Job worker status
            if self.job_worker:
                status['components']['job_worker'] = await self.job_worker.get_queue_stats()
            
            # Config manager status
            if self.config_manager:
                status['components']['config_manager'] = {'status': 'active'}
            
            # Exchange handler status
            if self.exchange_handler:
                status['components']['exchange_handler'] = {'status': 'active'}
            
            # Strategy manager status
            if self.strategy_manager:
                status['components']['strategy_manager'] = {'status': 'active'}
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get status: {str(e)}")
            return {
                'is_running': self.is_running,
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }
    
    # Background task methods
    async def _periodic_health_check(self):
        """Perform periodic health checks"""
        while self.is_running:
            try:
                # Check all components
                health_status = await self.get_status()
                
                # Log health status
                await self.logger.log_system_event('health_check', health_status)
                
                # Check for any critical issues
                if not self._validate_health(health_status):
                    await self._handle_health_issues(health_status)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                await asyncio.sleep(30)  # Shorter interval on error
    
    async def _monitor_system_resources(self):
        """Monitor system resources and performance"""
        while self.is_running:
            try:
                import psutil
                
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Get process metrics
                process = psutil.Process()
                process_memory = process.memory_info()
                process_cpu = process.cpu_percent()
                
                # Resource monitoring data
                resource_data = {
                    'system': {
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'memory_available': memory.available,
                        'disk_percent': disk.percent,
                        'disk_free': disk.free
                    },
                    'process': {
                        'cpu_percent': process_cpu,
                        'memory_rss': process_memory.rss,
                        'memory_vms': process_memory.vms,
                        'num_threads': process.num_threads()
                    }
                }
                
                # Log resource usage
                await self.logger.log_system_event('resource_monitoring', resource_data)
                
                # Check resource limits
                if cpu_percent > 90:
                    await self.logger.log_system_event('high_cpu_usage', {'cpu_percent': cpu_percent}, level='warning')
                
                if memory.percent > 90:
                    await self.logger.log_system_event('high_memory_usage', {'memory_percent': memory.percent}, level='warning')
                
                if disk.percent > 90:
                    await self.logger.log_system_event('high_disk_usage', {'disk_percent': disk.percent}, level='warning')
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except ImportError:
                logger.warning("psutil not available for system monitoring")
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Resource monitoring error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _process_websocket_events(self):
        """Process real-time events for WebSocket notifications"""
        while self.is_running:
            try:
                # This would integrate with Redis pub/sub for real-time updates
                # For now, just simulate periodic status updates
                if self.bot_manager:
                    # Get all bot statuses
                    bot_statuses = await self.bot_manager.get_all_bots_status()
                    
                    # Publish status updates to Redis
                    for bot_status in bot_statuses:
                        standby_message = {
                            'type': 'bot_status_update',
                            'data': bot_status
                        }
                        # This would publish to a Redis channel for WebSocket forwarding
                        _ = standby_message  # placeholder until WebSocket integration is wired
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"WebSocket event processing error: {str(e)}")
                await asyncio.sleep(10)
    
    def _validate_health(self, health_status: dict) -> bool:
        """Validate system health"""
        try:
            # Check if any critical components are unhealthy
            components = health_status.get('components', {})
            
            for component_name, component_status in components.items():
                if isinstance(component_status, dict):
                    status = component_status.get('status', '')
                    if status in ['unhealthy', 'error', 'failed']:
                        logger.error(f"Component {component_name} is unhealthy: {component_status}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health validation error: {str(e)}")
            return False
    
    async def _handle_health_issues(self, health_status: dict):
        """Handle detected health issues"""
        try:
            # Log health issues
            await self.logger.log_system_event('health_issues_detected', {
                'status': health_status,
                'action': 'manual_intervention_required'
            }, level='warning')
            
            # TODO: Implement automatic recovery mechanisms
            # - Restart failed components
            # - Clear stuck processes
            # - Reconnect to external services
            # - Resource cleanup
            
        except Exception as e:
            logger.error(f"Error handling health issues: {str(e)}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self.stop())


# Global bot runner instance
bot_runner: NusaNexusBotRunner = None


def get_bot_runner() -> NusaNexusBotRunner:
    """Get bot runner instance"""
    global bot_runner
    if bot_runner is None:
        bot_runner = NusaNexusBotRunner()
    return bot_runner


async def main():
    """
    Main function to run the bot runner
    """
    runner = get_bot_runner()
    
    try:
        # Start the bot runner
        await runner.start()
        
        # Keep the runner running
        while runner.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Bot runner error: {str(e)}")
    finally:
        logger.info("Shutting down bot runner...")
        await runner.stop()


if __name__ == "__main__":
    # CLI interface
    import argparse
    
    parser = argparse.ArgumentParser(description="NusaNexus NoFOMO Bot Runner")
    parser.add_argument('command', choices=['start', 'stop', 'status', 'health'], 
                       help="Command to execute")
    parser.add_argument('--bot-id', help="Bot ID for bot-specific operations")
    parser.add_argument('--user-id', help="User ID for user-specific operations")
    
    args = parser.parse_args()
    
    if args.command == 'start':
        # Run as service
        asyncio.run(main())
        
    elif args.command == 'stop':
        # Stop the bot runner
        print("Stopping NusaNexus Bot Runner...")
        # Implementation would send stop signal to running instance
        
    elif args.command == 'status':
        # Get status
        runner = get_bot_runner()
        status = asyncio.run(runner.get_status())
        print(json.dumps(status, indent=2))
        
    elif args.command == 'health':
        # Health check only
        runner = get_bot_runner()
        asyncio.run(runner.initialize())
        status = asyncio.run(runner.get_status())
        print(f"Health: {'HEALTHY' if status.get('is_running') else 'UNHEALTHY'}")
        if not status.get('is_running'):
            print(f"Error: {status.get('error', 'Unknown error')}")
