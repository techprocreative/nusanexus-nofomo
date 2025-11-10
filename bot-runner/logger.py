"""
NusaNexus NoFOMO - Bot Logger
Comprehensive logging system for bot operations and trade data
"""

import os
import json
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import aiofiles
import redis
from supabase import create_client, Client
import structlog

logger = structlog.get_logger(__name__)


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogType(Enum):
    """Types of logs"""
    BOT_EVENT = "bot_event"
    TRADE = "trade"
    ERROR = "error"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    AUDIT = "audit"


class BotLogger:
    """
    Comprehensive logging system for bot runner
    
    Features:
    - Structured logging with JSON format
    - Multiple log sinks (file, database, Redis)
    - Real-time log streaming
    - Log rotation and archiving
    - Performance metrics logging
    - Trade execution tracking
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Logging configuration
        self.base_dir = Path(__file__).parent
        self.logs_dir = self.base_dir / 'logs'
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create log directories
        (self.logs_dir / 'bots').mkdir(exist_ok=True)
        (self.logs_dir / 'trades').mkdir(exist_ok=True)
        (self.logs_dir / 'system').mkdir(exist_ok=True)
        (self.logs_dir / 'errors').mkdir(exist_ok=True)
        (self.logs_dir / 'performance').mkdir(exist_ok=True)
        
        # Setup structured logging
        self._setup_structured_logging()
        
        # Log streaming subscribers
        self.streaming_subscribers = {}
        
        logger.info("Bot Logger initialized")
    
    def _setup_structured_logging(self):
        """Setup structured logging configuration"""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    async def log_bot_event(self, bot_id: str, event_type: str, data: Dict[str, Any], 
                           level: LogLevel = LogLevel.INFO) -> bool:
        """
        Log bot events and state changes
        
        Args:
            bot_id: Bot identifier
            event_type: Type of event
            data: Event data
            level: Log level
            
        Returns:
            Success status
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "bot_id": bot_id,
                "log_type": LogType.BOT_EVENT.value,
                "event_type": event_type,
                "level": level.value,
                "data": data
            }
            
            # Write to file
            await self._write_to_file('bots', bot_id, log_entry)
            
            # Store in database
            await self._store_in_database('bot_logs', log_entry)
            
            # Publish to Redis for real-time streaming
            await self._publish_to_stream('bot_events', log_entry)
            
            # Log to structured logger
            log_message = f"Bot event: {event_type} for bot {bot_id}"
            if level == LogLevel.ERROR:
                logger.error(log_message, **data)
            elif level == LogLevel.WARNING:
                logger.warning(log_message, **data)
            else:
                logger.info(log_message, **data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log bot event: {str(e)}")
            return False
    
    async def log_trade(self, bot_id: str, trade_data: Dict[str, Any], 
                       level: LogLevel = LogLevel.INFO) -> bool:
        """
        Log trade execution and results
        
        Args:
            bot_id: Bot identifier
            trade_data: Trade data
            level: Log level
            
        Returns:
            Success status
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "bot_id": bot_id,
                "log_type": LogType.TRADE.value,
                "level": level.value,
                "data": trade_data
            }
            
            # Write to trade-specific log file
            await self._write_to_file('trades', bot_id, log_entry)
            
            # Store in database
            await self._store_in_database('trade_logs', log_entry)
            
            # Publish to Redis for real-time streaming
            await self._publish_to_stream('trade_updates', log_entry)
            
            # Update trade in main database
            await self._update_trade_in_db(trade_data)
            
            # Log to structured logger
            action = trade_data.get('action', 'unknown')
            pair = trade_data.get('pair', 'unknown')
            amount = trade_data.get('amount', 0)
            price = trade_data.get('price', 0)
            
            log_message = f"Trade {action}: {pair} {amount} @ {price}"
            if level == LogLevel.ERROR:
                logger.error(log_message, bot_id=bot_id, **trade_data)
            elif level == LogLevel.WARNING:
                logger.warning(log_message, bot_id=bot_id, **trade_data)
            else:
                logger.info(log_message, bot_id=bot_id, **trade_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log trade: {str(e)}")
            return False
    
    async def log_bot_error(self, bot_id: str, error_type: str, error_message: str, 
                           data: Dict[str, Any] = None, level: LogLevel = LogLevel.ERROR) -> bool:
        """
        Log bot errors and exceptions
        
        Args:
            bot_id: Bot identifier
            error_type: Type of error
            error_message: Error message
            data: Additional error data
            level: Log level
            
        Returns:
            Success status
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "bot_id": bot_id,
                "log_type": LogType.ERROR.value,
                "error_type": error_type,
                "error_message": error_message,
                "level": level.value,
                "data": data or {}
            }
            
            # Write to error-specific log file
            await self._write_to_file('errors', bot_id, log_entry)
            
            # Store in database
            await self._store_in_database('error_logs', log_entry)
            
            # Publish to Redis for real-time streaming
            await self._publish_to_stream('error_alerts', log_entry)
            
            # Log to structured logger
            logger.error(f"Bot error: {error_type} - {error_message}", 
                        bot_id=bot_id, error_type=error_type, **data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log bot error: {str(e)}")
            return False
    
    async def log_system_event(self, event_type: str, data: Dict[str, Any], 
                              level: LogLevel = LogLevel.INFO) -> bool:
        """
        Log system-level events
        
        Args:
            event_type: Type of system event
            data: Event data
            level: Log level
            
        Returns:
            Success status
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "log_type": LogType.SYSTEM.value,
                "event_type": event_type,
                "level": level.value,
                "data": data
            }
            
            # Write to system log file
            await self._write_to_file('system', 'system', log_entry)
            
            # Store in database
            await self._store_in_database('system_logs', log_entry)
            
            # Publish to Redis for real-time streaming
            await self._publish_to_stream('system_events', log_entry)
            
            # Log to structured logger
            log_message = f"System event: {event_type}"
            if level == LogLevel.ERROR:
                logger.error(log_message, **data)
            elif level == LogLevel.WARNING:
                logger.warning(log_message, **data)
            else:
                logger.info(log_message, **data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log system event: {str(e)}")
            return False
    
    async def log_performance_metrics(self, bot_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Log bot performance metrics
        
        Args:
            bot_id: Bot identifier
            metrics: Performance metrics data
            
        Returns:
            Success status
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "bot_id": bot_id,
                "log_type": LogType.PERFORMANCE.value,
                "data": metrics
            }
            
            # Write to performance log file
            await self._write_to_file('performance', bot_id, log_entry)
            
            # Store in database
            await self._store_in_database('performance_logs', log_entry)
            
            # Publish to Redis for real-time streaming
            await self._publish_to_stream('performance_updates', log_entry)
            
            # Log to structured logger
            logger.info("Performance metrics update", bot_id=bot_id, **metrics)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log performance metrics: {str(e)}")
            return False
    
    async def log_audit_event(self, user_id: str, action: str, resource: str, 
                             details: Dict[str, Any] = None) -> bool:
        """
        Log audit events for security and compliance
        
        Args:
            user_id: User identifier
            action: Action performed
            resource: Resource affected
            details: Additional details
            
        Returns:
            Success status
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "log_type": LogType.AUDIT.value,
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "details": details or {}
            }
            
            # Write to audit log file
            audit_file = self.logs_dir / 'audit' / f"{datetime.now().strftime('%Y%m%d')}.log"
            await self._write_to_file_direct(audit_file, log_entry)
            
            # Store in database
            await self._store_in_database('audit_logs', log_entry)
            
            # Log to structured logger
            logger.info("Audit event", user_id=user_id, action=action, resource=resource, **details)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            return False
    
    async def get_bot_logs(self, bot_id: str, log_type: LogType = None, 
                          start_time: datetime = None, end_time: datetime = None, 
                          limit: int = 100) -> list:
        """
        Retrieve bot logs with filtering
        
        Args:
            bot_id: Bot identifier
            log_type: Type of logs to retrieve
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of logs
            
        Returns:
            List of log entries
        """
        try:
            query = self.supabase.table('bot_logs').select('*').eq('bot_id', bot_id)
            
            if log_type:
                query = query.eq('log_type', log_type.value)
            
            if start_time:
                query = query.gte('timestamp', start_time.isoformat())
            
            if end_time:
                query = query.lte('timestamp', end_time.isoformat())
            
            result = query.order('timestamp', desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get bot logs for {bot_id}: {str(e)}")
            return []
    
    async def get_trade_logs(self, bot_id: str = None, start_time: datetime = None, 
                            end_time: datetime = None, limit: int = 100) -> list:
        """
        Retrieve trade logs with filtering
        
        Args:
            bot_id: Bot identifier filter
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of logs
            
        Returns:
            List of trade log entries
        """
        try:
            query = self.supabase.table('trade_logs').select('*')
            
            if bot_id:
                query = query.eq('bot_id', bot_id)
            
            if start_time:
                query = query.gte('timestamp', start_time.isoformat())
            
            if end_time:
                query = query.lte('timestamp', end_time.isoformat())
            
            result = query.order('timestamp', desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get trade logs: {str(e)}")
            return []
    
    async def get_error_logs(self, bot_id: str = None, start_time: datetime = None, 
                            end_time: datetime = None, limit: int = 100) -> list:
        """
        Retrieve error logs with filtering
        
        Args:
            bot_id: Bot identifier filter
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of logs
            
        Returns:
            List of error log entries
        """
        try:
            query = self.supabase.table('error_logs').select('*')
            
            if bot_id:
                query = query.eq('bot_id', bot_id)
            
            if start_time:
                query = query.gte('timestamp', start_time.isoformat())
            
            if end_time:
                query = query.lte('timestamp', end_time.isoformat())
            
            result = query.order('timestamp', desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get error logs: {str(e)}")
            return []
    
    async def start_log_stream(self, stream_name: str, log_types: list = None) -> str:
        """
        Start real-time log streaming
        
        Args:
            stream_name: Name of the stream
            log_types: Types of logs to stream
            
        Returns:
            Stream identifier
        """
        try:
            stream_id = f"{stream_name}_{datetime.now().timestamp()}"
            
            # Store stream configuration
            self.streaming_subscribers[stream_id] = {
                "name": stream_name,
                "types": log_types or [LogType.BOT_EVENT.value, LogType.TRADE.value, LogType.ERROR.value],
                "active": True
            }
            
            logger.info(f"Started log stream: {stream_id}")
            return stream_id
            
        except Exception as e:
            logger.error(f"Failed to start log stream: {str(e)}")
            return ""
    
    async def stop_log_stream(self, stream_id: str) -> bool:
        """
        Stop log streaming
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            Success status
        """
        try:
            if stream_id in self.streaming_subscribers:
                self.streaming_subscribers[stream_id]["active"] = False
                del self.streaming_subscribers[stream_id]
                
                logger.info(f"Stopped log stream: {stream_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop log stream: {str(e)}")
            return False
    
    async def _write_to_file(self, log_type: str, bot_id: str, log_entry: Dict[str, Any]):
        """Write log entry to file"""
        try:
            log_dir = self.logs_dir / log_type
            log_file = log_dir / f"{bot_id}.log"
            
            async with aiofiles.open(log_file, 'a') as f:
                await f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write to log file: {str(e)}")
    
    async def _write_to_file_direct(self, file_path: Path, log_entry: Dict[str, Any]):
        """Write log entry directly to specified file path"""
        try:
            file_path.parent.mkdir(exist_ok=True)
            
            async with aiofiles.open(file_path, 'a') as f:
                await f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write to log file: {str(e)}")
    
    async def _store_in_database(self, table_name: str, log_entry: Dict[str, Any]):
        """Store log entry in database"""
        try:
            self.supabase.table(table_name).insert(log_entry).execute()
        except Exception as e:
            logger.error(f"Failed to store in database: {str(e)}")
    
    async def _publish_to_stream(self, channel: str, log_entry: Dict[str, Any]):
        """Publish log entry to Redis channel"""
        try:
            self.redis_client.publish(channel, json.dumps(log_entry))
        except Exception as e:
            logger.error(f"Failed to publish to stream: {str(e)}")
    
    async def _update_trade_in_db(self, trade_data: Dict[str, Any]):
        """Update trade in main database"""
        try:
            trade_id = trade_data.get('trade_id')
            if not trade_id:
                return
            
            update_data = {
                'updated_at': datetime.now().isoformat()
            }
            
            # Add trade-specific fields
            for field in ['profit_ratio', 'profit_abs', 'amount', 'price', 'status']:
                if field in trade_data:
                    update_data[field] = trade_data[field]
            
            self.supabase.table('trades').update(update_data).eq('id', trade_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to update trade in database: {str(e)}")
    
    async def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Clean up old log files and database records
        
        Args:
            days_to_keep: Number of days of logs to keep
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Clean up old log files
            for log_type_dir in self.logs_dir.iterdir():
                if log_type_dir.is_dir():
                    for log_file in log_type_dir.glob("*.log"):
                        if log_file.stat().st_mtime < cutoff_date.timestamp():
                            log_file.unlink()
            
            # Clean up old database records
            cutoff_str = cutoff_date.isoformat()
            
            for table in ['bot_logs', 'trade_logs', 'error_logs', 'system_logs', 'performance_logs']:
                try:
                    self.supabase.table(table).delete().lt('timestamp', cutoff_str).execute()
                except Exception as e:
                    logger.error(f"Failed to cleanup {table}: {str(e)}")
            
            logger.info("Log cleanup completed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {str(e)}")


if __name__ == "__main__":
    # Test bot logger
    async def test():
        bot_logger = BotLogger()
        
        # Test bot event logging
        await bot_logger.log_bot_event("test_bot_123", "bot_started", {
            "strategy": "SampleStrategy",
            "exchange": "binance",
            "pair": "BTC/USDT"
        })
        
        # Test trade logging
        await bot_logger.log_trade("test_bot_123", {
            "action": "buy",
            "pair": "BTC/USDT",
            "amount": 0.001,
            "price": 45000,
            "trade_id": "trade_123"
        })
        
        # Test error logging
        await bot_logger.log_bot_error("test_bot_123", "strategy_error", "RSI calculation failed", {
            "rsi_value": None,
            "error_code": "DIVISION_BY_ZERO"
        })
        
        # Test system event logging
        await bot_logger.log_system_event("bot_manager_startup", {
            "version": "1.0.0",
            "startup_time": datetime.now().isoformat()
        })
        
        print("Test logging completed")
    
    import asyncio
    asyncio.run(test())