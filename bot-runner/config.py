"""
NusaNexus NoFOMO - Config Manager
Manages bot configurations and Freqtrade config generation
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import redis
from supabase import create_client, Client

from manager import BotConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Configuration Manager for Bot Runner
    
    Responsibilities:
    - Generate Freqtrade configuration files
    - Manage bot-specific configurations
    - Handle encrypted exchange credentials
    - Validate configuration data
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
        
        # Configuration templates
        self.base_config_template = {
            "timeframe": "1h",
            "stake_currency": "USDT",
            "stake_amount": "100",
            "tradable_balance_ratio": 0.99,
            "fiat_display_currency": "USD",
            "dry_run": True,
            "cancel_open_orders_on_exit": False,
            "max_open_trades": 1,
            "unfilledtimeout": {
                "buy": 10,
                "sell": 30
            },
            "stoploss": -0.10,
            "trailing_stop": True,
            "trailing_stop_positive": 0.01,
            "trailing_stop_positive_offset": 0.011,
            "trailing_only_offset_is_reached": False,
            "use_exit_signal": True,
            "exit_profit_only": False,
            "ignore_roi_if_buy_signal": False,
            "bid_strategy": {
                "price_side": "bid",
                "ask_last_balance": 0.0,
                "use_order_book": True,
                "order_book_top": 1
            },
            "ask_strategy": {
                "price_side": "ask",
                "bid_last_balance": 0.0,
                "use_order_book": True,
                "order_book_top": 1
            },
            "pair_whitelist": ["BTC/USDT"],
            "pair_blacklist": [],
            "data_period_minutes": 30,
            "data_picker_rollover_periods": 30,
            "startup_candles": 30,
            "fee": 0.001
        }
        
        # Exchange-specific configurations
        self.exchange_configs = {
            "binance": {
                "ccxt_config": {
                    "enableRateLimit": True,
                    "rateLimit": 100
                },
                "ccxt_async_config": {
                    "enableRateLimit": True,
                    "rateLimit": 100
                }
            },
            "bybit": {
                "ccxt_config": {
                    "enableRateLimit": True,
                    "rateLimit": 100
                },
                "ccxt_async_config": {
                    "enableRateLimit": True,
                    "rateLimit": 100
                }
            }
        }
        
        logger.info("Config Manager initialized")
    
    async def create_freqtrade_config(self, bot_id: str, bot_config: BotConfig) -> Optional[Path]:
        """
        Create complete Freqtrade configuration for a bot
        
        Args:
            bot_id: Bot identifier
            bot_config: Bot configuration data
            
        Returns:
            Path to created config file
        """
        try:
            # Start with base configuration
            config = self.base_config_template.copy()
            
            # Update with bot-specific settings
            config.update({
                "timeframe": bot_config.timeframe,
                "stake_amount": str(bot_config.stake_amount),
                "max_open_trades": bot_config.max_open_trades,
                "dry_run": bot_config.dry_run,
                "pair_whitelist": [bot_config.pair]
            })
            
            # Add stop loss configuration
            if bot_config.stop_loss:
                config["stoploss"] = -bot_config.stop_loss / 100
            
            # Add take profit configuration
            if bot_config.take_profit:
                config["minimal_roi"] = {
                    "0": bot_config.take_profit / 100
                }
            
            # Add exchange configuration
            exchange_config = await self._get_exchange_config(bot_config.exchange, bot_config.user_id)
            if exchange_config:
                config["exchange"] = exchange_config
            
            # Add strategy configuration
            config["strategy"] = bot_config.strategy
            
            # Add bot-specific metadata
            config["bot_metadata"] = {
                "bot_id": bot_id,
                "user_id": bot_config.user_id,
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            # Write configuration to file
            config_path = Path(f"configs/{bot_id}_config.json")
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Created Freqtrade config for bot {bot_id}")
            return config_path
            
        except Exception as e:
            logger.error(f"Failed to create Freqtrade config for bot {bot_id}: {str(e)}")
            return None
    
    async def _get_exchange_config(self, exchange: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get exchange configuration with encrypted credentials
        
        Args:
            exchange: Exchange name
            user_id: User identifier
            
        Returns:
            Exchange configuration with credentials
        """
        try:
            # Get exchange credentials from database
            result = self.supabase.table('user_exchanges').select('*').eq('user_id', user_id).eq('exchange', exchange).execute()
            
            if not result.data:
                logger.warning(f"No exchange credentials found for {exchange} and user {user_id}")
                return None
            
            exchange_data = result.data[0]
            
            # Decrypt API credentials
            api_key = self._decrypt_credentials(exchange_data['api_key'])
            api_secret = self._decrypt_credentials(exchange_data['api_secret'])
            
            if not api_key or not api_secret:
                logger.error(f"Failed to decrypt credentials for {exchange}")
                return None
            
            # Get base exchange config
            base_config = self.exchange_configs.get(exchange, {})
            
            # Create complete exchange config
            exchange_config = {
                "name": exchange,
                "key": api_key,
                "secret": api_secret,
                **base_config
            }
            
            # Add additional credentials if available
            if exchange_data.get('api_password'):
                exchange_config["password"] = self._decrypt_credentials(exchange_data['api_password'])
            
            if exchange_data.get('sandbox'):
                exchange_config["sandbox"] = exchange_data['sandbox']
            
            return exchange_config
            
        except Exception as e:
            logger.error(f"Failed to get exchange config for {exchange}: {str(e)}")
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
    
    async def get_bot_config(self, bot_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete bot configuration
        
        Args:
            bot_id: Bot identifier
            user_id: User identifier
            
        Returns:
            Bot configuration dictionary
        """
        try:
            # Get from Redis cache first
            cache_key = f"bot_config:{bot_id}:{user_id}"
            cached_config = self.redis_client.get(cache_key)
            
            if cached_config:
                return json.loads(cached_config)
            
            # Get from database
            result = self.supabase.table('bots').select('*').eq('id', bot_id).eq('user_id', user_id).execute()
            
            if not result.data:
                return None
            
            bot_data = result.data[0]
            
            # Get exchange configuration
            exchange_config = await self._get_exchange_config(bot_data['exchange'], user_id)
            
            # Combine all configuration data
            config = {
                **bot_data,
                "exchange_config": exchange_config
            }
            
            # Cache in Redis (1 hour expiry)
            self.redis_client.setex(cache_key, 3600, json.dumps(config))
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to get bot config for {bot_id}: {str(e)}")
            return None
    
    async def validate_config(self, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate bot configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Required fields
            required_fields = ['strategy', 'exchange', 'stake_amount', 'timeframe']
            for field in required_fields:
                if not config.get(field):
                    errors.append(f"Missing required field: {field}")
            
            # Validate stake amount
            stake_amount = config.get('stake_amount')
            if stake_amount and (not isinstance(stake_amount, (int, float)) or stake_amount <= 0):
                errors.append("Invalid stake amount")
            
            # Validate max open trades
            max_trades = config.get('max_open_trades')
            if max_trades and (not isinstance(max_trades, int) or max_trades < 1):
                errors.append("Invalid max_open_trades")
            
            # Validate timeframes
            valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
            timeframe = config.get('timeframe')
            if timeframe and timeframe not in valid_timeframes:
                errors.append(f"Invalid timeframe: {timeframe}")
            
            # Validate exchanges
            valid_exchanges = ['binance', 'bybit', 'kucoin', 'okx']
            exchange = config.get('exchange')
            if exchange and exchange not in valid_exchanges:
                errors.append(f"Invalid exchange: {exchange}")
            
            # Validate stop loss and take profit
            if config.get('stop_loss') and config['stop_loss'] <= 0:
                errors.append("Stop loss must be positive percentage")
            
            if config.get('take_profit') and config['take_profit'] <= 0:
                errors.append("Take profit must be positive percentage")
            
            # Validate pairs if provided
            pairs = config.get('pair_whitelist', [])
            for pair in pairs:
                if not isinstance(pair, str) or '/' not in pair:
                    errors.append(f"Invalid pair format: {pair}")
            
            is_valid = len(errors) == 0
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
    
    async def update_config(self, bot_id: str, user_id: str, config_updates: Dict[str, Any]) -> bool:
        """
        Update bot configuration
        
        Args:
            bot_id: Bot identifier
            user_id: User identifier
            config_updates: Configuration updates
            
        Returns:
            Success status
        """
        try:
            # Validate updates
            # Get current config
            current_config = await self.get_bot_config(bot_id, user_id)
            if not current_config:
                return False
            
            # Merge updates
            updated_config = {**current_config, **config_updates}
            
            # Validate updated config
            is_valid, errors = await self.validate_config(updated_config)
            if not is_valid:
                logger.error(f"Config validation failed for bot {bot_id}: {errors}")
                return False
            
            # Update in database
            self.supabase.table('bots').update({
                **config_updates,
                'updated_at': datetime.now().isoformat()
            }).eq('id', bot_id).eq('user_id', user_id).execute()
            
            # Clear cache
            cache_key = f"bot_config:{bot_id}:{user_id}"
            self.redis_client.delete(cache_key)
            
            # Recreate Freqtrade config if necessary
            if any(field in config_updates for field in ['strategy', 'exchange', 'stake_amount', 'timeframe']):
                # Update BotConfig object
                bot_config = BotConfig(
                    bot_id=bot_id,
                    user_id=user_id,
                    name=updated_config.get('name', ''),
                    strategy=updated_config['strategy'],
                    exchange=updated_config['exchange'],
                    pair=updated_config.get('trading_pair', 'BTC/USDT'),
                    timeframe=updated_config['timeframe'],
                    stake_amount=updated_config['stake_amount'],
                    max_open_trades=updated_config.get('max_open_trades', 1),
                    dry_run=updated_config.get('is_paper_trade', True)
                )
                
                await self.create_freqtrade_config(bot_id, bot_config)
            
            logger.info(f"Updated configuration for bot {bot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update config for bot {bot_id}: {str(e)}")
            return False
    
    async def get_config_template(self, strategy_type: str = "basic") -> Dict[str, Any]:
        """
        Get configuration template for different strategy types
        
        Args:
            strategy_type: Type of strategy (basic, advanced, ai)
            
        Returns:
            Configuration template
        """
        try:
            templates = {
                "basic": {
                    **self.base_config_template,
                    "strategy": "SampleStrategy",
                    "use_exit_signal": True,
                    "exit_profit_only": False,
                    "stoploss": -0.10,
                    "minimal_roi": {
                        "0": 0.10,
                        "20": 0.05,
                        "40": 0.02
                    }
                },
                "advanced": {
                    **self.base_config_template,
                    "strategy": "AdvancedStrategy",
                    "use_exit_signal": True,
                    "exit_profit_only": False,
                    "stoploss": -0.05,
                    "trailing_stop": True,
                    "trailing_stop_positive": 0.01,
                    "minimal_roi": {
                        "0": 0.05,
                        "10": 0.03,
                        "20": 0.01
                    }
                },
                "ai": {
                    **self.base_config_template,
                    "strategy": "AIStrategy",
                    "use_exit_signal": True,
                    "exit_profit_only": False,
                    "stoploss": -0.05,
                    "trailing_stop": True,
                    "minimal_roi": {
                        "0": 0.03,
                        "5": 0.02,
                        "10": 0.01
                    }
                }
            }
            
            return templates.get(strategy_type, self.base_config_template)
            
        except Exception as e:
            logger.error(f"Failed to get config template: {str(e)}")
            return self.base_config_template


if __name__ == "__main__":
    # Test config manager
    async def test():
        manager = ConfigManager()
        
        # Test config generation
        bot_config = BotConfig(
            bot_id="test_bot_123",
            user_id="user_123",
            name="Test Bot",
            strategy="SampleStrategy",
            exchange="binance",
            pair="BTC/USDT",
            timeframe="1h",
            stake_amount=100.0,
            max_open_trades=1,
            dry_run=True
        )
        
        config_path = await manager.create_freqtrade_config("test_bot_123", bot_config)
        print(f"Created config at: {config_path}")
    
    import asyncio
    asyncio.run(test())