"""
Authentication Pydantic models for NusaNexus NoFOMO
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from .user import UserResponse


# Token Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    exp: Optional[int] = None


# Authentication Response
class AuthResponse(BaseModel):
    success: bool = True
    message: str
    data: Token


# Authentication Error
class AuthError(BaseModel):
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Password Reset Models
class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


# Token Refresh
class TokenRefresh(BaseModel):
    refresh_token: str


# Session Management
class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    device_info: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    is_active: bool = True


# API Key Management
class APIKey(BaseModel):
    id: str
    user_id: str
    name: str
    key_prefix: str  # First few characters for identification
    permissions: Dict[str, Any]
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime


class APIKeyCreate(BaseModel):
    name: str
    permissions: Dict[str, Any]
    expires_at: Optional[datetime] = None


# Two-Factor Authentication
class TwoFactorSetup(BaseModel):
    secret: str
    qr_code_url: str
    backup_codes: List[str]


class TwoFactorVerify(BaseModel):
    code: str
    backup_code: Optional[str] = None


# OAuth Models
class OAuthProvider(BaseModel):
    provider: str  # google, github, etc.
    client_id: str
    client_secret: str
    redirect_uri: str


class OAuthCallback(BaseModel):
    provider: str
    code: str
    state: Optional[str] = None


# Security Models
class SecuritySettings(BaseModel):
    two_factor_enabled: bool = False
    session_timeout: int = 24  # hours
    allow_multiple_sessions: bool = True
    require_email_verification: bool = True
    password_expires_days: Optional[int] = None
    login_notifications: bool = True


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LoginAttempt(BaseModel):
    ip_address: str
    user_agent: str
    success: bool
    failure_reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=_utcnow)
