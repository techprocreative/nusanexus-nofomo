"""
User Pydantic models for NusaNexus NoFOMO
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum


class SubscriptionPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Base User Model
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    avatar_url: Optional[str] = None
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    preferences: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


# User Response Model
class UserResponse(UserBase):
    id: str
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# User with Exchange Credentials
class UserWithCredentials(UserResponse):
    exchange_credentials: Optional[Dict[str, Any]] = None


# User Update Model
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


# User Registration Model
class UserRegister(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


# User Login Model
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


# User Profile Response
class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str]
    subscription_plan: str
    created_at: datetime
    last_login_at: Optional[datetime] = None
    stats: Optional[Dict[str, Any]] = None


# User Statistics
class UserStats(BaseModel):
    total_bots: int = 0
    active_bots: int = 0
    total_trades: int = 0
    total_profit: float = 0.0
    win_rate: float = 0.0
    strategies_count: int = 0


# User Preferences
class UserPreferences(BaseModel):
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    notifications: Dict[str, bool] = Field(default_factory=lambda: {
        "email": True,
        "push": True,
        "bot_alerts": True,
        "trade_alerts": True,
        "ai_insights": True
    })
    trading_defaults: Dict[str, Any] = Field(default_factory=dict)
    dashboard_layout: Optional[Dict[str, Any]] = None
