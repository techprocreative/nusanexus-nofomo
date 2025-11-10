"""
NusaNexus NoFOMO - WebSocket Manager
Real-time AI updates and communication manager
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime
from pydantic import BaseModel
from fastapi import WebSocket, WebSocketDisconnect
import structlog
from enum import Enum

# Configure logging
logger = structlog.get_logger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    AI_ANALYSIS_UPDATE = "ai_analysis_update"
    STRATEGY_GENERATION = "strategy_generation"
    PARAMETER_OPTIMIZATION = "parameter_optimization"
    MARKET_ANALYSIS = "market_analysis"
    BOT_SUPERVISION = "bot_supervision"
    CHAT_MESSAGE = "chat_message"
    ALERT = "alert"
    METRICS_UPDATE = "metrics_update"
    HEALTH_STATUS = "health_status"
    TASK_STATUS = "task_status"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime
    message_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    priority: int = 1  # 1-5, 5 being highest


class ConnectionManager:
    """
    Manages WebSocket connections for real-time AI updates
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}  # connection_id -> metadata
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.ai_engine = None  # Will be set later
        
    def set_ai_engine(self, ai_engine):
        """Set the AI engine instance for broadcasting"""
        self.ai_engine = ai_engine
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        # Store connection
        self.active_connections[connection_id] = websocket
        
        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        # Store metadata
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "subscriptions": set()
        }
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        
        # Send welcome message
        await self.send_personal_message(
            WebSocketMessage(
                type=MessageType.HEALTH_STATUS,
                data={
                    "status": "connected",
                    "message": "AI Engine connection established",
                    "connection_id": connection_id
                },
                timestamp=datetime.now(),
                message_id=f"welcome_{connection_id}",
                user_id=user_id
            ),
            user_id
        )
    
    def disconnect(self, connection_id: str):
        """Handle WebSocket disconnection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from user connections
        if connection_id in self.connection_metadata:
            user_id = self.connection_metadata[connection_id]["user_id"]
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
        
        # Remove metadata
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: WebSocketMessage, user_id: str):
        """Send message to specific user"""
        if user_id not in self.user_connections:
            logger.warning(f"User {user_id} has no active connections")
            return
        
        message_data = message.model_dump()
        message_str = json.dumps(message_data, default=str)
        
        # Send to all connections for this user
        for connection_id in self.user_connections[user_id].copy():
            try:
                websocket = self.active_connections.get(connection_id)
                if websocket:
                    await websocket.send_text(message_str)
                    # Update last activity
                    if connection_id in self.connection_metadata:
                        self.connection_metadata[connection_id]["last_activity"] = datetime.now()
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {str(e)}")
                # Remove failed connection
                self.disconnect(connection_id)
    
    async def broadcast_message(self, message: WebSocketMessage, user_ids: Optional[List[str]] = None):
        """Broadcast message to multiple users"""
        if user_ids is None:
            # Broadcast to all users
            user_ids = list(self.user_connections.keys())
        
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
    
    async def broadcast_to_subscribers(
        self,
        message: WebSocketMessage,
        subscription_type: str
    ):
        """Broadcast to users subscribed to specific type"""
        for connection_id, metadata in self.connection_metadata.items():
            if subscription_type in metadata.get("subscriptions", set()):
                user_id = metadata["user_id"]
                await self.send_personal_message(message, user_id)
    
    def subscribe(self, connection_id: str, subscription_type: str):
        """Subscribe connection to specific message type"""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"].add(subscription_type)
    
    def unsubscribe(self, connection_id: str, subscription_type: str):
        """Unsubscribe connection from specific message type"""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["subscriptions"].discard(subscription_type)
    
    async def handle_websocket_messages(self, websocket: WebSocket, user_id: str, connection_id: str):
        """Handle incoming WebSocket messages"""
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Update last activity
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]["last_activity"] = datetime.now()
                
                # Process message
                await self._process_incoming_message(message_data, user_id, connection_id)
                
        except WebSocketDisconnect:
            self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")
            # Send error message
            error_message = WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": str(e)},
                timestamp=datetime.now(),
                message_id=f"error_{connection_id}",
                user_id=user_id
            )
            await self.send_personal_message(error_message, user_id)
    
    async def _process_incoming_message(self, message_data: Dict[str, Any], user_id: str, connection_id: str):
        """Process incoming WebSocket message"""
        try:
            message_type = message_data.get("type")
            
            if message_type == "subscribe":
                # Handle subscription
                subscription_type = message_data.get("subscription_type")
                if subscription_type:
                    self.subscribe(connection_id, subscription_type)
                    
                    # Send confirmation
                    await self.send_personal_message(
                        WebSocketMessage(
                            type=MessageType.HEALTH_STATUS,
                            data={
                                "status": "subscribed",
                                "subscription_type": subscription_type
                            },
                            timestamp=datetime.now(),
                            message_id=f"sub_confirm_{connection_id}",
                            user_id=user_id
                        ),
                        user_id
                    )
            
            elif message_type == "unsubscribe":
                # Handle unsubscription
                subscription_type = message_data.get("subscription_type")
                if subscription_type:
                    self.unsubscribe(connection_id, subscription_type)
            
            elif message_type == "ping":
                # Handle ping
                await self.send_personal_message(
                    WebSocketMessage(
                        type=MessageType.HEALTH_STATUS,
                        data={"status": "pong"},
                        timestamp=datetime.now(),
                        message_id=f"pong_{connection_id}",
                        user_id=user_id
                    ),
                    user_id
                )
            
            elif message_type == "request_metrics":
                # Handle metrics request
                if self.ai_engine:
                    metrics = await self.ai_engine.get_engine_metrics()
                    await self.send_personal_message(
                        WebSocketMessage(
                            type=MessageType.METRICS_UPDATE,
                            data=metrics,
                            timestamp=datetime.now(),
                            message_id=f"metrics_{connection_id}",
                            user_id=user_id
                        ),
                        user_id
                    )
            
            elif message_type == "request_health":
                # Handle health check request
                if self.ai_engine:
                    health = await self.ai_engine.get_health_status()
                    await self.send_personal_message(
                        WebSocketMessage(
                            type=MessageType.HEALTH_STATUS,
                            data=health,
                            timestamp=datetime.now(),
                            message_id=f"health_{connection_id}",
                            user_id=user_id
                        ),
                        user_id
                    )
            
            # Call registered handlers
            if message_type in self.message_handlers:
                for handler in self.message_handlers[message_type]:
                    try:
                        await handler(message_data, user_id, connection_id)
                    except Exception as e:
                        logger.error(f"Error in message handler: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error processing incoming message: {str(e)}")
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register message handler"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def get_user_count(self) -> int:
        """Get number of users with active connections"""
        return len(self.user_connections)
    
    def get_active_users(self) -> List[str]:
        """Get list of active user IDs"""
        return list(self.user_connections.keys())


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get or create global connection manager"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


class AIWebSocketBroadcaster:
    """
    Utility class for broadcasting AI-related updates
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def broadcast_task_update(
        self,
        user_id: str,
        task_id: str,
        task_type: str,
        status: str,
        progress: float,
        message: str,
        result: Optional[Dict[str, Any]] = None
    ):
        """Broadcast task status update"""
        message = WebSocketMessage(
            type=MessageType.TASK_STATUS,
            data={
                "task_id": task_id,
                "task_type": task_type,
                "status": status,
                "progress": progress,
                "message": message,
                "result": result
            },
            timestamp=datetime.now(),
            message_id=f"task_{task_id}",
            user_id=user_id
        )
        
        await self.connection_manager.send_personal_message(message, user_id)
    
    async def broadcast_strategy_update(
        self,
        user_id: str,
        strategy_id: str,
        status: str,
        progress: float,
        data: Dict[str, Any]
    ):
        """Broadcast strategy generation update"""
        message = WebSocketMessage(
            type=MessageType.STRATEGY_GENERATION,
            data={
                "strategy_id": strategy_id,
                "status": status,
                "progress": progress,
                **data
            },
            timestamp=datetime.now(),
            message_id=f"strategy_{strategy_id}",
            user_id=user_id
        )
        
        await self.connection_manager.send_personal_message(message, user_id)
    
    async def broadcast_analysis_update(
        self,
        user_id: str,
        analysis_id: str,
        analysis_type: str,
        progress: float,
        data: Dict[str, Any]
    ):
        """Broadcast analysis update"""
        message = WebSocketMessage(
            type=MessageType.AI_ANALYSIS_UPDATE,
            data={
                "analysis_id": analysis_id,
                "analysis_type": analysis_type,
                "progress": progress,
                **data
            },
            timestamp=datetime.now(),
            message_id=f"analysis_{analysis_id}",
            user_id=user_id
        )
        
        await self.connection_manager.send_personal_message(message, user_id)
    
    async def broadcast_chat_message(
        self,
        user_id: str,
        session_id: str,
        message: str,
        response: str,
        confidence: float
    ):
        """Broadcast chat message"""
        message = WebSocketMessage(
            type=MessageType.CHAT_MESSAGE,
            data={
                "session_id": session_id,
                "user_message": message,
                "ai_response": response,
                "confidence": confidence
            },
            timestamp=datetime.now(),
            message_id=f"chat_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=user_id
        )
        
        await self.connection_manager.send_personal_message(message, user_id)
    
    async def broadcast_alert(
        self,
        user_id: str,
        alert_id: str,
        level: str,
        title: str,
        message: str,
        data: Dict[str, Any]
    ):
        """Broadcast alert"""
        message = WebSocketMessage(
            type=MessageType.ALERT,
            data={
                "alert_id": alert_id,
                "level": level,
                "title": title,
                "message": message,
                **data
            },
            timestamp=datetime.now(),
            message_id=f"alert_{alert_id}",
            user_id=user_id,
            priority=5 if level == "critical" else 3
        )
        
        await self.connection_manager.send_personal_message(message, user_id)
    
    async def broadcast_metrics_update(self, metrics: Dict[str, Any]):
        """Broadcast metrics update to all subscribers"""
        message = WebSocketMessage(
            type=MessageType.METRICS_UPDATE,
            data=metrics,
            timestamp=datetime.now(),
            message_id=f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            priority=1
        )
        
        await self.connection_manager.broadcast_to_subscribers(
            message, "metrics"
        )
    
    async def broadcast_health_status(self, health_status: Dict[str, Any]):
        """Broadcast health status update to all subscribers"""
        message = WebSocketMessage(
            type=MessageType.HEALTH_STATUS,
            data=health_status,
            timestamp=datetime.now(),
            message_id=f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            priority=2
        )
        
        await self.connection_manager.broadcast_to_subscribers(
            message, "health"
        )


async def create_websocket_endpoint(websocket: WebSocket, user_id: str, connection_id: str):
    """Create WebSocket endpoint for AI Engine"""
    connection_manager = get_connection_manager()
    await connection_manager.connect(websocket, user_id, connection_id)
    
    try:
        await connection_manager.handle_websocket_messages(websocket, user_id, connection_id)
    finally:
        connection_manager.disconnect(connection_id)


def main():
    """
    Test function for WebSocket manager
    """
    async def test_websocket_manager():
        # Test connection manager
        manager = get_connection_manager()
        
        # Create broadcaster
        broadcaster = AIWebSocketBroadcaster(manager)
        
        # Test message creation
        test_message = WebSocketMessage(
            type=MessageType.HEALTH_STATUS,
            data={"status": "test"},
            timestamp=datetime.now(),
            message_id="test_001"
        )
        
        print(f"WebSocket message created: {test_message.type}")
        print(f"Active connections: {manager.get_connection_count()}")
        print(f"Active users: {manager.get_user_count()}")
        
        # Test metrics update
        test_metrics = {
            "total_tasks": 10,
            "completed_tasks": 8,
            "failed_tasks": 2,
            "active_connections": 0
        }
        
        await broadcaster.broadcast_metrics_update(test_metrics)
        print("Metrics update broadcasted")
    
    asyncio.run(test_websocket_manager())


if __name__ == "__main__":
    main()
