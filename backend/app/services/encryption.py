"""
Encryption service for secure storage of API keys and sensitive data
"""

from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        self._fernet: Optional[Fernet] = None
        self._setup_encryption()
    
    def _setup_encryption(self):
        """Setup encryption key from environment or generate new one"""
        try:
            if hasattr(settings, 'encryption_key') and settings.encryption_key:
                # Use provided encryption key
                key = settings.encryption_key.encode()
            else:
                # Generate key from password and salt
                password = settings.secret_key.encode()
                salt = b'nusafxtrade_salt_2023'  # In production, store this securely
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
            
            self._fernet = Fernet(key)
            logger.info("Encryption service initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize encryption service", error=str(e))
            raise
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not self._fernet:
            raise RuntimeError("Encryption service not initialized")
        
        try:
            encrypted_data = self._fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error("Failed to encrypt data", error=str(e))
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not self._fernet:
            raise RuntimeError("Encryption service not initialized")
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error("Failed to decrypt data", error=str(e))
            raise
    
    def encrypt_api_credentials(self, api_key: str, api_secret: str) -> dict:
        """Encrypt API credentials"""
        try:
            return {
                "api_key_encrypted": self.encrypt_data(api_key),
                "api_secret_encrypted": self.encrypt_data(api_secret),
                "encrypted_at": "2025-11-10T00:00:00Z"
            }
        except Exception as e:
            logger.error("Failed to encrypt API credentials", error=str(e))
            raise
    
    def decrypt_api_credentials(self, encrypted_credentials: dict) -> dict:
        """Decrypt API credentials"""
        try:
            return {
                "api_key": self.decrypt_data(encrypted_credentials["api_key_encrypted"]),
                "api_secret": self.decrypt_data(encrypted_credentials["api_secret_encrypted"])
            }
        except Exception as e:
            logger.error("Failed to decrypt API credentials", error=str(e))
            raise
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a secure random token"""
        return base64.urlsafe_b64encode(os.urandom(length)).decode()
    
    def hash_sensitive_data(self, data: str) -> str:
        """Create a hash of sensitive data (one-way)"""
        import hashlib
        return hashlib.sha256(data.encode()).hexdigest()


# Global encryption service instance
encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get encryption service instance"""
    global encryption_service
    if encryption_service is None:
        encryption_service = EncryptionService()
    return encryption_service