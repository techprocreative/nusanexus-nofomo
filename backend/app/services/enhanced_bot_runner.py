"""
NusaNexus NoFOMO - Enhanced Bot Runner Service
FastAPI integration for the complete bot runner system
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
import redis
from supabase import create_client, Client
import structlog

from app.core.database import get_db_client

logger = structlog.get_logger()


class EnhancedBotRunnerService:
    """
    Enhanced Bot Runner Service for FastAPI integration
    
    Integrates with the NusaNexus Bot Runner system
    """
    
    def __init__(self):
        self.db_client = get_db_client()
        
        # External bot runner service connection
        self.bot_runner_url = os.getenv('BOT_RUNNER_URL', 'http://localhost:8001')
        self.bot_runner_api_key = os.getenv('BOT_RUNNER_API_KEY', '')
        
        # HTTP client for bot runner communication
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Redis for real-time updates
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        # Supabase client
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Bot runner status cache
        self.bot_runner_status = {}
        self.last_health_check = None
        
        logger.info("Enhanced Bot Runner Service initialized")
    
    async def start_bot(self, bot_id: str, user_id: str) -> Dict[str, Any]:
        """
        Start a bot using the enhanced bot runner system
        
        Args:
            bot_id: Bot identifier
            user_id: User identifier
            
        Returns:
            Operation result
        """
        try:
            # Get bot configuration
            bot_config = await self._get_bot_config(bot_id, user_id)
            if not bot_config:
                return {"success": False, "error": "Bot not found"}
            
            # Start bot via bot runner service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.bot_runner_url}/api/v1/bots/{bot_id}/start",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    json={"user_id": user_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Update bot status in database
                    await self._update_bot_status(bot_id, user_id, "running", {
                        "started_at": datetime.now().isoformat(),
                        "bot_runner_status": result
                    })
                    
                    # Publish real-time update
                    await self._publish_bot_update(bot_id, "started", result)
                    
                    logger.info(f"Bot {bot_id} started successfully")
                    return {"success": True, "data": result}
                else:
                    error_msg = f"Bot runner error: {response.text}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
                    
        except Exception as e:
            logger.error(f"Failed to start bot {bot_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def stop_bot(self, bot_id: str, user_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Stop a bot
        
        Args:
            bot_id: Bot identifier
            user_id: User identifier
            force: Force stop
            
        Returns:
            Operation result
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.bot_runner_url}/api/v1/bots/{bot_id}/stop",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    json={"user_id": user_id, "force": force}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Update bot status
                    await self._update_bot_status(bot_id, user_id, "stopped", {
                        "stopped_at": datetime.now().isoformat(),
                        "forced": force
                    })
                    
                    # Publish real-time update
                    await self._publish_bot_update(bot_id, "stopped", result)
                    
                    logger.info(f"Bot {bot_id} stopped successfully")
                    return {"success": True, "data": result}
                else:
                    error_msg = f"Bot runner error: {response.text}"
                    return {"success": False, "error": error_msg}
                    
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def pause_bot(self, bot_id: str, user_id: str) -> Dict[str, Any]:
        """Pause a bot"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.bot_runner_url}/api/v1/bots/{bot_id}/pause",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    json={"user_id": user_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    await self._update_bot_status(bot_id, user_id, "paused", {
                        "paused_at": datetime.now().isoformat()
                    })
                    
                    await self._publish_bot_update(bot_id, "paused", result)
                    
                    return {"success": True, "data": result}
                else:
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to pause bot {bot_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def resume_bot(self, bot_id: str, user_id: str) -> Dict[str, Any]:
        """Resume a paused bot"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.bot_runner_url}/api/v1/bots/{bot_id}/resume",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    json={"user_id": user_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    await self._update_bot_status(bot_id, user_id, "running", {
                        "resumed_at": datetime.now().isoformat()
                    })
                    
                    await self._publish_bot_update(bot_id, "resumed", result)
                    
                    return {"success": True, "data": result}
                else:
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to resume bot {bot_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_bot_status(self, bot_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive bot status
        
        Args:
            bot_id: Bot identifier
            user_id: User identifier
            
        Returns:
            Bot status information
        """
        try:
            # Get status from bot runner
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.bot_runner_url}/api/v1/bots/{bot_id}/status",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    params={"user_id": user_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Enrich with database information
                    bot_config = await self._get_bot_config(bot_id, user_id)
                    if bot_config:
                        result["bot_config"] = bot_config
                    
                    return {"success": True, "data": result}
                else:
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to get bot status for {bot_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_all_bots_status(self, user_id: str) -> List[Dict[str, Any]]:
        """Get status of all user bots"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.bot_runner_url}/api/v1/bots/status",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    params={"user_id": user_id}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get all bots status: {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to get all bots status: {str(e)}")
            return []
    
    async def get_bot_logs(self, bot_id: str, user_id: str, log_type: str = None, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get bot logs"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.bot_runner_url}/api/v1/bots/{bot_id}/logs",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    params={
                        "user_id": user_id,
                        "log_type": log_type,
                        "limit": limit
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to get bot logs for {bot_id}: {str(e)}")
            return []
    
    async def get_bot_metrics(self, bot_id: str, user_id: str) -> Dict[str, Any]:
        """Get bot performance metrics"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.bot_runner_url}/api/v1/bots/{bot_id}/metrics",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    params={"user_id": user_id}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to get bot metrics for {bot_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_bot_config(self, bot_id: str, user_id: str, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update bot configuration"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.bot_runner_url}/api/v1/bots/{bot_id}/config",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    json={
                        "user_id": user_id,
                        "config_updates": config_updates
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Publish configuration update
                    await self._publish_bot_update(bot_id, "config_updated", result)
                    
                    return {"success": True, "data": result}
                else:
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to update bot config for {bot_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_exchange_connection(self, user_id: str, exchange: str) -> Dict[str, Any]:
        """Test exchange connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.bot_runner_url}/api/v1/exchanges/test",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    json={"user_id": user_id, "exchange": exchange}
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to test exchange connection: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def validate_strategy(self, strategy_code: str, strategy_name: str) -> Dict[str, Any]:
        """Validate strategy code"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.bot_runner_url}/api/v1/strategies/validate",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    json={
                        "strategy_code": strategy_code,
                        "strategy_name": strategy_name
                    }
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to validate strategy: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check bot runner system health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.bot_runner_url}/api/v1/health",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Update cache
                    self.bot_runner_status = result
                    self.last_health_check = datetime.now()
                    
                    return {
                        "success": True,
                        "data": result,
                        "cached_at": self.last_health_check.isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Health check failed: {response.text}",
                        "last_check": self.last_health_check.isoformat() if self.last_health_check else None
                    }
                    
        except Exception as e:
            logger.error(f"Bot runner health check failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "last_check": self.last_health_check.isoformat() if self.last_health_check else None
            }
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get job queue status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.bot_runner_url}/api/v1/queue/status",
                    headers={"Authorization": f"Bearer {self.bot_runner_api_key}"}
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Failed to get queue status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_bot_config(self, bot_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get bot configuration from database"""
        try:
            result = self.supabase.table('bots').select('*').eq('id', bot_id).eq('user_id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get bot config: {str(e)}")
            return None
    
    async def _update_bot_status(self, bot_id: str, user_id: str, status: str, additional_data: Dict[str, Any] = None):
        """Update bot status in database"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if additional_data:
                update_data.update(additional_data)
            
            self.supabase.table('bots').update(update_data).eq('id', bot_id).eq('user_id', user_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to update bot status: {str(e)}")
    
    async def _publish_bot_update(self, bot_id: str, event_type: str, data: Dict[str, Any]):
        """Publish bot update to Redis for real-time notifications"""
        try:
            message = {
                "type": "bot_update",
                "bot_id": bot_id,
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            self.redis_client.publish('bot_updates', message)
            
        except Exception as e:
            logger.error(f"Failed to publish bot update: {str(e)}")


# Global enhanced bot runner service instance
enhanced_bot_runner_service: Optional[EnhancedBotRunnerService] = None


def get_enhanced_bot_runner_service() -> EnhancedBotRunnerService:
    """Get enhanced bot runner service instance"""
    global enhanced_bot_runner_service
    if enhanced_bot_runner_service is None:
        enhanced_bot_runner_service = EnhancedBotRunnerService()
    return enhanced_bot_runner_service