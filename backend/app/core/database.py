"""
Database client for NusaNexus NoFOMO
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client
from app.core.config import settings
import structlog

logger = structlog.get_logger()

class SupabaseClient:
    """Supabase client wrapper with NusaNexus-specific methods"""
    
    def __init__(self):
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError("Supabase URL and key must be configured")
        
        self.client: Client = create_client(settings.supabase_url, settings.supabase_key)
        self.service_role_client: Optional[Client] = None
        
        # Initialize service role client if service key is available
        if settings.supabase_service_role_key:
            self.service_role_client = create_client(
                settings.supabase_url, 
                settings.supabase_service_role_key
            )
    
    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current user from JWT token"""
        try:
            response = self.client.auth.get_user(token)
            return response.user.__dict__ if response.user else None
        except Exception as e:
            logger.error("Failed to get current user", error=str(e))
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            response = self.client.table('users').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to get user by ID", user_id=user_id, error=str(e))
            return None
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new user"""
        try:
            response = self.client.table('users').insert(user_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to create user", error=str(e))
            return None
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user data"""
        try:
            response = self.client.table('users').update(user_data).eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to update user", user_id=user_id, error=str(e))
            return None
    
    def get_user_bots(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all bots for a user"""
        try:
            response = self.client.table('bots').select('*').eq('user_id', user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error("Failed to get user bots", user_id=user_id, error=str(e))
            return []
    
    def get_bot_by_id(self, bot_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get bot by ID (user-specific)"""
        try:
            response = self.client.table('bots').select('*').eq('id', bot_id).eq('user_id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to get bot by ID", bot_id=bot_id, user_id=user_id, error=str(e))
            return None
    
    def create_bot(self, bot_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new bot"""
        try:
            response = self.client.table('bots').insert(bot_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to create bot", error=str(e))
            return None
    
    def update_bot(self, bot_id: str, user_id: str, bot_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update bot"""
        try:
            response = self.client.table('bots').update(bot_data).eq('id', bot_id).eq('user_id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to update bot", bot_id=bot_id, error=str(e))
            return None
    
    def delete_bot(self, bot_id: str, user_id: str) -> bool:
        """Delete bot"""
        try:
            response = self.client.table('bots').delete().eq('id', bot_id).eq('user_id', user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error("Failed to delete bot", bot_id=bot_id, error=str(e))
            return False
    
    def get_user_strategies(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all strategies for a user"""
        try:
            response = self.client.table('strategies').select('*').eq('user_id', user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error("Failed to get user strategies", user_id=user_id, error=str(e))
            return []
    
    def get_marketplace_strategies(self) -> List[Dict[str, Any]]:
        """Get public marketplace strategies"""
        try:
            response = self.client.table('strategies').select('*').eq('is_public', True).eq('strategy_type', 'marketplace').execute()
            return response.data or []
        except Exception as e:
            logger.error("Failed to get marketplace strategies", error=str(e))
            return []
    
    def get_strategy_by_id(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get strategy by ID"""
        try:
            response = self.client.table('strategies').select('*').eq('id', strategy_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to get strategy by ID", strategy_id=strategy_id, error=str(e))
            return None
    
    def create_strategy(self, strategy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new strategy"""
        try:
            response = self.client.table('strategies').insert(strategy_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to create strategy", error=str(e))
            return None
    
    def update_strategy(self, strategy_id: str, user_id: str, strategy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update strategy"""
        try:
            response = self.client.table('strategies').update(strategy_data).eq('id', strategy_id).eq('user_id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to update strategy", strategy_id=strategy_id, error=str(e))
            return None
    
    def delete_strategy(self, strategy_id: str, user_id: str) -> bool:
        """Delete strategy"""
        try:
            response = self.client.table('strategies').delete().eq('id', strategy_id).eq('user_id', user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error("Failed to delete strategy", strategy_id=strategy_id, error=str(e))
            return False
    
    def get_bot_trades(self, bot_id: str, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trades for a specific bot"""
        try:
            response = self.client.table('trades').select('*').eq('bot_id', bot_id).eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error("Failed to get bot trades", bot_id=bot_id, error=str(e))
            return []
    
    def create_trade(self, trade_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new trade"""
        try:
            response = self.client.table('trades').insert(trade_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to create trade", error=str(e))
            return None
    
    def update_trade(self, trade_id: str, trade_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update trade"""
        try:
            response = self.client.table('trades').update(trade_data).eq('id', trade_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to update trade", trade_id=trade_id, error=str(e))
            return None
    
    def create_ai_analysis(self, analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create AI analysis record"""
        try:
            response = self.client.table('ai_analyses').insert(analysis_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to create AI analysis", error=str(e))
            return None
    
    def create_backtest_result(self, result_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create backtest result"""
        try:
            response = self.client.table('backtest_results').insert(result_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to create backtest result", error=str(e))
            return None
    
    def create_log(self, log_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create log entry"""
        try:
            response = self.client.table('logs').insert(log_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to create log", error=str(e))
            return None
    
    def get_user_logs(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs for a user"""
        try:
            response = self.client.table('logs').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error("Failed to get user logs", user_id=user_id, error=str(e))
            return []
    
    def execute_rpc(self, function_name: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Execute PostgreSQL function"""
        try:
            if params:
                response = self.client.rpc(function_name, params).execute()
            else:
                response = self.client.rpc(function_name).execute()
            return response.data
        except Exception as e:
            logger.error("Failed to execute RPC", function=function_name, error=str(e))
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            start_time = datetime.now()
            self.client.table('users').select('count').limit(1).execute()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connected": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "response_time_ms": None,
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global database client instance
db_client: Optional[SupabaseClient] = None

def get_db_client() -> SupabaseClient:
    """Get database client instance"""
    global db_client
    if db_client is None:
        db_client = SupabaseClient()
    return db_client
