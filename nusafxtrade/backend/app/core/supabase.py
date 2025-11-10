"""
Supabase client configuration and utilities for NusaNexus NoFOMO
"""

from typing import Optional, Dict, Any
from supabase import create_client, Client
import structlog

from .config import settings

logger = structlog.get_logger()


class SupabaseClient:
    """Supabase client wrapper with authentication and database utilities"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._service_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get authenticated client (with user token)"""
        if self._client is None:
            raise ValueError("Client not initialized. Call init() first.")
        return self._client
    
    @property
    def service_client(self) -> Client:
        """Get service role client (admin access)"""
        if self._service_client is None:
            raise ValueError("Service client not initialized. Call init() first.")
        return self._service_client
    
    def init(self, access_token: Optional[str] = None):
        """Initialize Supabase clients"""
        try:
            # Regular client (for authenticated requests)
            if access_token:
                self._client = create_client(
                    supabase_url=settings.supabase_url,
                    supabase_key=settings.supabase_key,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
            else:
                self._client = create_client(
                    supabase_url=settings.supabase_url,
                    supabase_key=settings.supabase_key
                )
            
            # Service role client (for admin operations)
            self._service_client = create_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_service_role_key
            )
            
            logger.info("Supabase clients initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Supabase clients", error=str(e))
            raise
    
    def reset(self):
        """Reset clients (for logout)"""
        self._client = None
        self._service_client = None
        logger.info("Supabase clients reset")


# Global client instance
supabase_client = SupabaseClient()


class AuthService:
    """Supabase authentication service"""
    
    def __init__(self):
        self.client = supabase_client.service_client
    
    async def register_user(
        self, 
        email: str, 
        password: str, 
        full_name: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register a new user with Supabase Auth"""
        try:
            user_metadata = {
                "full_name": full_name,
                **(metadata or {})
            }
            
            result = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })
            
            if result.user and result.session:
                return {
                    "user": {
                        "id": result.user.id,
                        "email": result.user.email,
                        "full_name": result.user.user_metadata.get("full_name"),
                        "email_confirmed_at": result.user.email_confirmed_at,
                        "created_at": result.user.created_at,
                        "updated_at": result.user.updated_at,
                    },
                    "access_token": result.session.access_token,
                    "refresh_token": result.session.refresh_token,
                    "expires_at": result.session.expires_at
                }
            else:
                logger.error("User registration failed - no user or session")
                return None
                
        except Exception as e:
            logger.error("User registration error", email=email, error=str(e))
            return None
    
    async def authenticate_user(
        self, 
        email: str, 
        password: str
    ) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        try:
            result = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if result.user and result.session:
                return {
                    "user": {
                        "id": result.user.id,
                        "email": result.user.email,
                        "full_name": result.user.user_metadata.get("full_name"),
                        "email_confirmed_at": result.user.email_confirmed_at,
                        "created_at": result.user.created_at,
                        "updated_at": result.user.updated_at,
                    },
                    "access_token": result.session.access_token,
                    "refresh_token": result.session.refresh_token,
                    "expires_at": result.session.expires_at
                }
            else:
                logger.error("User authentication failed - no user or session")
                return None
                
        except Exception as e:
            logger.error("User authentication error", email=email, error=str(e))
            return None
    
    async def sign_in_with_oauth(
        self, 
        provider: str, 
        redirect_to: str = None
    ) -> Dict[str, Any]:
        """Sign in with OAuth provider (Google, GitHub, Discord)"""
        try:
            result = self.client.auth.sign_in_with_oauth({
                "provider": provider,
                "options": {
                    "redirectTo": redirect_to
                }
            })
            
            return {
                "url": result.url,
                "code_challenge": result.code_challenge,
                "code_verifier": result.code_verifier
            }
            
        except Exception as e:
            logger.error("OAuth sign in error", provider=provider, error=str(e))
            return None
    
    async def exchange_oauth_code(
        self, 
        code: str, 
        code_verifier: str
    ) -> Dict[str, Any]:
        """Exchange OAuth code for session"""
        try:
            result = self.client.auth.exchange_code_for_session(
                code=code,
                code_verifier=code_verifier
            )
            
            if result.user and result.session:
                return {
                    "user": {
                        "id": result.user.id,
                        "email": result.user.email,
                        "full_name": result.user.user_metadata.get("full_name"),
                        "email_confirmed_at": result.user.email_confirmed_at,
                        "created_at": result.user.created_at,
                        "updated_at": result.user.updated_at,
                    },
                    "access_token": result.session.access_token,
                    "refresh_token": result.session.refresh_token,
                    "expires_at": result.session.expires_at
                }
            else:
                return None
                
        except Exception as e:
            logger.error("OAuth code exchange error", error=str(e))
            return None
    
    async def refresh_token(
        self, 
        refresh_token: str
    ) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            result = self.client.auth.refresh_session(refresh_token)
            
            if result.user and result.session:
                return {
                    "user": {
                        "id": result.user.id,
                        "email": result.user.email,
                        "full_name": result.user.user_metadata.get("full_name"),
                        "email_confirmed_at": result.user.email_confirmed_at,
                        "created_at": result.user.created_at,
                        "updated_at": result.user.updated_at,
                    },
                    "access_token": result.session.access_token,
                    "refresh_token": result.session.refresh_token,
                    "expires_at": result.session.expires_at
                }
            else:
                return None
                
        except Exception as e:
            logger.error("Token refresh error", error=str(e))
            return None
    
    async def get_user(self, access_token: str) -> Dict[str, Any]:
        """Get current user from access token"""
        try:
            result = self.client.auth.get_user(access_token)
            
            if result.user:
                return {
                    "id": result.user.id,
                    "email": result.user.email,
                    "full_name": result.user.user_metadata.get("full_name"),
                    "email_confirmed_at": result.user.email_confirmed_at,
                    "created_at": result.user.created_at,
                    "updated_at": result.user.updated_at,
                }
            else:
                return None
                
        except Exception as e:
            logger.error("Get user error", error=str(e))
            return None
    
    async def update_user(
        self, 
        access_token: str, 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user information"""
        try:
            result = self.client.auth.update_user(updates, access_token)
            
            if result.user:
                return {
                    "id": result.user.id,
                    "email": result.user.email,
                    "full_name": result.user.user_metadata.get("full_name"),
                    "email_confirmed_at": result.user.email_confirmed_at,
                    "created_at": result.user.created_at,
                    "updated_at": result.user.updated_at,
                }
            else:
                return None
                
        except Exception as e:
            logger.error("Update user error", error=str(e))
            return None
    
    async def sign_out(self, access_token: str) -> bool:
        """Sign out user (invalidate session)"""
        try:
            result = self.client.auth.sign_out(access_token)
            return result is not None
            
        except Exception as e:
            logger.error("Sign out error", error=str(e))
            return False
    
    async def reset_password(
        self, 
        email: str, 
        redirect_to: str = None
    ) -> bool:
        """Send password reset email"""
        try:
            result = self.client.auth.reset_password_email(
                email, 
                redirect_to=redirect_to
            )
            return result is not None
            
        except Exception as e:
            logger.error("Password reset error", email=email, error=str(e))
            return False
    
    async def update_password(
        self, 
        access_token: str, 
        new_password: str
    ) -> bool:
        """Update user password"""
        try:
            result = self.client.auth.update_user(
                {"password": new_password}, 
                access_token
            )
            return result is not None
            
        except Exception as e:
            logger.error("Update password error", error=str(e))
            return False


# Global auth service instance
auth_service = AuthService()


# Helper functions for dependency injection
def get_supabase_client(access_token: Optional[str] = None) -> SupabaseClient:
    """Get Supabase client for dependency injection"""
    if access_token:
        supabase_client.init(access_token=access_token)
    return supabase_client


def get_auth_service() -> AuthService:
    """Get auth service for dependency injection"""
    return auth_service