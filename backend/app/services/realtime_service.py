"""
Real-time service for NusaNexus NoFOMO
Combines WebSocket and Supabase Realtime for comprehensive real-time features
"""

import json
import asyncio
import structlog
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from fastapi import WebSocket

from app.core.supabase import supabase_client

logger = structlog.get_logger()


class MessageType(str, Enum):
    """Real-time message types"""
    # Bot events
    BOT_STATUS = "bot_status"
    BOT_PERFORMANCE = "bot_performance"
    BOT_TRADE = "bot_trade"
    
    # Trade events
    TRADE_EXECUTED = "trade_executed"
    TRADE_UPDATED = "trade_updated"
    TRADE_CANCELLED = "trade_cancelled"
    
    # Strategy events
    STRATEGY_GENERATION = "strategy_generation"
    STRATEGY_COMPLETED = "strategy_completed"
    STRATEGY_ERROR = "strategy_error"
    
    # AI events
    AI_ANALYSIS = "ai_analysis"
    AI_CHAT = "ai_chat"
    AI_RESPONSE = "ai_response"
    
    # Dashboard events
    METRICS_UPDATE = "metrics_update"
    PORTFOLIO_UPDATE = "portfolio_update"
    MARKET_DATA = "market_data"
    
    # System events
    ALERT = "alert"
    NOTIFICATION = "notification"
    SYSTEM_STATUS = "system_status"
    
    # Health events
    HEARTBEAT = "heartbeat"
    CONNECTION_STATUS = "connection_status"


class RealtimeMessage:
    """Real-time message model"""
    def __init__(
        self,
        message_type: MessageType,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        bot_id: Optional[str] = None,
        trade_id: Optional[str] = None,
        strategy_id: Optional[str] = None,
        priority: int = 1,
        timestamp: Optional[datetime] = None
    ):
        self.message_type = message_type
        self.data = data
        self.user_id = user_id
        self.bot_id = bot_id
        self.trade_id = trade_id
        self.strategy_id = strategy_id
        self.priority = priority
        self.timestamp = timestamp or datetime.utcnow()
        self.message_id = f"{message_type}_{self.timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "type": self.message_type,
            "data": self.data,
            "user_id": self.user_id,
            "bot_id": self.bot_id,
            "trade_id": self.trade_id,
            "strategy_id": self.strategy_id,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class RealtimeConnection:
    """Real-time connection manager"""
    
    def __init__(self, user_id: str, websocket: WebSocket, connection_id: str):
        self.user_id = user_id
        self.websocket = websocket
        self.connection_id = connection_id
        self.connected_at = datetime.utcnow()
        self.last_activity = self.connected_at
        self.subscriptions: Set[str] = set()
        self.is_alive = True
    
    async def send_message(self, message: RealtimeMessage):
        """Send message to this connection"""
        try:
            await self.websocket.send_text(message.to_json())
            self.last_activity = datetime.utcnow()
        except Exception as e:
            logger.error("Failed to send message", 
                        connection_id=self.connection_id, 
                        error=str(e))
            self.is_alive = False
    
    def add_subscription(self, subscription_type: str):
        """Add subscription for this connection"""
        self.subscriptions.add(subscription_type)
    
    def remove_subscription(self, subscription_type: str):
        """Remove subscription for this connection"""
        self.subscriptions.discard(subscription_type)
    
    def is_subscribed_to(self, subscription_type: str) -> bool:
        """Check if connection is subscribed to type"""
        return subscription_type in self.subscriptions


class RealtimeService:
    """Main real-time service"""
    
    def __init__(self):
        self.connections: Dict[str, RealtimeConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self.bot_subscriptions: Dict[str, Set[str]] = {}  # bot_id -> set of connection_ids
        self.trade_subscriptions: Dict[str, Set[str]] = {}  # trade_id -> set of connection_ids
        self.strategy_subscriptions: Dict[str, Set[str]] = {}  # strategy_id -> set of connection_ids
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.health_check_interval = 30
        self.connection_timeout = 300  # 5 minutes
        
        # Supabase Realtime subscriptions
        self.supabase_subscriptions: Dict[str, Any] = {}
    
    async def connect_websocket(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        connection_id: str,
        token: str
    ) -> bool:
        """Connect WebSocket with authentication"""
        try:
            # Validate token
            supabase_client.init(access_token=token)
            auth_service = supabase_client.service_client.auth
            
            # Get user info
            user = auth_service.get_user(token)
            if not user or not user.user:
                logger.warning("Invalid token for WebSocket connection", 
                              connection_id=connection_id)
                await websocket.close(code=1008, reason="Invalid token")
                return False
            
            # Accept connection
            await websocket.accept()
            
            # Create connection
            connection = RealtimeConnection(user_id, websocket, connection_id)
            self.connections[connection_id] = connection
            
            # Add to user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Subscribe to user-specific events
            connection.add_subscription(f"user:{user_id}")
            connection.add_subscription("system")
            
            # Send welcome message
            welcome_message = RealtimeMessage(
                message_type=MessageType.CONNECTION_STATUS,
                data={
                    "status": "connected",
                    "connection_id": connection_id,
                    "message": "Real-time connection established"
                },
                user_id=user_id,
                priority=5
            )
            await connection.send_message(welcome_message)
            
            # Start connection health check
            asyncio.create_task(self._connection_health_check(connection_id))
            
            logger.info("WebSocket connected", 
                       connection_id=connection_id, 
                       user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("WebSocket connection error", 
                        connection_id=connection_id, 
                        error=str(e))
            try:
                await websocket.close(code=1011, reason="Internal error")
            except Exception:
                pass
            return False
    
    async def disconnect_websocket(self, connection_id: str):
        """Disconnect WebSocket"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        user_id = connection.user_id
        
        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from subscriptions
        for bot_id, conns in self.bot_subscriptions.items():
            conns.discard(connection_id)
            if not conns:
                del self.bot_subscriptions[bot_id]
        
        for trade_id, conns in self.trade_subscriptions.items():
            conns.discard(connection_id)
            if not conns:
                del self.trade_subscriptions[trade_id]
        
        for strategy_id, conns in self.strategy_subscriptions.items():
            conns.discard(connection_id)
            if not conns:
                del self.strategy_subscriptions[strategy_id]
        
        # Remove connection
        del self.connections[connection_id]
        
        logger.info("WebSocket disconnected", 
                   connection_id=connection_id, 
                   user_id=user_id)
    
    async def handle_websocket_message(self, connection_id: str, message_data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        connection.last_activity = datetime.utcnow()
        
        try:
            message_type = message_data.get("type")
            
            if message_type == "subscribe":
                subscription_type = message_data.get("subscription")
                if subscription_type:
                    connection.add_subscription(subscription_type)
                    
                    # Handle specific subscription types
                    if subscription_type.startswith("bot:"):
                        bot_id = subscription_type.split(":", 1)[1]
                        if bot_id not in self.bot_subscriptions:
                            self.bot_subscriptions[bot_id] = set()
                        self.bot_subscriptions[bot_id].add(connection_id)
                        await self._subscribe_to_bot_updates(bot_id)
                    
                    elif subscription_type.startswith("trade:"):
                        trade_id = subscription_type.split(":", 1)[1]
                        if trade_id not in self.trade_subscriptions:
                            self.trade_subscriptions[trade_id] = set()
                        self.trade_subscriptions[trade_id].add(connection_id)
                        await self._subscribe_to_trade_updates(trade_id)
                    
                    elif subscription_type.startswith("strategy:"):
                        strategy_id = subscription_type.split(":", 1)[1]
                        if strategy_id not in self.strategy_subscriptions:
                            self.strategy_subscriptions[strategy_id] = set()
                        self.strategy_subscriptions[strategy_id].add(connection_id)
                        await self._subscribe_to_strategy_updates(strategy_id)
            
            elif message_type == "unsubscribe":
                subscription_type = message_data.get("subscription")
                if subscription_type:
                    connection.remove_subscription(subscription_type)
                    
                    if subscription_type.startswith("bot:"):
                        bot_id = subscription_type.split(":", 1)[1]
                        if bot_id in self.bot_subscriptions:
                            self.bot_subscriptions[bot_id].discard(connection_id)
                    
                    elif subscription_type.startswith("trade:"):
                        trade_id = subscription_type.split(":", 1)[1]
                        if trade_id in self.trade_subscriptions:
                            self.trade_subscriptions[trade_id].discard(connection_id)
                    
                    elif subscription_type.startswith("strategy:"):
                        strategy_id = subscription_type.split(":", 1)[1]
                        if strategy_id in self.strategy_subscriptions:
                            self.strategy_subscriptions[strategy_id].discard(connection_id)
            
            elif message_type == "ping":
                await connection.send_message(RealtimeMessage(
                    message_type=MessageType.HEARTBEAT,
                    data={"timestamp": datetime.utcnow().isoformat()},
                    user_id=connection.user_id
                ))
            
            # Call registered handlers
            if message_type in self.message_handlers:
                for handler in self.message_handlers[message_type]:
                    try:
                        await handler(message_data, connection)
                    except Exception as e:
                        logger.error("Message handler error", 
                                   connection_id=connection_id, 
                                   error=str(e))
        
        except Exception as e:
            logger.error("Error handling WebSocket message", 
                        connection_id=connection_id, 
                        error=str(e))
    
    async def broadcast_message(self, message: RealtimeMessage):
        """Broadcast message to relevant connections"""
        # Determine target connections
        target_connections = set()
        
        # Direct user message
        if message.user_id and message.user_id in self.user_connections:
            target_connections.update(self.user_connections[message.user_id])
        
        # Bot subscription message
        if message.bot_id and message.bot_id in self.bot_subscriptions:
            target_connections.update(self.bot_subscriptions[message.bot_id])
        
        # Trade subscription message
        if message.trade_id and message.trade_id in self.trade_subscriptions:
            target_connections.update(self.trade_subscriptions[message.trade_id])
        
        # Strategy subscription message
        if message.strategy_id and message.strategy_id in self.strategy_subscriptions:
            target_connections.update(self.strategy_subscriptions[message.strategy_id])
        
        # System-wide message
        if message.message_type in [MessageType.SYSTEM_STATUS, MessageType.METRICS_UPDATE]:
            target_connections.update(self.connections.keys())
        
        # Send to target connections
        disconnected = []
        for connection_id in target_connections:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                if connection.is_alive:
                    try:
                        await connection.send_message(message)
                    except Exception as e:
                        logger.error("Failed to broadcast message", 
                                   connection_id=connection_id, 
                                   error=str(e))
                        disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self.disconnect_websocket(connection_id)
    
    async def notify_bot_status(self, user_id: str, bot_id: str, status: str, data: Dict[str, Any] = None):
        """Notify bot status change"""
        message = RealtimeMessage(
            message_type=MessageType.BOT_STATUS,
            data={
                "bot_id": bot_id,
                "status": status,
                **(data or {})
            },
            user_id=user_id,
            bot_id=bot_id
        )
        await self.broadcast_message(message)
    
    async def notify_trade_executed(self, user_id: str, trade_data: Dict[str, Any]):
        """Notify trade execution"""
        trade_id = trade_data.get("id")
        bot_id = trade_data.get("bot_id")
        
        message = RealtimeMessage(
            message_type=MessageType.TRADE_EXECUTED,
            data=trade_data,
            user_id=user_id,
            bot_id=bot_id,
            trade_id=trade_id
        )
        await self.broadcast_message(message)
    
    async def notify_strategy_progress(self, user_id: str, strategy_id: str, progress: float, data: Dict[str, Any] = None):
        """Notify strategy generation progress"""
        message = RealtimeMessage(
            message_type=MessageType.STRATEGY_GENERATION,
            data={
                "strategy_id": strategy_id,
                "progress": progress,
                **(data or {})
            },
            user_id=user_id,
            strategy_id=strategy_id
        )
        await self.broadcast_message(message)
    
    async def notify_ai_chat(self, user_id: str, session_id: str, message_data: Dict[str, Any]):
        """Notify AI chat update"""
        message = RealtimeMessage(
            message_type=MessageType.AI_CHAT,
            data=message_data,
            user_id=user_id
        )
        await self.broadcast_message(message)
    
    async def notify_metrics_update(self, user_id: str, metrics_data: Dict[str, Any]):
        """Notify metrics update"""
        message = RealtimeMessage(
            message_type=MessageType.METRICS_UPDATE,
            data=metrics_data,
            user_id=user_id
        )
        await self.broadcast_message(message)
    
    async def notify_alert(self, user_id: str, alert_data: Dict[str, Any], priority: int = 3):
        """Notify alert"""
        message = RealtimeMessage(
            message_type=MessageType.ALERT,
            data=alert_data,
            user_id=user_id,
            priority=priority
        )
        await self.broadcast_message(message)
    
    async def _connection_health_check(self, connection_id: str):
        """Health check for connection"""
        while connection_id in self.connections:
            try:
                connection = self.connections[connection_id]
                if not connection.is_alive:
                    break
                
                # Check if connection is stale
                if datetime.utcnow() - connection.last_activity > timedelta(seconds=self.connection_timeout):
                    logger.warning("Connection timed out", connection_id=connection_id)
                    await self.disconnect_websocket(connection_id)
                    break
                
                # Send heartbeat
                if connection.is_alive:
                    heartbeat = RealtimeMessage(
                        message_type=MessageType.HEARTBEAT,
                        data={"timestamp": datetime.utcnow().isoformat()},
                        user_id=connection.user_id
                    )
                    await connection.send_message(heartbeat)
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error("Health check error", 
                           connection_id=connection_id, 
                           error=str(e))
                break
    
    async def _subscribe_to_bot_updates(self, bot_id: str):
        """Subscribe to Supabase Realtime bot updates"""
        # This would set up Supabase Realtime subscription for bot changes
        pass
    
    async def _subscribe_to_trade_updates(self, trade_id: str):
        """Subscribe to Supabase Realtime trade updates"""
        # This would set up Supabase Realtime subscription for trade changes
        pass
    
    async def _subscribe_to_strategy_updates(self, strategy_id: str):
        """Subscribe to Supabase Realtime strategy updates"""
        # This would set up Supabase Realtime subscription for strategy changes
        pass
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register message handler"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.connections),
            "total_users": len(self.user_connections),
            "active_bots": len(self.bot_subscriptions),
            "active_trades": len(self.trade_subscriptions),
            "active_strategies": len(self.strategy_subscriptions)
        }


# Global real-time service instance
realtime_service = RealtimeService()


def get_realtime_service() -> RealtimeService:
    """Get global real-time service instance"""
    return realtime_service
