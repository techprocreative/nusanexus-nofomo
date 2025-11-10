"""
Configuration settings for NusaNexus NoFOMO
"""

from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # App settings
    app_name: str = "NusaNexus NoFOMO API"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # API settings
    api_v1_str: str = "/api/v1"
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # CORS settings - comma separated list of origins
    allowed_origins: str = "http://localhost:3000"
    allowed_hosts: str = "localhost,*.nusafxtrade.com,*.onrender.com"
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins.split(',')]
    
    @property
    def trusted_hosts(self) -> List[str]:
        """Parse allowed hosts from comma-separated string"""
        return [host.strip() for host in self.allowed_hosts.split(',')]
    
    # Supabase settings
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    
    # OpenRouter AI settings
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Exchange API settings (encrypted storage)
    binance_api_url: str = "https://api.binance.com"
    bybit_api_url: str = "https://api.bybit.com"
    
    # Tripay billing settings
    tripay_api_key: Optional[str] = None
    tripay_merchant_code: Optional[str] = None
    tripay_private_key: Optional[str] = None
    
    # Sentry for monitoring
    sentry_dsn: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()