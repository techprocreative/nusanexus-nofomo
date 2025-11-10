"""
Notification service for real-time updates and alerts
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from app.core.database import get_db_client
from app.models.common import WebSocketMessage, BotStatusUpdate, TradeUpdate

logger = structlog.get_logger()


class NotificationService:
    """Service for managing notifications and real-time updates"""
    
    def __init__(self):
        self.db_client = get_db_client()
        self.websocket_connections: Dict[str, List] = {}  # user_id -> list of connections
        self.notification_queue: List[Dict[str, Any]] = []
    
    def register_websocket_connection(self, user_id: str, connection):
        """Register a WebSocket connection for a user"""
        if user_id not in self.websocket_connections:
            self.websocket_connections[user_id] = []
        self.websocket_connections[user_id].append(connection)
        logger.info("WebSocket connection registered", user_id=user_id)
    
    def unregister_websocket_connection(self, user_id: str, connection):
        """Unregister a WebSocket connection"""
        if user_id in self.websocket_connections:
            if connection in self.websocket_connections[user_id]:
                self.websocket_connections[user_id].remove(connection)
                logger.info("WebSocket connection unregistered", user_id=user_id)
            
            # Clean up empty lists
            if not self.websocket_connections[user_id]:
                del self.websocket_connections[user_id]
    
    async def send_websocket_message(self, user_id: str, message: WebSocketMessage):
        """Send a message to all WebSocket connections for a user"""
        if user_id not in self.websocket_connections:
            return
        
        disconnected_connections = []
        
        for connection in self.websocket_connections[user_id]:
            try:
                await connection.send_text(message.model_dump_json())
            except Exception as e:
                logger.error("Failed to send WebSocket message", user_id=user_id, error=str(e))
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.unregister_websocket_connection(user_id, connection)
    
    async def notify_bot_status_change(self, user_id: str, bot_id: str, status: str, details: Dict[str, Any] = None):
        """Notify about bot status changes"""
        try:
            message = BotStatusUpdate(
                type="bot_status",
                data={
                    "bot_id": bot_id,
                    "status": status,
                    "details": details or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            await self.send_websocket_message(user_id, message)
            
            # Also save notification to database
            self.db_client.create_log({
                "user_id": user_id,
                "bot_id": bot_id,
                "log_level": "info",
                "message": f"Bot status changed to {status}",
                "context": details or {},
                "source": "notification_service",
                "created_at": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error("Failed to notify bot status change", user_id=user_id, bot_id=bot_id, error=str(e))
    
    async def notify_trade_update(self, user_id: str, bot_id: str, trade_data: Dict[str, Any]):
        """Notify about trade updates"""
        try:
            message = TradeUpdate(
                type="trade_update",
                data={
                    "bot_id": bot_id,
                    "trade": trade_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            await self.send_websocket_message(user_id, message)
            
            # Create log entry
            self.db_client.create_log({
                "user_id": user_id,
                "bot_id": bot_id,
                "log_level": "info",
                "message": f"Trade {trade_data.get('side', '').upper()} executed: {trade_data.get('symbol', '')}",
                "context": trade_data,
                "source": "notification_service",
                "created_at": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error("Failed to notify trade update", user_id=user_id, bot_id=bot_id, error=str(e))
    
    async def notify_error(self, user_id: str, error_type: str, message: str, details: Dict[str, Any] = None):
        """Notify about errors"""
        try:
            error_message = WebSocketMessage(
                type="error",
                data={
                    "error_type": error_type,
                    "message": message,
                    "details": details or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            await self.send_websocket_message(user_id, error_message)
            
            # Create error log
            self.db_client.create_log({
                "user_id": user_id,
                "log_level": "error",
                "message": f"{error_type}: {message}",
                "context": details or {},
                "source": "notification_service",
                "created_at": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error("Failed to notify error", user_id=user_id, error=str(e))
    
    async def notify_ai_insight(self, user_id: str, insight_data: Dict[str, Any]):
        """Notify about AI insights and analysis"""
        try:
            ai_message = WebSocketMessage(
                type="ai_insight",
                data={
                    "insight": insight_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            await self.send_websocket_message(user_id, ai_message)
            
        except Exception as e:
            logger.error("Failed to notify AI insight", user_id=user_id, error=str(e))
    
    async def notify_system_alert(self, alert_type: str, message: str, severity: str = "info", details: Dict[str, Any] = None):
        """Send system-wide alerts"""
        try:
            alert_message = WebSocketMessage(
                type="system_alert",
                data={
                    "alert_type": alert_type,
                    "message": message,
                    "severity": severity,
                    "details": details or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Send to all connected users
            for user_id in self.websocket_connections.keys():
                await self.send_websocket_message(user_id, alert_message)
            
        except Exception as e:
            logger.error("Failed to send system alert", error=str(e))
    
    async def send_email_notification(self, user_id: str, subject: str, body: str, template: str = None):
        """Send email notification (placeholder for future implementation)"""
        # This would integrate with an email service like SendGrid, AWS SES, etc.
        logger.info("Email notification sent", user_id=user_id, subject=subject)
        
        # Create log entry
        self.db_client.create_log({
            "user_id": user_id,
            "log_level": "info",
            "message": f"Email sent: {subject}",
            "context": {
                "subject": subject,
                "body": body,
                "template": template
            },
            "source": "notification_service",
            "created_at": datetime.utcnow().isoformat()
        })
    
    async def send_push_notification(self, user_id: str, title: str, body: str, data: Dict[str, Any] = None):
        """Send push notification (placeholder for future implementation)"""
        # This would integrate with a push notification service like Firebase, Pusher, etc.
        logger.info("Push notification sent", user_id=user_id, title=title)
    
    def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user notification history from database"""
        try:
            logs = self.db_client.get_user_logs(user_id, limit)
            return [log for log in logs if log.get("source") == "notification_service"]
        except Exception as e:
            logger.error("Failed to get user notifications", user_id=user_id, error=str(e))
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check notification service health"""
        try:
            connected_users = len(self.websocket_connections)
            total_connections = sum(len(connections) for connections in self.websocket_connections.values())
            queue_size = len(self.notification_queue)
            
            return {
                "status": "healthy",
                "connected_users": connected_users,
                "total_connections": total_connections,
                "queue_size": queue_size,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error("Notification service health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global notification service instance
notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get notification service instance"""
    global notification_service
    if notification_service is None:
        notification_service = NotificationService()
    return notification_service