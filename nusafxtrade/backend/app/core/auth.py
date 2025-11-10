"""
Authentication middleware and dependencies for NusaNexus NoFOMO
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import structlog

from app.core.database import get_db_client
from app.core.supabase import get_auth_service, supabase_client
from app.models.user import UserResponse, UserLogin, UserRegister
from app.models.auth import Token, AuthResponse

logger = structlog.get_logger()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    """
    Get current authenticated user from JWT token using Supabase Auth
    """
    try:
        token = credentials.credentials
        
        # Initialize Supabase client with the access token
        supabase_client.init(access_token=token)
        
        # Get user from Supabase Auth
        auth_service = get_auth_service()
        user_data = await auth_service.get_user(token)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create UserResponse from Supabase user data
        user = UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            subscription_plan="free",  # Default subscription plan
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at")
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserResponse]:
    """
    Get current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def require_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Dependency that requires authenticated user
    """
    return current_user


async def require_subscription(
    min_plan: str = "free",
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Check user subscription level
    """
    plan_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
    user_plan_level = plan_hierarchy.get(current_user.subscription_plan, 0)
    required_plan_level = plan_hierarchy.get(min_plan, 0)
    
    if user_plan_level < required_plan_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Subscription level '{min_plan}' or higher required"
        )
    
    return current_user


# Authentication service functions (legacy compatibility)
async def login(credentials: UserLogin) -> AuthResponse:
    """Login endpoint using Supabase Auth"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.authenticate_user(
            email=credentials.email,
            password=credentials.password
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_data = result["user"]
        user = UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            subscription_plan="free",
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at")
        )
        
        return AuthResponse(
            success=True,
            message="Login successful",
            data=Token(
                access_token=result["access_token"],
                expires_in=3600,
                user=user
            )
        )
    except Exception as e:
        logger.error("Login error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def register(user_data: UserRegister) -> AuthResponse:
    """Registration endpoint using Supabase Auth"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed. Email may already be in use."
            )
        
        user_data = result["user"]
        user = UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            subscription_plan="free",
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at")
        )
        
        return AuthResponse(
            success=True,
            message="Registration successful",
            data=Token(
                access_token=result["access_token"],
                expires_in=3600,
                user=user
            )
        )
    except Exception as e:
        logger.error("Registration error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def logout(access_token: str) -> Dict[str, Any]:
    """Logout endpoint - invalidate session using Supabase Auth"""
    try:
        auth_service = get_auth_service()
        success = await auth_service.sign_out(access_token)
        
        # Reset client state
        supabase_client.reset()
        
        if success:
            return {
                "success": True,
                "message": "Logged out successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )
    except Exception as e:
        logger.error("Logout error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def refresh_token(
    refresh_token: str
) -> Token:
    """Refresh access token using Supabase Auth"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.refresh_token(refresh_token)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_data = result["user"]
        user = UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            subscription_plan="free",
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at")
        )
        
        return Token(
            access_token=result["access_token"],
            expires_in=3600,
            user=user
        )
    except Exception as e:
        logger.error("Token refresh error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# OAuth providers
async def sign_in_with_oauth(provider: str, redirect_to: str = None) -> Dict[str, Any]:
    """Sign in with OAuth provider (Google, GitHub, Discord)"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.sign_in_with_oauth(
            provider=provider,
            redirect_to=redirect_to
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth sign in failed for provider: {provider}"
            )
        
        return result
    except Exception as e:
        logger.error("OAuth sign in error", provider=provider, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def exchange_oauth_code(
    code: str,
    code_verifier: str
) -> AuthResponse:
    """Exchange OAuth code for session"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.exchange_oauth_code(
            code=code,
            code_verifier=code_verifier
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth code exchange failed"
            )
        
        user_data = result["user"]
        user = UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            subscription_plan="free",
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at")
        )
        
        return AuthResponse(
            success=True,
            message="OAuth authentication successful",
            data=Token(
                access_token=result["access_token"],
                expires_in=3600,
                user=user
            )
        )
    except Exception as e:
        logger.error("OAuth code exchange error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Password reset
async def reset_password(email: str, redirect_to: str = None) -> Dict[str, Any]:
    """Send password reset email using Supabase Auth"""
    try:
        auth_service = get_auth_service()
        success = await auth_service.reset_password(
            email=email,
            redirect_to=redirect_to
        )
        
        if success:
            return {
                "success": True,
                "message": "Password reset instructions sent to your email"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email"
            )
    except Exception as e:
        logger.error("Password reset error", email=email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def update_password(
    access_token: str,
    new_password: str
) -> Dict[str, Any]:
    """Update user password using Supabase Auth"""
    try:
        auth_service = get_auth_service()
        success = await auth_service.update_password(
            access_token=access_token,
            new_password=new_password
        )
        
        if success:
            return {
                "success": True,
                "message": "Password updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
    except Exception as e:
        logger.error("Update password error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# User profile endpoints
async def get_user_profile(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Get current user profile"""
    return current_user


async def update_user_profile(
    profile_data: Dict[str, Any],
    access_token: str
) -> UserResponse:
    """Update user profile in Supabase Auth"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.update_user(access_token, profile_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )
        
        user = UserResponse(
            id=result["id"],
            email=result["email"],
            full_name=result.get("full_name"),
            subscription_plan="free",
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at")
        )
        
        return user
    except Exception as e:
        logger.error("Update user profile error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Permission checking helpers
async def check_bot_access(
    bot_id: str,
    user: UserResponse = Depends(get_current_user)
) -> bool:
    """Check if user has access to a specific bot"""
    try:
        db_client = get_db_client()
        bot = db_client.get_bot_by_id(bot_id, user.id)
        return bot is not None
    except Exception:
        return False


async def check_strategy_access(
    strategy_id: str,
    user: UserResponse = Depends(get_current_user)
) -> bool:
    """Check if user has access to a specific strategy"""
    try:
        db_client = get_db_client()
        strategy = db_client.get_strategy_by_id(strategy_id)
        
        if not strategy:
            return False
        
        # User can access if they own it or it's public
        return strategy.get("user_id") == user.id or strategy.get("is_public", False)
    except Exception:
        return False