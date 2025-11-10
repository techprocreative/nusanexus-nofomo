"""
Exchange service for Binance and Bybit API integration
"""

from typing import Dict, Any, Optional
import aiohttp
import hmac
import hashlib
import time
import structlog
from app.core.config import settings
from app.services.encryption import get_encryption_service

logger = structlog.get_logger()


class ExchangeService:
    """Service for interacting with exchange APIs"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.encryption_service = get_encryption_service()
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None


class BinanceService(ExchangeService):
    """Binance exchange service"""
    
    def __init__(self):
        super().__init__()
        self.base_url = settings.binance_api_url
        self.session = None
    
    def _generate_signature(self, data: str, secret_key: str) -> str:
        """Generate HMAC SHA256 signature"""
        return hmac.new(
            secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def get_account_info(self, api_key: str, api_secret: str, is_testnet: bool = False) -> Dict[str, Any]:
        """Get account information"""
        try:
            session = await self._get_session()
            
            timestamp = int(time.time() * 1000)
            params = f"timestamp={timestamp}"
            signature = self._generate_signature(params, api_secret)
            
            headers = {
                'X-MBX-APIKEY': api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            url = f"{self.base_url}/api/v3/account"
            async with session.get(
                f"{url}?{params}&signature={signature}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Binance API error: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error("Failed to get Binance account info", error=str(e))
            raise
    
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information"""
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/api/v3/exchangeInfo"
            async with session.get(f"{url}?symbol={symbol}") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('symbols', [{}])[0]
                else:
                    raise Exception(f"Failed to get symbol info: {response.status}")
                    
        except Exception as e:
            logger.error("Failed to get Binance symbol info", symbol=symbol, error=str(e))
            raise
    
    async def place_order(self, api_key: str, api_secret: str, symbol: str, side: str, 
                         order_type: str, quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Place an order"""
        try:
            session = await self._get_session()
            
            timestamp = int(time.time() * 1000)
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
                'timestamp': timestamp
            }
            
            if price and order_type == 'LIMIT':
                params['price'] = price
                params['timeInForce'] = 'GTC'
            
            # Create query string
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = self._generate_signature(query_string, api_secret)
            
            headers = {
                'X-MBX-APIKEY': api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            url = f"{self.base_url}/api/v3/order"
            async with session.post(
                f"{url}?{query_string}&signature={signature}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Binance order error: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error("Failed to place Binance order", symbol=symbol, error=str(e))
            raise
    
    async def get_order_status(self, api_key: str, api_secret: str, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status"""
        try:
            session = await self._get_session()
            
            timestamp = int(time.time() * 1000)
            params = f"symbol={symbol}&orderId={order_id}&timestamp={timestamp}"
            signature = self._generate_signature(params, api_secret)
            
            headers = {
                'X-MBX-APIKEY': api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            url = f"{self.base_url}/api/v3/order"
            async with session.get(
                f"{url}?{params}&signature={signature}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get order status: {response.status}")
                    
        except Exception as e:
            logger.error("Failed to get Binance order status", symbol=symbol, order_id=order_id, error=str(e))
            raise


class BybitService(ExchangeService):
    """Bybit exchange service"""
    
    def __init__(self):
        super().__init__()
        self.base_url = settings.bybit_api_url
        self.session = None
    
    def _generate_signature(self, data: str, secret_key: str) -> str:
        """Generate HMAC SHA256 signature"""
        return hmac.new(
            secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def get_wallet_balance(self, api_key: str, api_secret: str) -> Dict[str, Any]:
        """Get wallet balance"""
        try:
            session = await self._get_session()
            
            timestamp = str(int(time.time() * 1000))
            params = f"api_key={api_key}&timestamp={timestamp}"
            signature = self._generate_signature(params, api_secret)
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/v5/account/wallet-balance"
            async with session.get(
                f"{url}?{params}&sign={signature}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Bybit API error: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error("Failed to get Bybit wallet balance", error=str(e))
            raise


# Global exchange services
binance_service: Optional[BinanceService] = None
bybit_service: Optional[BybitService] = None


def get_binance_service() -> BinanceService:
    """Get Binance service instance"""
    global binance_service
    if binance_service is None:
        binance_service = BinanceService()
    return binance_service


def get_bybit_service() -> BybitService:
    """Get Bybit service instance"""
    global bybit_service
    if bybit_service is None:
        bybit_service = BybitService()
    return bybit_service