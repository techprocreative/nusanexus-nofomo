"""
Bot Runner service for managing Freqtrade bot lifecycle
"""

import subprocess
import json
import os
import signal
from typing import Dict, Any, Optional
from datetime import datetime
import structlog
from pathlib import Path

from app.core.database import get_db_client

logger = structlog.get_logger()


class BotRunnerService:
    """Service for managing bot lifecycle and execution"""
    
    def __init__(self):
        self.db_client = get_db_client()
        self.bot_processes: Dict[str, subprocess.Popen] = {}
        self.bot_configs: Dict[str, Dict[str, Any]] = {}
        self.base_dir = Path("/app/bots")
        self.base_dir.mkdir(exist_ok=True)
    
    def start_bot(self, bot_id: str, user_id: str, config: Dict[str, Any]) -> bool:
        """Start a trading bot"""
        try:
            # Get bot data from database
            bot_data = self.db_client.get_bot_by_id(bot_id, user_id)
            if not bot_data:
                raise ValueError(f"Bot {bot_id} not found for user {user_id}")
            
            if bot_data["status"] == "running":
                logger.warning("Bot already running", bot_id=bot_id)
                return True
            
            # Create bot directory
            bot_dir = self.base_dir / bot_id
            bot_dir.mkdir(exist_ok=True)
            
            # Generate bot configuration
            bot_config = self._generate_bot_config(bot_data, config)
            config_path = bot_dir / "config.json"
            
            with open(config_path, 'w') as f:
                json.dump(bot_config, f, indent=2)
            
            # Create strategy file if needed
            strategy_path = bot_dir / "strategy.py"
            if not strategy_path.exists():
                self._create_strategy_file(bot_data, strategy_path)
            
            # Prepare command
            cmd = [
                "freqtrade",
                "trade",
                "--config", str(config_path),
                "--strategy-path", str(bot_dir)
            ]
            
            # Start bot process
            env = os.environ.copy()
            env['FREQTRADE__DATABASE__URL'] = f"sqlite:///{bot_dir}/trades.db"
            
            process = subprocess.Popen(
                cmd,
                cwd=str(bot_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Store process
            self.bot_processes[bot_id] = process
            
            # Update bot status in database
            self.db_client.update_bot(bot_id, user_id, {
                "status": "running",
                "last_trade_at": datetime.utcnow().isoformat()
            })
            
            logger.info("Bot started successfully", bot_id=bot_id, pid=process.pid)
            return True
            
        except Exception as e:
            logger.error("Failed to start bot", bot_id=bot_id, error=str(e))
            # Update bot status to error
            self.db_client.update_bot(bot_id, user_id, {
                "status": "error",
                "error_message": str(e)
            })
            return False
    
    def stop_bot(self, bot_id: str, user_id: str) -> bool:
        """Stop a trading bot"""
        try:
            if bot_id not in self.bot_processes:
                logger.warning("Bot process not found", bot_id=bot_id)
                return True
            
            process = self.bot_processes[bot_id]
            
            # Terminate process gracefully
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait()
            
            # Clean up
            del self.bot_processes[bot_id]
            if bot_id in self.bot_configs:
                del self.bot_configs[bot_id]
            
            # Update bot status
            self.db_client.update_bot(bot_id, user_id, {
                "status": "stopped"
            })
            
            logger.info("Bot stopped successfully", bot_id=bot_id)
            return True
            
        except Exception as e:
            logger.error("Failed to stop bot", bot_id=bot_id, error=str(e))
            return False
    
    def get_bot_status(self, bot_id: str) -> Dict[str, Any]:
        """Get current bot status"""
        try:
            if bot_id in self.bot_processes:
                process = self.bot_processes[bot_id]
                if process.poll() is None:
                    # Process is still running
                    return {
                        "status": "running",
                        "pid": process.pid,
                        "running_since": datetime.now().isoformat()
                    }
                else:
                    # Process has ended
                    return {
                        "status": "stopped",
                        "exit_code": process.returncode
                    }
            else:
                return {"status": "stopped"}
                
        except Exception as e:
            logger.error("Failed to get bot status", bot_id=bot_id, error=str(e))
            return {"status": "error", "error": str(e)}
    
    def pause_bot(self, bot_id: str, user_id: str) -> bool:
        """Pause a running bot"""
        try:
            if bot_id not in self.bot_processes:
                logger.warning("Bot process not found", bot_id=bot_id)
                return False
            
            # For Freqtrade, we'll just update the status
            # In a real implementation, you might want to send a pause signal
            self.db_client.update_bot(bot_id, user_id, {
                "status": "paused"
            })
            
            logger.info("Bot paused", bot_id=bot_id)
            return True
            
        except Exception as e:
            logger.error("Failed to pause bot", bot_id=bot_id, error=str(e))
            return False
    
    def resume_bot(self, bot_id: str, user_id: str) -> bool:
        """Resume a paused bot"""
        try:
            self.db_client.update_bot(bot_id, user_id, {
                "status": "running"
            })
            
            logger.info("Bot resumed", bot_id=bot_id)
            return True
            
        except Exception as e:
            logger.error("Failed to resume bot", bot_id=bot_id, error=str(e))
            return False
    
    def _generate_bot_config(self, bot_data: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Freqtrade configuration"""
        config = {
            "max_open_trades": bot_data.get("max_open_trades", 1),
            "stake_currency": "USDT",
            "stake_amount": str(bot_data.get("stake_amount", 100)),
            "tradable_balance_ratio": 0.99,
            "fiat_display_currency": "USD",
            "unfilledtimeout": {
                "buy": 10,
                "sell": 30
            },
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
            "pair_whitelist": [bot_data.get("trading_pair")],
            "pair_blacklist": [],
            "dry_run": bot_data.get("is_paper_trade", True),
            "dry_run_wallet": bot_data.get("initial_balance", 1000),
            "fee": 0.001,
            "startup_candles": 30
        }
        
        # Add exchange configuration
        exchange_config = user_config.get("exchange_config", {})
        if exchange_config:
            config["exchange"] = {
                "name": bot_data.get("exchange"),
                "key": exchange_config.get("api_key"),
                "secret": exchange_config.get("api_secret"),
                "ccxt_config": {},
                "ccxt_async_config": {}
            }
        
        # Add stop loss and take profit if specified
        if bot_data.get("stop_loss"):
            config["stoploss"] = -bot_data["stop_loss"] / 100
        
        if bot_data.get("take_profit"):
            config["minimal_roi"] = {
                "0": bot_data["take_profit"] / 100
            }
        
        return config
    
    def _create_strategy_file(self, bot_data: Dict[str, Any], strategy_path: Path):
        """Create a basic strategy file for the bot"""
        strategy_name = bot_data.get("strategy", "SampleStrategy")
        
        strategy_code = f'''
# {strategy_name} - Generated for NusaNexus NoFOMO
from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import merge_informative_pair
from freqtrade.strategy.experimental import IStrategy
from pandas import DataFrame
import numpy as np

class {strategy_name}(IStrategy):
    """
    {strategy_name} strategy for {bot_data.get('trading_pair')} on {bot_data.get('timeframe')} timeframe
    """
    
    # Strategy interface version - allow new iterations of the interface.
    # These are rules for the overall framework, so please read and follow
    # the docs, in order to understand what the modifications to these files
    # should do!
    INTERFACE_VERSION = 3

    # The minimum capital required (USD) used to determine the allowed stake.
    # Check the documentation and the `state.stake_amount` property of the
    # class. This is the capital for your current strategy.
    # For the more advanced examples, you might want to use
    # `average_last_candles()` function in the logic here.
    # Be aware that `dry_run_wallet` amount in config.json contains 999.99,
    # and as we're only working with the money we use the daily
    # ROI below, a short cut has been set to a default of 1000.
    min_stake_amount = 10

    # This attribute will be overridden if the config file contains "stake_currency"
    stake_currency = "USDT"

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_exit_signal = False
    use_entry_signal = True

    # Hyperopt parameters
    buy_rsi = 30
    buy_rsi_enabled = False
    buy_rsi_period = 14
    buy_sell_enabled = False

    # Sell signal
    sell_rsi = 70
    sell_rsi_enabled = False
    sell_rsi_period = 14

    # Optimal timeframe for the strategy
    timeframe = "{bot_data.get('timeframe', '1h')}"

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Add indicators to the given DataFrame
        
        Please note you also need to set the "stake_currency" value in the config.
        """
        
        # RSI
        dataframe['rsi'] = (
            dataframe['close']
            .rolling(length=14)
            .apply(lambda x: x.ewm(alpha=1/14).mean())
        )
        
        # SMA
        dataframe['sma'] = dataframe['close'].rolling(20).mean()
        dataframe['sma_long'] = dataframe['close'].rolling(50).mean()
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populate entry signals for the strategy
        """
        
        # Long signals
        dataframe.loc[
            (
                (dataframe['rsi'] < self.buy_rsi) &
                (dataframe['sma'] > dataframe['sma_long']) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'
        ] = 1
        
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populate exit signals for the strategy
        """
        
        # Exit signals
        dataframe.loc[
            (
                (dataframe['rsi'] > self.sell_rsi) |
                (dataframe['sma'] < dataframe['sma_long'])
            ),
            'exit_long'
        ] = 1
        
        return dataframe
'''
        
        with open(strategy_path, 'w') as f:
            f.write(strategy_code)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check bot runner health"""
        try:
            running_bots = len(self.bot_processes)
            
            # Check each bot process
            bot_statuses = {}
            for bot_id, process in self.bot_processes.items():
                if process.poll() is None:
                    bot_statuses[bot_id] = "running"
                else:
                    bot_statuses[bot_id] = f"stopped (exit code: {process.returncode})"
            
            return {
                "status": "healthy",
                "running_bots": running_bots,
                "bot_statuses": bot_statuses,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Bot runner health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global bot runner service instance
bot_runner_service: Optional[BotRunnerService] = None


def get_bot_runner_service() -> BotRunnerService:
    """Get bot runner service instance"""
    global bot_runner_service
    if bot_runner_service is None:
        bot_runner_service = BotRunnerService()
    return bot_runner_service