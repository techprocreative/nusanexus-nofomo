"""
WebSocket endpoints for real-time updates in NusaNexus NoFOMO
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import structlog
from datetime import datetime

from app.models.common import WebSocketMessage

logger = structlog.get_logger()
router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.bot_connections: Dict[str, Set[str]] = {}  # bot_id -> set of connection_ids
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        logger.info("WebSocket connected", connection_id=connection_id, user_id=user_id)
    
    def disconnect(self, connection_id: str, user_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id in self.user_connections and connection_id in self.user_connections[user_id]:
            self.user_connections[user_id].disconnect(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from bot connections
        for bot_id, connections in self.bot_connections.items():
            if connection_id in connections:
                connections.discard(connection_id)
                if not connections:
                    del self.bot_connections[bot_id]
        
        logger.info("WebSocket disconnected", connection_id=connection_id, user_id=user_id)
    
    async def send_personal_message(self, message: WebSocketMessage, user_id: str):
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if connection_id in self.active_connections:
                    try:
                        await self.active_connections[connection_id].send_text(message.json())
                    except Exception as e:
                        logger.error("Failed to send personal message", connection_id=connection_id, error=str(e))
                        self.disconnect(connection_id, user_id)
    
    async def send_to_bot(self, message: WebSocketMessage, bot_id: str):
        if bot_id in self.bot_connections:
            for connection_id in self.bot_connections[bot_id]:
                if connection_id in self.active_connections:
                    try:
                        await self.active_connections[connection_id].send_text(message.json())
                    except Exception as e:
                        logger.error("Failed to send bot message", connection_id=connection_id, error=str(e))
                        # Find user_id for this connection
                        user_id = None
                        for uid, connections in self.user_connections.items():
                            if connection_id in connections:
                                user_id = uid
                                break
                        if user_id:
                            self.disconnect(connection_id, user_id)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        disconnected_connections = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message.json())
            except Exception as e:
                logger.error("Failed to broadcast message", connection_id=connection_id, error=str(e))
                disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            user_id = None
            for uid, connections in self.user_connections.items():
                if connection_id in connections:
                    user_id = uid
                    break
            if user_id:
                self.disconnect(connection_id, user_id)
    
    def subscribe_to_bot(self, connection_id: str, bot_id: str):
        if bot_id not in self.bot_connections:
            self.bot_connections[bot_id] = set()
        self.bot_connections[bot_id].add(connection_id)
    
    def unsubscribe_from_bot(self, connection_id: str, bot_id: str):
        if bot_id in self.bot_connections:
            self.bot_connections[bot_id].discard(connection_id)
            if not self.bot_connections[bot_id]:
                del self.bot_connections[bot_id]


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, connection_id: str = None, token: str = None):
    """
    Main WebSocket endpoint for real-time updates
    """
    if not connection_id:
        connection_id = f"conn_{datetime.utcnow().timestamp()}"
    
    try:
        # Get current user (this would need to be implemented)
        user_id = "anonymous"  # Placeholder
        
        await manager.connect(websocket, connection_id, user_id)
        
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            message_type = message_data.get("type")
            
            if message_type == "subscribe_bot":
                bot_id = message_data.get("bot_id")
                if bot_id:
                    manager.subscribe_to_bot(connection_id, bot_id)
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "bot_id": bot_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            
            elif message_type == "unsubscribe_bot":
                bot_id = message_data.get("bot_id")
                if bot_id:
                    manager.unsubscribe_from_bot(connection_id, bot_id)
                    await websocket.send_text(json.dumps({
                        "type": "unsubscribed",
                        "bot_id": bot_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            
            elif message_type == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id)
    except Exception as e:
        logger.error("WebSocket error", connection_id=connection_id, error=str(e))
        manager.disconnect(connection_id, user_id)


@router.websocket("/ws/bot/{bot_id}")
async def bot_websocket(websocket: WebSocket, bot_id: str, token: str = None):
    """
    Bot-specific WebSocket for direct bot updates
    """
    connection_id = f"bot_{bot_id}_{datetime.utcnow().timestamp()}"
    user_id = "anonymous"  # Placeholder
    
    try:
        await manager.connect(websocket, connection_id, user_id)
        manager.subscribe_to_bot(connection_id, bot_id)
        
        # Send initial status
        initial_message = WebSocketMessage(
            type="bot_status",
            data={
                "bot_id": bot_id,
                "status": "connected",
                "message": "WebSocket connection established"
            }
        )
        await websocket.send_text(initial_message.json())
        
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "bot_id": bot_id,
                    "timestamp": datetime.utcnow().isoformat()
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id)
    except Exception as e:
        logger.error("Bot WebSocket error", connection_id=connection_id, bot_id=bot_id, error=str(e))
        manager.disconnect(connection_id, user_id)


# Helper functions for sending updates
async def notify_bot_status_change(user_id: str, bot_id: str, status: str, details: Dict = None):
    """Send bot status update to all connected clients"""
    message = WebSocketMessage(
        type="bot_status",
        data={
            "bot_id": bot_id,
            "status": status,
            "details": details or {}
        }
    )
    await manager.send_personal_message(message, user_id)
    await manager.send_to_bot(message, bot_id)


async def notify_trade_update(user_id: str, trade_data: Dict):
    """Send trade update to connected clients"""
    message = WebSocketMessage(
        type="trade_update",
        data=trade_data
    )
    await manager.send_personal_message(message, user_id)


async def notify_market_data_update(user_id: str, market_data: Dict):
    """Send market data update to connected clients"""
    message = WebSocketMessage(
        type="market_data",
        data=market_data
    )
    await manager.send_personal_message(message, user_id)


async def notify_ai_analysis_complete(user_id: str, analysis_data: Dict):
    """Send AI analysis completion notification"""
    message = WebSocketMessage(
        type="ai_analysis_complete",
        data=analysis_data
    )
    await manager.send_personal_message(message, user_id)


async def notify_system_alert(user_id: str, alert_data: Dict):
    """Send system alert to connected clients"""
    message = WebSocketMessage(
        type="system_alert",
        data=alert_data
    )
    await manager.send_personal_message(message, user_id)