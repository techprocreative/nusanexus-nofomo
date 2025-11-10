"""
NusaNexus NoFOMO - Exchange Handler
Manages exchange API integrations and authentication
"""

import os
import asyncio
import json
from typing import Dict, Any, Optional, List
import ccxt
import redis
from supabase import create_client, Client
import structlog

logger = structlog.get_logger(__name__)


class ExchangeHandler:
    """
    Exchange API Handler for managing trading operations
    
    Responsibilities:
    - Exchange API authentication and validation
    - Market data retrieval
    - Order placement and management
    - Balance and account information
    - Connection pooling and rate limiting
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Exchange instances cache
        self.exchange_instances: Dict[str, ccxt.Exchange] = {}
        self.exchange_configs: Dict[str, Dict[str, Any]] = {}
        
        # Rate limiting
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        
        # Supported exchanges
        self.supported_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'coinbase']
        
        # Exchange-specific configurations
        self.exchange_settings = {
            'binance': {
                'rateLimit': 100,
                'max_retries': 3,
                'timeout': 30,
                'enableRateLimit': True
            },
            'bybit': {
                'rateLimit': 100,
                'max_retries': 3,
                'timeout': 30,
                'enableRateLimit': True
            },
            'kucoin': {
                'rateLimit': 100,
                'max_retries': 3,
                'timeout': 30,
                'enableRateLimit': True
            },
            'okx': {
                'rateLimit': 100,
                'max_retries': 3,
                'timeout': 30,
                'enableRateLimit': True
            },
            'coinbase': {
                'rateLimit': 100,
                'max_retries': 3,
                'timeout': 30,
                'enableRateLimit': True
            }
        }
        
        logger.info("Exchange Handler initialized")
    
    async def validate_exchange_config(self, exchange: str, user_id: str) -> bool:
        """
        Validate exchange configuration and credentials
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            
        Returns:
            Validation success status
        """
        try:
            # Get exchange credentials
            config = await self._get_exchange_config(exchange, user_id)
            if not config:
                return False
            
            # Test connection with public endpoints
            exchange_instance = await self._create_exchange_instance(exchange, config)
            if not exchange_instance:
                return False
            
            # Test public API
            try:
                markets = await asyncio.wait_for(
                    exchange_instance.load_markets(),
                    timeout=10
                )
                return len(markets) > 0
            except Exception as e:
                logger.error(f"Failed to load markets for {exchange}: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Exchange validation failed for {exchange}: {str(e)}")
            return False
    
    async def get_exchange_info(self, exchange: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get exchange information and capabilities
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            
        Returns:
            Exchange information dictionary
        """
        try:
            config = await self._get_exchange_config(exchange, user_id)
            if not config:
                return None
            
            exchange_instance = await self._create_exchange_instance(exchange, config)
            if not exchange_instance:
                return None
            
            info = {
                'name': exchange,
                'version': exchange_instance.version,
                'countries': getattr(exchange_instance, 'countries', []),
                'rateLimit': exchange_instance.rateLimit,
                'urls': getattr(exchange_instance, 'urls', {}),
                'has': {
                    'publicAPI': exchange_instance.has.get('publicAPI', False),
                    'privateAPI': exchange_instance.has.get('privateAPI', False),
                    'CORS': exchange_instance.has.get('CORS', False),
                    'fetchCurrencies': exchange_instance.has.get('fetchCurrencies', False),
                    'fetchTicker': exchange_instance.has.get('fetchTicker', False),
                    'fetchTickers': exchange_instance.has.get('fetchTickers', False),
                    'fetchOrderBook': exchange_instance.has.get('fetchOrderBook', False),
                    'fetchTrades': exchange_instance.has.get('fetchTrades', False),
                    'fetchOHLCV': exchange_instance.has.get('fetchOHLCV', False),
                    'fetchStatus': exchange_instance.has.get('fetchStatus', False),
                    'fetchTime': exchange_instance.has.get('fetchTime', False),
                    'fetchMarkets': exchange_instance.has.get('fetchMarkets', False),
                    'fetchBalance': exchange_instance.has.get('fetchBalance', False),
                    'createOrder': exchange_instance.has.get('createOrder', False),
                    'cancelOrder': exchange_instance.has.get('cancelOrder', False),
                    'cancelAllOrders': exchange_instance.has.get('cancelAllOrders', False),
                    'fetchOrder': exchange_instance.has.get('fetchOrder', False),
                    'fetchOrders': exchange_instance.has.get('fetchOrders', False),
                    'fetchOpenOrders': exchange_instance.has.get('fetchOpenOrders', False),
                    'fetchClosedOrders': exchange_instance.has.get('fetchClosedOrders', False),
                    'fetchMyTrades': exchange_instance.has.get('fetchMyTrades', False),
                    'fetchOrderTrades': exchange_instance.has.get('fetchOrderTrades', False),
                    'withdraw': exchange_instance.has.get('withdraw', False)
                },
                'timeframes': list(exchange_instance.timeframes.keys()) if hasattr(exchange_instance, 'timeframes') else []
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get exchange info for {exchange}: {str(e)}")
            return None
    
    async def get_market_data(self, exchange: str, symbol: str, user_id: str, 
                             data_type: str = 'ticker') -> Optional[Dict[str, Any]]:
        """
        Get market data for a symbol
        
        Args:
            exchange: Exchange name
            symbol: Trading symbol
            user_id: User identifier
            data_type: Type of data (ticker, orderbook, trades, ohlcv)
            
        Returns:
            Market data dictionary
        """
        try:
            config = await self._get_exchange_config(exchange, user_id)
            if not config:
                return None
            
            exchange_instance = await self._create_exchange_instance(exchange, config)
            if not exchange_instance:
                return None
            
            # Load markets if not already loaded
            if not exchange_instance.markets:
                await exchange_instance.load_markets()
            
            if symbol not in exchange_instance.markets:
                logger.error(f"Symbol {symbol} not found on {exchange}")
                return None
            
            market_data = {}
            
            if data_type == 'ticker' or data_type == 'all':
                try:
                    ticker = await asyncio.wait_for(
                        exchange_instance.fetch_ticker(symbol),
                        timeout=10
                    )
                    market_data['ticker'] = ticker
                except Exception as e:
                    logger.error(f"Failed to fetch ticker for {symbol}: {str(e)}")
            
            if data_type == 'orderbook' or data_type == 'all':
                try:
                    orderbook = await asyncio.wait_for(
                        exchange_instance.fetch_order_book(symbol),
                        timeout=10
                    )
                    market_data['orderbook'] = orderbook
                except Exception as e:
                    logger.error(f"Failed to fetch orderbook for {symbol}: {str(e)}")
            
            if data_type == 'trades' or data_type == 'all':
                try:
                    trades = await asyncio.wait_for(
                        exchange_instance.fetch_trades(symbol),
                        timeout=10
                    )
                    market_data['trades'] = trades[:50]  # Limit to 50 recent trades
                except Exception as e:
                    logger.error(f"Failed to fetch trades for {symbol}: {str(e)}")
            
            if data_type == 'ohlcv' or data_type == 'all':
                try:
                    ohlcv = await asyncio.wait_for(
                        exchange_instance.fetch_ohlcv(symbol, timeframe='1h', limit=24),
                        timeout=10
                    )
                    market_data['ohlcv'] = ohlcv
                except Exception as e:
                    logger.error(f"Failed to fetch OHLCV for {symbol}: {str(e)}")
            
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {str(e)}")
            return None
    
    async def get_balance(self, exchange: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get account balance
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            
        Returns:
            Balance information dictionary
        """
        try:
            config = await self._get_exchange_config(exchange, user_id)
            if not config:
                return None
            
            exchange_instance = await self._create_exchange_instance(exchange, config)
            if not exchange_instance:
                return None
            
            balance = await asyncio.wait_for(
                exchange_instance.fetch_balance(),
                timeout=10
            )
            
            # Filter out empty balances
            filtered_balance = {
                'info': balance.get('info', {}),
                'timestamp': balance.get('timestamp'),
                'datetime': balance.get('datetime'),
                'total': {},
                'free': {},
                'used': {}
            }
            
            for currency, balance_data in balance.items():
                if isinstance(balance_data, dict) and 'total' in balance_data:
                    if balance_data['total'] > 0:
                        filtered_balance['total'][currency] = balance_data['total']
                        filtered_balance['free'][currency] = balance_data.get('free', 0)
                        filtered_balance['used'][currency] = balance_data.get('used', 0)
            
            return filtered_balance
            
        except Exception as e:
            logger.error(f"Failed to get balance for {exchange}: {str(e)}")
            return None
    
    async def create_order(self, exchange: str, user_id: str, symbol: str, side: str, 
                          order_type: str, amount: float, price: float = None, 
                          params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Create a trading order
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            symbol: Trading symbol
            side: Order side ('buy' or 'sell')
            order_type: Order type ('market', 'limit', etc.)
            amount: Order amount
            price: Order price (for limit orders)
            params: Additional order parameters
            
        Returns:
            Order information dictionary
        """
        try:
            config = await self._get_exchange_config(exchange, user_id)
            if not config:
                return None
            
            exchange_instance = await self._create_exchange_instance(exchange, config)
            if not exchange_instance:
                return None
            
            # Load markets if not already loaded
            if not exchange_instance.markets:
                await exchange_instance.load_markets()
            
            # Prepare order parameters
            order_params = {
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'amount': amount
            }
            
            if price is not None:
                order_params['price'] = price
            
            if params:
                order_params.update(params)
            
            # Create order
            order = await asyncio.wait_for(
                exchange_instance.create_order(**order_params),
                timeout=30
            )
            
            logger.info(f"Created {order_type} {side} order for {symbol}: {order.get('id')}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            return None
    
    async def cancel_order(self, exchange: str, user_id: str, symbol: str, order_id: str) -> bool:
        """
        Cancel an order
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            symbol: Trading symbol
            order_id: Order identifier
            
        Returns:
            Cancellation success status
        """
        try:
            config = await self._get_exchange_config(exchange, user_id)
            if not config:
                return False
            
            exchange_instance = await self._create_exchange_instance(exchange, config)
            if not exchange_instance:
                return False
            
            await asyncio.wait_for(
                exchange_instance.cancel_order(order_id, symbol),
                timeout=10
            )
            
            logger.info(f"Cancelled order {order_id} for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            return False
    
    async def get_order_status(self, exchange: str, user_id: str, symbol: str, 
                              order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order status
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            symbol: Trading symbol
            order_id: Order identifier
            
        Returns:
            Order status dictionary
        """
        try:
            config = await self._get_exchange_config(exchange, user_id)
            if not config:
                return None
            
            exchange_instance = await self._create_exchange_instance(exchange, config)
            if not exchange_instance:
                return None
            
            order = await asyncio.wait_for(
                exchange_instance.fetch_order(order_id, symbol),
                timeout=10
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {str(e)}")
            return None
    
    async def get_open_orders(self, exchange: str, user_id: str, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Get open orders
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            symbol: Trading symbol (optional)
            
        Returns:
            List of open orders
        """
        try:
            config = await self._get_exchange_config(exchange, user_id)
            if not config:
                return []
            
            exchange_instance = await self._create_exchange_instance(exchange, config)
            if not exchange_instance:
                return []
            
            orders = await asyncio.wait_for(
                exchange_instance.fetch_open_orders(symbol),
                timeout=10
            )
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get open orders: {str(e)}")
            return []
    
    async def get_trade_history(self, exchange: str, user_id: str, symbol: str = None, 
                               limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get trade history
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            symbol: Trading symbol (optional)
            limit: Maximum number of trades
            
        Returns:
            List of trades
        """
        try:
            config = await self._get_exchange_config(exchange, user_id)
            if not config:
                return []
            
            exchange_instance = await self._create_exchange_instance(exchange, config)
            if not exchange_instance:
                return []
            
            trades = await asyncio.wait_for(
                exchange_instance.fetch_my_trades(symbol, limit=limit),
                timeout=10
            )
            
            return trades
            
        except Exception as e:
            logger.error(f"Failed to get trade history: {str(e)}")
            return []
    
    async def get_supported_symbols(self, exchange: str, user_id: str) -> List[str]:
        """
        Get list of supported trading symbols
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            
        Returns:
            List of supported symbols
        """
        try:
            config = await self._get_exchange_config(exchange, user_id)
            if not config:
                return []
            
            exchange_instance = await self._create_exchange_instance(exchange, config)
            if not exchange_instance:
                return []
            
            if not exchange_instance.markets:
                await exchange_instance.load_markets()
            
            return list(exchange_instance.markets.keys())
            
        except Exception as e:
            logger.error(f"Failed to get supported symbols for {exchange}: {str(e)}")
            return []
    
    async def get_supported_timeframes(self, exchange: str, user_id: str) -> List[str]:
        """
        Get supported timeframes for an exchange
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            
        Returns:
            List of supported timeframes
        """
        try:
            config = await self._get_exchange_config(exchange, user_id)
            if not config:
                return []
            
            exchange_instance = await self._create_exchange_instance(exchange, config)
            if not exchange_instance:
                return []
            
            if hasattr(exchange_instance, 'timeframes'):
                return list(exchange_instance.timeframes.keys())
            
            return ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
            
        except Exception as e:
            logger.error(f"Failed to get timeframes for {exchange}: {str(e)}")
            return ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
    
    async def _get_exchange_config(self, exchange: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get exchange configuration for a user
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            
        Returns:
            Exchange configuration dictionary
        """
        try:
            cache_key = f"exchange_config:{user_id}:{exchange}"
            
            # Check cache first
            cached_config = self.redis_client.get(cache_key)
            if cached_config:
                return json.loads(cached_config)
            
            # Get from database
            result = self.supabase.table('user_exchanges').select('*').eq('user_id', user_id).eq('exchange', exchange).execute()
            
            if not result.data:
                logger.warning(f"No exchange config found for {exchange} and user {user_id}")
                return None
            
            exchange_data = result.data[0]
            
            # Decrypt credentials
            api_key = self._decrypt_credentials(exchange_data['api_key'])
            api_secret = self._decrypt_credentials(exchange_data['api_secret'])
            
            if not api_key or not api_secret:
                return None
            
            config = {
                'apiKey': api_key,
                'secret': api_secret,
                'sandbox': exchange_data.get('sandbox', False)
            }
            
            # Add additional credentials if available
            if exchange_data.get('api_password'):
                config['password'] = self._decrypt_credentials(exchange_data['api_password'])
            
            # Cache in Redis (30 minutes)
            self.redis_client.setex(cache_key, 1800, json.dumps(config))
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to get exchange config: {str(e)}")
            return None
    
    async def _create_exchange_instance(self, exchange: str, config: Dict[str, Any]) -> Optional[ccxt.Exchange]:
        """
        Create CCXT exchange instance
        
        Args:
            exchange: Exchange name
            config: Exchange configuration
            
        Returns:
            CCXT Exchange instance
        """
        try:
            if exchange not in self.supported_exchanges:
                logger.error(f"Unsupported exchange: {exchange}")
                return None
            
            # Get exchange class
            exchange_class = getattr(ccxt, exchange, None)
            if not exchange_class:
                logger.error(f"Exchange class not found: {exchange}")
                return None
            
            # Create exchange instance with settings
            settings = self.exchange_settings.get(exchange, {}).copy()
            settings.update(config)
            
            exchange_instance = exchange_class(settings)
            
            # Add timeout and retry settings
            if hasattr(exchange_instance, 'timeout'):
                exchange_instance.timeout = settings.get('timeout', 30)
            
            logger.info(f"Created exchange instance for {exchange}")
            return exchange_instance
            
        except Exception as e:
            logger.error(f"Failed to create exchange instance for {exchange}: {str(e)}")
            return None
    
    def _decrypt_credentials(self, encrypted_data: str) -> Optional[str]:
        """
        Decrypt encrypted API credentials
        
        Args:
            encrypted_data: Encrypted credential string
            
        Returns:
            Decrypted credential string
        """
        try:
            if not encrypted_data:
                return None
            
            # TODO: Implement actual encryption/decryption
            # For now, return as-is - implement proper encryption
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {str(e)}")
            return None
    
    async def test_exchange_connection(self, exchange: str, user_id: str) -> bool:
        """
        Test exchange connection and authentication
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            
        Returns:
            Connection test success status
        """
        try:
            # Get exchange info to test public API
            info = await self.get_exchange_info(exchange, user_id)
            if not info:
                return False
            
            # Test private API with balance
            balance = await self.get_balance(exchange, user_id)
            return balance is not None
            
        except Exception as e:
            logger.error(f"Exchange connection test failed for {exchange}: {str(e)}")
            return False


if __name__ == "__main__":
    # Test exchange handler
    async def test():
        handler = ExchangeHandler()
        
        # Test exchange validation
        is_valid = await handler.validate_exchange_config("binance", "test_user")
        print(f"Exchange validation: {is_valid}")
        
        # Test exchange info
        info = await handler.get_exchange_info("binance", "test_user")
        print(f"Exchange info: {info}")
        
        # Test market data
        market_data = await handler.get_market_data("binance", "BTC/USDT", "test_user")
        print(f"Market data: {market_data}")
    
    import asyncio
    asyncio.run(test())