"""
Services package for NusaNexus NoFOMO
"""

from .ai_service import AIService
from .other_services import BotService, ExchangeService, EncryptionService, NotificationService

# Service factory functions
def get_ai_service() -> AIService:
    """Get AI service instance"""
    return AIService()

def get_bot_service() -> BotService:
    """Get bot service instance"""
    return BotService()

def get_exchange_service() -> ExchangeService:
    """Get exchange service instance"""
    return ExchangeService()

def get_encryption_service() -> EncryptionService:
    """Get encryption service instance"""
    return EncryptionService()

def get_notification_service() -> NotificationService:
    """Get notification service instance"""
    return NotificationService()