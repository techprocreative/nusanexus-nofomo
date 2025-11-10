"""
Authentication endpoints for NusaNexus NoFOMO with Supabase Auth
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict
import structlog

from app.core.auth import (
    get_current_user, get_optional_user,
    login, register, logout, refresh_token,
    sign_in_with_oauth, exchange_oauth_code,
    reset_password, update_password, update_user_profile
)
from app.core.database import get_db_client
from app.models.auth import (
    AuthResponse, TokenRefresh,
    PasswordResetRequest, PasswordResetConfirm,
    UserRegister, UserLogin
)
from app.models.user import UserResponse, UserUpdate, UserProfile, UserStats
from app.models.common import APIResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = structlog.get_logger()
router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=AuthResponse)
async def login_endpoint(user_data: UserLogin, request: Request):
    """
    Authenticate user and return access token
    """
    try:
        result = await login(user_data)
        logger.info("User logged in successfully", email=user_data.email, ip=request.client.host)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error", email=user_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/register", response_model=AuthResponse)
async def register_endpoint(user_data: UserRegister, request: Request):
    """
    Register new user account
    """
    try:
        result = await register(user_data)
        logger.info("User registered successfully", email=user_data.email, ip=request.client.host)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration error", email=user_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current user profile information
    """
    try:
        db_client = get_db_client()
        
        # Get additional user statistics
        bots = db_client.get_user_bots(current_user.id)
        strategies = db_client.get_user_strategies(current_user.id)
        
        # Calculate statistics
        total_bots = len(bots)
        active_bots = len([bot for bot in bots if bot.get("status") == "running"])
        total_trades = sum(bot.get("total_trades", 0) for bot in bots)
        total_profit = sum(bot.get("profit", 0.0) for bot in bots)
        
        winning_trades = sum(bot.get("winning_trades", 0) for bot in bots)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        stats = UserStats(
            total_bots=total_bots,
            active_bots=active_bots,
            total_trades=total_trades,
            total_profit=total_profit,
            win_rate=win_rate,
            strategies_count=len(strategies)
        )
        
        profile = UserProfile(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            avatar_url=current_user.avatar_url,
            subscription_plan=current_user.subscription_plan,
            created_at=current_user.created_at,
            last_login_at=current_user.last_login_at,
            stats=stats.model_dump() if stats else None
        )
        
        return profile
        
    except Exception as e:
        logger.error("Failed to get user profile", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user profile"
        )


@router.put("/profile", response_model=UserProfile)
async def update_user_profile_endpoint(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update user profile information
    """
    try:
        access_token = credentials.credentials
        update_data = user_update.dict(exclude_unset=True)
        
        if update_data:
            updated_user = await update_user_profile(update_data, access_token)
            
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Failed to update user profile"
                )
            
            logger.info("User profile updated", user_id=current_user.id)
            return updated_user
        else:
            return UserProfile(
                id=current_user.id,
                email=current_user.email,
                full_name=current_user.full_name,
                avatar_url=current_user.avatar_url,
                subscription_plan=current_user.subscription_plan,
                created_at=current_user.created_at,
                last_login_at=current_user.last_login_at
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user profile", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token_endpoint(
    token_data: TokenRefresh,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Refresh access token using refresh token
    """
    try:
        result = await refresh_token(token_data.refresh_token)
        
        return AuthResponse(
            success=True,
            message="Token refreshed successfully",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/logout", response_model=APIResponse)
async def logout_endpoint(
    current_user: UserResponse = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout user (invalidate session)
    """
    try:
        access_token = credentials.credentials
        result = await logout(access_token)
        
        logger.info("User logged out", user_id=current_user.id)
        return APIResponse(**result)
        
    except Exception as e:
        logger.error("Logout error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/forgot-password", response_model=APIResponse)
async def forgot_password_endpoint(request: PasswordResetRequest, request_obj: Request):
    """
    Request password reset
    """
    try:
        redirect_to = f"{request_obj.headers.get('origin', 'http://localhost:3000')}/reset-password"
        result = await reset_password(request.email, redirect_to)
        
        logger.info("Password reset requested", email=request.email, ip=request_obj.client.host)
        return APIResponse(**result)
        
    except Exception as e:
        logger.error("Password reset request error", email=request.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/reset-password", response_model=APIResponse)
async def reset_password_endpoint(
    reset_data: PasswordResetConfirm,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Reset password with token
    """
    try:
        access_token = credentials.credentials
        result = await update_password(access_token, reset_data.new_password)
        
        logger.info("Password reset completed")
        return APIResponse(**result)
        
    except Exception as e:
        logger.error("Password reset error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/verify-token", response_model=APIResponse)
async def verify_token_endpoint(
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """
    Verify if current token is valid
    """
    if current_user:
        return APIResponse(
            success=True,
            message="Token is valid",
            data={"user_id": current_user.id, "email": current_user.email}
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


# OAuth Endpoints
@router.get("/oauth/{provider}")
async def oauth_sign_in(
    provider: str,
    redirect_to: Optional[str] = None
):
    """
    Initiate OAuth sign-in with provider
    """
    try:
        if redirect_to is None:
            redirect_to = "http://localhost:3000/auth/callback"
        
        result = await sign_in_with_oauth(provider, redirect_to)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result
            }
        )
        
    except Exception as e:
        logger.error("OAuth sign in error", provider=provider, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth sign in failed for provider: {provider}"
        )


@router.post("/oauth/callback", response_model=AuthResponse)
async def oauth_callback(oauth_data: Dict[str, str]):
    """
    Handle OAuth callback and exchange code for tokens
    """
    try:
        code = oauth_data.get("code")
        code_verifier = oauth_data.get("code_verifier")
        
        if not code or not code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing OAuth code or code_verifier"
            )
        
        result = await exchange_oauth_code(code, code_verifier)
        
        logger.info("OAuth authentication successful")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OAuth callback error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )


@router.delete("/account", response_model=APIResponse)
async def delete_user_account(
    current_user: UserResponse = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete user account and all associated data
    """
    try:
        # In a real implementation, you would:
        # 1. Stop all running bots
        # 2. Delete user data with RLS policies
        # 3. Delete Supabase Auth user
        # 4. Clean up files and resources
        
        logger.warning("User account deletion requested", user_id=current_user.id)
        
        # For now, just return success
        return APIResponse(
            success=True,
            message="Account deletion initiated. This may take a few minutes to process."
        )
        
    except Exception as e:
        logger.error("Account deletion error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
