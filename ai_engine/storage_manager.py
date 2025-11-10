"""
NusaNexus NoFOMO - Storage Manager
Supabase integration for AI analysis storage
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from pydantic import BaseModel
import structlog
from pathlib import Path

# Supabase client
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase client not available. Using fallback storage.")

# Configure logging
logger = structlog.get_logger(__name__)


class AnalysisStorage(BaseModel):
    """Base model for AI analysis storage"""
    id: Optional[str] = None
    user_id: str
    analysis_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class StrategyStorage(BaseModel):
    """Model for strategy storage"""
    id: Optional[str] = None
    user_id: str
    strategy_name: str
    strategy_code: str
    parameters: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    is_public: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChatSessionStorage(BaseModel):
    """Model for chat session storage"""
    id: Optional[str] = None
    user_id: str
    session_id: str
    title: str
    messages: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OptimizationResultStorage(BaseModel):
    """Model for optimization results storage"""
    id: Optional[str] = None
    user_id: str
    strategy_id: str
    optimization_id: str
    results: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    created_at: Optional[datetime] = None


class StorageManager:
    """
    Manages storage operations for AI Engine with Supabase integration
    """
    
    def __init__(self):
        self.use_supabase = SUPABASE_AVAILABLE and self._check_supabase_config()
        
        if self.use_supabase:
            self.supabase: Client = create_client(
                os.getenv('SUPABASE_URL', ''),
                os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
            )
            logger.info("Supabase storage enabled")
        else:
            self.local_storage_dir = Path('ai_storage')
            self.local_storage_dir.mkdir(exist_ok=True)
            logger.info("Using local file storage")
    
    def _check_supabase_config(self) -> bool:
        """Check if Supabase configuration is available"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase configuration not found")
            return False
        
        return True
    
    async def store_analysis(
        self,
        user_id: str,
        analysis_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_hours: Optional[int] = None
    ) -> str:
        """
        Store AI analysis result
        """
        try:
            storage = AnalysisStorage(
                user_id=user_id,
                analysis_type=analysis_type,
                data=data,
                metadata=metadata or {},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=expires_in_hours) if expires_in_hours else None
            )
            
            if self.use_supabase:
                return await self._store_analysis_supabase(storage)
            else:
                return await self._store_analysis_local(storage)
            
        except Exception as e:
            logger.error(f"Failed to store analysis: {str(e)}")
            raise
    
    async def _store_analysis_supabase(self, storage: AnalysisStorage) -> str:
        """Store analysis in Supabase"""
        try:
            # Note: This would require proper table setup in Supabase
            # For now, using a generic approach
            response = self.supabase.table('ai_analyses').insert({
                'user_id': storage.user_id,
                'analysis_type': storage.analysis_type,
                'data': storage.data,
                'metadata': storage.metadata,
                'created_at': storage.created_at.isoformat(),
                'updated_at': storage.updated_at.isoformat(),
                'expires_at': storage.expires_at.isoformat() if storage.expires_at else None
            }).execute()
            
            if response.data:
                analysis_id = response.data[0]['id']
                logger.info(f"Analysis stored in Supabase: {analysis_id}")
                return analysis_id
            else:
                raise Exception("No data returned from Supabase")
                
        except Exception as e:
            logger.error(f"Supabase storage failed: {str(e)}")
            # Fallback to local storage
            return await self._store_analysis_local(storage)
    
    async def _store_analysis_local(self, storage: AnalysisStorage) -> str:
        """Store analysis locally"""
        analysis_id = f"analysis_{storage.user_id}_{storage.analysis_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        storage.id = analysis_id
        
        # Save to file
        filepath = self.local_storage_dir / f"analyses/{analysis_id}.json"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(storage.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Analysis stored locally: {analysis_id}")
        return analysis_id
    
    async def get_analysis(
        self,
        analysis_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored analysis
        """
        try:
            if self.use_supabase:
                return await self._get_analysis_supabase(analysis_id, user_id)
            else:
                return await self._get_analysis_local(analysis_id, user_id)
                
        except Exception as e:
            logger.error(f"Failed to retrieve analysis {analysis_id}: {str(e)}")
            return None
    
    async def _get_analysis_supabase(self, analysis_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis from Supabase"""
        try:
            response = self.supabase.table('ai_analyses').select('*').eq('id', analysis_id).eq('user_id', user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get analysis from Supabase: {str(e)}")
            return None
    
    async def _get_analysis_local(self, analysis_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis from local storage"""
        try:
            filepath = self.local_storage_dir / f"analyses/{analysis_id}.json"
            if filepath.exists():
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Check if user has access
                if data.get('user_id') == user_id:
                    return data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get analysis from local storage: {str(e)}")
            return None
    
    async def list_analyses(
        self,
        user_id: str,
        analysis_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List user's analyses
        """
        try:
            if self.use_supabase:
                return await self._list_analyses_supabase(user_id, analysis_type, limit)
            else:
                return await self._list_analyses_local(user_id, analysis_type, limit)
                
        except Exception as e:
            logger.error(f"Failed to list analyses for user {user_id}: {str(e)}")
            return []
    
    async def _list_analyses_supabase(
        self,
        user_id: str,
        analysis_type: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """List analyses from Supabase"""
        try:
            query = self.supabase.table('ai_analyses').select('*').eq('user_id', user_id)
            
            if analysis_type:
                query = query.eq('analysis_type', analysis_type)
            
            response = query.order('created_at', desc=True).limit(limit).execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to list analyses from Supabase: {str(e)}")
            return []
    
    async def _list_analyses_local(
        self,
        user_id: str,
        analysis_type: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """List analyses from local storage"""
        try:
            analyses_dir = self.local_storage_dir / "analyses"
            if not analyses_dir.exists():
                return []
            
            analyses = []
            for filepath in analyses_dir.glob("*.json"):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    if data.get('user_id') == user_id:
                        if not analysis_type or data.get('analysis_type') == analysis_type:
                            analyses.append(data)
                except Exception:
                    continue  # Skip corrupted files
            
            # Sort by created_at and limit
            analyses.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return analyses[:limit]
            
        except Exception as e:
            logger.error(f"Failed to list analyses from local storage: {str(e)}")
            return []
    
    async def store_strategy(
        self,
        user_id: str,
        strategy_name: str,
        strategy_code: str,
        parameters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_public: bool = False
    ) -> str:
        """
        Store generated strategy
        """
        try:
            storage = StrategyStorage(
                user_id=user_id,
                strategy_name=strategy_name,
                strategy_code=strategy_code,
                parameters=parameters or {},
                metadata=metadata or {},
                is_public=is_public,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            if self.use_supabase:
                return await self._store_strategy_supabase(storage)
            else:
                return await self._store_strategy_local(storage)
            
        except Exception as e:
            logger.error(f"Failed to store strategy: {str(e)}")
            raise
    
    async def _store_strategy_supabase(self, storage: StrategyStorage) -> str:
        """Store strategy in Supabase"""
        try:
            response = self.supabase.table('strategies').insert({
                'user_id': storage.user_id,
                'strategy_name': storage.strategy_name,
                'strategy_code': storage.strategy_code,
                'parameters': storage.parameters,
                'metadata': storage.metadata,
                'is_public': storage.is_public,
                'created_at': storage.created_at.isoformat(),
                'updated_at': storage.updated_at.isoformat()
            }).execute()
            
            if response.data:
                strategy_id = response.data[0]['id']
                logger.info(f"Strategy stored in Supabase: {strategy_id}")
                return strategy_id
            else:
                raise Exception("No data returned from Supabase")
                
        except Exception as e:
            logger.error(f"Supabase strategy storage failed: {str(e)}")
            return await self._store_strategy_local(storage)
    
    async def _store_strategy_local(self, storage: StrategyStorage) -> str:
        """Store strategy locally"""
        strategy_id = f"strategy_{storage.user_id}_{storage.strategy_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        storage.id = strategy_id
        
        # Save code file
        code_dir = self.local_storage_dir / "strategies" / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        
        code_filepath = code_dir / f"{strategy_id}.py"
        with open(code_filepath, 'w') as f:
            f.write(storage.strategy_code)
        
        # Save metadata
        metadata_dir = self.local_storage_dir / "strategies" / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_filepath = metadata_dir / f"{strategy_id}.json"
        with open(metadata_filepath, 'w') as f:
            json.dump(storage.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Strategy stored locally: {strategy_id}")
        return strategy_id
    
    async def store_chat_session(
        self,
        user_id: str,
        session_id: str,
        title: str,
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store chat session
        """
        try:
            storage = ChatSessionStorage(
                user_id=user_id,
                session_id=session_id,
                title=title,
                messages=messages,
                metadata=metadata or {},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            if self.use_supabase:
                return await self._store_chat_session_supabase(storage)
            else:
                return await self._store_chat_session_local(storage)
            
        except Exception as e:
            logger.error(f"Failed to store chat session: {str(e)}")
            raise
    
    async def _store_chat_session_supabase(self, storage: ChatSessionStorage) -> str:
        """Store chat session in Supabase"""
        try:
            response = self.supabase.table('chat_sessions').insert({
                'user_id': storage.user_id,
                'session_id': storage.session_id,
                'title': storage.title,
                'messages': storage.messages,
                'metadata': storage.metadata,
                'created_at': storage.created_at.isoformat(),
                'updated_at': storage.updated_at.isoformat()
            }).execute()
            
            if response.data:
                session_id = response.data[0]['id']
                logger.info(f"Chat session stored in Supabase: {session_id}")
                return session_id
            else:
                raise Exception("No data returned from Supabase")
                
        except Exception as e:
            logger.error(f"Supabase chat session storage failed: {str(e)}")
            return await self._store_chat_session_local(storage)
    
    async def _store_chat_session_local(self, storage: ChatSessionStorage) -> str:
        """Store chat session locally"""
        storage.id = f"chat_{storage.user_id}_{storage.session_id}"
        
        # Save to file
        filepath = self.local_storage_dir / f"chat_sessions/{storage.id}.json"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(storage.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Chat session stored locally: {storage.id}")
        return storage.id
    
    async def get_user_metrics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get user usage metrics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get all analyses for the user in the period
            analyses = await self.list_analyses(user_id, limit=1000)
            
            # Filter by date
            recent_analyses = []
            for analysis in analyses:
                try:
                    created_at = datetime.fromisoformat(analysis.get('created_at', ''))
                    if created_at >= cutoff_date:
                        recent_analyses.append(analysis)
                except Exception:
                    continue
            
            # Calculate metrics
            metrics = {
                'user_id': user_id,
                'period_days': days,
                'total_analyses': len(recent_analyses),
                'analysis_types': {},
                'daily_activity': {},
                'tokens_used': 0,
                'cost_estimate': 0.0
            }
            
            # Analyze by type
            for analysis in recent_analyses:
                analysis_type = analysis.get('analysis_type', 'unknown')
                metrics['analysis_types'][analysis_type] = metrics['analysis_types'].get(analysis_type, 0) + 1
                
                # Daily activity
                try:
                    created_at = datetime.fromisoformat(analysis.get('created_at', ''))
                    date_key = created_at.strftime('%Y-%m-%d')
                    metrics['daily_activity'][date_key] = metrics['daily_activity'].get(date_key, 0) + 1
                except Exception:
                    pass
                
                # Estimate tokens and cost
                metadata = analysis.get('metadata', {})
                tokens_used = metadata.get('tokens_used', 0)
                metrics['tokens_used'] += tokens_used
                
                # Rough cost estimation (placeholder)
                cost_per_token = 0.0001  # Adjust based on model pricing
                metrics['cost_estimate'] += tokens_used * cost_per_token
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get user metrics: {str(e)}")
            return {}
    
    async def cleanup_expired_data(self):
        """
        Clean up expired data
        """
        try:
            if self.use_supabase:
                await self._cleanup_expired_supabase()
            else:
                await self._cleanup_expired_local()
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {str(e)}")
    
    async def _cleanup_expired_supabase(self):
        """Cleanup expired data from Supabase"""
        try:
            # Delete expired analyses
            expired_analyses = self.supabase.table('ai_analyses').select('id').lt('expires_at', datetime.now().isoformat()).execute()
            
            if expired_analyses.data:
                ids_to_delete = [item['id'] for item in expired_analyses.data]
                self.supabase.table('ai_analyses').delete().in_('id', ids_to_delete).execute()
                
                logger.info(f"Cleaned up {len(ids_to_delete)} expired analyses from Supabase")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired Supabase data: {str(e)}")
    
    async def _cleanup_expired_local(self):
        """Cleanup expired data from local storage"""
        try:
            analyses_dir = self.local_storage_dir / "analyses"
            if not analyses_dir.exists():
                return
            
            expired_count = 0
            for filepath in analyses_dir.glob("*.json"):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    expires_at = data.get('expires_at')
                    if expires_at:
                        expires_datetime = datetime.fromisoformat(expires_at)
                        if expires_datetime < datetime.now():
                            filepath.unlink()
                            expired_count += 1
                            
                except Exception:
                    continue  # Skip corrupted files
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired analyses from local storage")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired local data: {str(e)}")
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all user data for GDPR compliance
        """
        try:
            export_data = {
                'user_id': user_id,
                'exported_at': datetime.now().isoformat(),
                'analyses': await self.list_analyses(user_id, limit=10000),
                'strategies': [],  # Would implement similar listing for strategies
                'chat_sessions': []  # Would implement similar listing for chat sessions
            }
            
            # In a real implementation, you'd also get strategies and chat sessions
            # For now, just return analyses
            
            logger.info(f"Exported data for user {user_id}")
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export user data: {str(e)}")
            raise
    
    async def delete_user_data(self, user_id: str) -> bool:
        """
        Delete all user data (GDPR right to be forgotten)
        """
        try:
            if self.use_supabase:
                return await self._delete_user_data_supabase(user_id)
            else:
                return await self._delete_user_data_local(user_id)
                
        except Exception as e:
            logger.error(f"Failed to delete user data: {str(e)}")
            return False
    
    async def _delete_user_data_supabase(self, user_id: str) -> bool:
        """Delete user data from Supabase"""
        try:
            # Delete all user data from relevant tables
            tables = ['ai_analyses', 'strategies', 'chat_sessions', 'optimization_results']
            
            for table in tables:
                self.supabase.table(table).delete().eq('user_id', user_id).execute()
            
            logger.info(f"Deleted all data for user {user_id} from Supabase")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user data from Supabase: {str(e)}")
            return False
    
    async def _delete_user_data_local(self, user_id: str) -> bool:
        """Delete user data from local storage"""
        try:
            # Delete analysis files
            analyses_dir = self.local_storage_dir / "analyses"
            deleted_count = 0
            
            if analyses_dir.exists():
                for filepath in analyses_dir.glob("*.json"):
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        
                        if data.get('user_id') == user_id:
                            filepath.unlink()
                            deleted_count += 1
                    except Exception:
                        continue
            
            logger.info(f"Deleted {deleted_count} files for user {user_id} from local storage")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user data from local storage: {str(e)}")
            return False


# Global storage manager instance
_storage_manager: Optional[StorageManager] = None


def get_storage_manager() -> StorageManager:
    """Get or create global storage manager"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager


def main():
    """
    Test function for storage manager
    """
    async def test_storage():
        storage = get_storage_manager()
        
        # Test storing analysis
        analysis_id = await storage.store_analysis(
            user_id="test_user",
            analysis_type="market_analysis",
            data={
                "symbol": "BTC/USDT",
                "analysis": "bullish",
                "confidence": 0.85
            },
            metadata={"model": "claude-3-sonnet", "tokens": 1500}
        )
        
        print(f"Stored analysis: {analysis_id}")
        
        # Test retrieving analysis
        retrieved = await storage.get_analysis(analysis_id, "test_user")
        print(f"Retrieved analysis: {retrieved is not None}")
        
        # Test listing analyses
        analyses = await storage.list_analyses("test_user")
        print(f"Total analyses: {len(analyses)}")
        
        # Test user metrics
        metrics = await storage.get_user_metrics("test_user")
        print(f"User metrics: {metrics}")
    
    asyncio.run(test_storage())


if __name__ == "__main__":
    main()
