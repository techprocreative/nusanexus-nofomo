"""
Bot management endpoints for NusaNexus NoFOMO
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import structlog

from app.core.auth import get_current_user
from app.core.database import get_db_client
from app.models.user import UserResponse

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models
class BotConfig(BaseModel):
    name: str
    exchange: str  # binance, bybit
    trading_pair: str
    timeframe: str  # 1m, 5m, 15m, 1h, 4h, 1d
    strategy: str
    initial_balance: float
    max_open_trades: int = 1
    stake_amount: float

class BotUpdate(BaseModel):
    name: Optional[str] = None
    strategy: Optional[str] = None
    max_open_trades: Optional[int] = None
    stake_amount: Optional[float] = None

class BotResponse(BaseModel):
    id: str
    user_id: str
    name: str
    exchange: str
    trading_pair: str
    timeframe: str
    strategy: str
    status: str  # running, stopped, error
    initial_balance: float
    current_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    profit: float
    created_at: datetime
    updated_at: datetime

@router.get("/", response_model=List[BotResponse])
async def get_bots(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all bots for current user
    """
    try:
        db_client = get_db_client()
        
        # Get user bots from database
        bots = db_client.get_user_bots(current_user.id)
        
        # Convert to response models
        bot_responses = []
        for bot in bots:
            # Parse datetime strings
            created_at = datetime.fromisoformat(bot.get("created_at", datetime.utcnow().isoformat()))
            updated_at = datetime.fromisoformat(bot.get("updated_at", datetime.utcnow().isoformat()))
            
            # Calculate current balance and profit from trades
            trades = db_client.get_bot_trades(bot["id"], current_user.id, limit=1000)
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get("profit", 0) > 0])
            losing_trades = total_trades - winning_trades
            total_profit = sum(t.get("profit", 0) for t in trades)
            current_balance = bot.get("initial_balance", 0) + total_profit
            
            bot_response = BotResponse(
                id=bot["id"],
                user_id=bot["user_id"],
                name=bot["name"],
                exchange=bot["exchange"],
                trading_pair=bot["trading_pair"],
                timeframe=bot["timeframe"],
                strategy=bot["strategy"],
                status=bot.get("status", "stopped"),
                initial_balance=bot.get("initial_balance", 0),
                current_balance=current_balance,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                profit=total_profit,
                created_at=created_at,
                updated_at=updated_at
            )
            bot_responses.append(bot_response)
        
        logger.info("Retrieved user bots", user_id=current_user.id, count=len(bot_responses))
        return bot_responses
        
    except Exception as e:
        logger.error("Failed to get bots", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bots"
        )

@router.post("/", response_model=BotResponse)
async def create_bot(
    bot_config: BotConfig,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create new trading bot
    """
    try:
        db_client = get_db_client()
        
        # Prepare bot data for database
        bot_record = {
            "user_id": current_user.id,
            "name": bot_config.name,
            "exchange": bot_config.exchange,
            "trading_pair": bot_config.trading_pair,
            "timeframe": bot_config.timeframe,
            "strategy": bot_config.strategy,
            "initial_balance": bot_config.initial_balance,
            "max_open_trades": bot_config.max_open_trades,
            "stake_amount": bot_config.stake_amount,
            "status": "stopped",  # New bots start as stopped
            "current_balance": bot_config.initial_balance,  # Initially same as initial
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "profit": 0.0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Create bot in database
        created_bot = db_client.create_bot(bot_record)
        
        if not created_bot:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create bot"
            )
        
        # Convert to response model
        created_at = datetime.fromisoformat(created_bot.get("created_at"))
        updated_at = datetime.fromisoformat(created_bot.get("updated_at"))
        
        bot_response = BotResponse(
            id=created_bot["id"],
            user_id=created_bot["user_id"],
            name=created_bot["name"],
            exchange=created_bot["exchange"],
            trading_pair=created_bot["trading_pair"],
            timeframe=created_bot["timeframe"],
            strategy=created_bot["strategy"],
            status=created_bot.get("status", "stopped"),
            initial_balance=created_bot.get("initial_balance", 0),
            current_balance=created_bot.get("current_balance", 0),
            total_trades=created_bot.get("total_trades", 0),
            winning_trades=created_bot.get("winning_trades", 0),
            losing_trades=created_bot.get("losing_trades", 0),
            profit=created_bot.get("profit", 0.0),
            created_at=created_at,
            updated_at=updated_at
        )
        
        logger.info("Bot created", bot_id=created_bot["id"], user_id=current_user.id)
        
        return bot_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create bot", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bot"
        )

@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get specific bot details
    """
    try:
        db_client = get_db_client()
        
        # Get bot with user authorization check
        bot = db_client.get_bot_by_id(bot_id, current_user.id)
        
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Parse datetime strings
        created_at = datetime.fromisoformat(bot.get("created_at", datetime.utcnow().isoformat()))
        updated_at = datetime.fromisoformat(bot.get("updated_at", datetime.utcnow().isoformat()))
        
        # Calculate current balance and profit from trades
        trades = db_client.get_bot_trades(bot_id, current_user.id, limit=1000)
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get("profit", 0) > 0])
        losing_trades = total_trades - winning_trades
        total_profit = sum(t.get("profit", 0) for t in trades)
        current_balance = bot.get("initial_balance", 0) + total_profit
        
        # Convert to response model
        bot_response = BotResponse(
            id=bot["id"],
            user_id=bot["user_id"],
            name=bot["name"],
            exchange=bot["exchange"],
            trading_pair=bot["trading_pair"],
            timeframe=bot["timeframe"],
            strategy=bot["strategy"],
            status=bot.get("status", "stopped"),
            initial_balance=bot.get("initial_balance", 0),
            current_balance=current_balance,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            profit=total_profit,
            created_at=created_at,
            updated_at=updated_at
        )
        
        logger.info("Retrieved bot details", bot_id=bot_id, user_id=current_user.id)
        
        return bot_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get bot", bot_id=bot_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bot"
        )

@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: str,
    bot_update: BotUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update bot configuration
    """
    try:
        db_client = get_db_client()
        
        # Verify bot exists and belongs to user
        existing_bot = db_client.get_bot_by_id(bot_id, current_user.id)
        if not existing_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Prepare update data with only non-None fields
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        
        if bot_update.name is not None:
            update_data["name"] = bot_update.name
        if bot_update.strategy is not None:
            update_data["strategy"] = bot_update.strategy
        if bot_update.max_open_trades is not None:
            update_data["max_open_trades"] = bot_update.max_open_trades
        if bot_update.stake_amount is not None:
            update_data["stake_amount"] = bot_update.stake_amount
        
        # Update bot in database
        updated_bot = db_client.update_bot(bot_id, current_user.id, update_data)
        
        if not updated_bot:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update bot"
            )
        
        # Parse datetime strings
        created_at = datetime.fromisoformat(updated_bot.get("created_at", datetime.utcnow().isoformat()))
        updated_at = datetime.fromisoformat(updated_bot.get("updated_at", datetime.utcnow().isoformat()))
        
        # Calculate current balance and profit from trades
        trades = db_client.get_bot_trades(bot_id, current_user.id, limit=1000)
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get("profit", 0) > 0])
        losing_trades = total_trades - winning_trades
        total_profit = sum(t.get("profit", 0) for t in trades)
        current_balance = updated_bot.get("initial_balance", 0) + total_profit
        
        # Convert to response model
        bot_response = BotResponse(
            id=updated_bot["id"],
            user_id=updated_bot["user_id"],
            name=updated_bot["name"],
            exchange=updated_bot["exchange"],
            trading_pair=updated_bot["trading_pair"],
            timeframe=updated_bot["timeframe"],
            strategy=updated_bot["strategy"],
            status=updated_bot.get("status", "stopped"),
            initial_balance=updated_bot.get("initial_balance", 0),
            current_balance=current_balance,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            profit=total_profit,
            created_at=created_at,
            updated_at=updated_at
        )
        
        logger.info("Bot updated", bot_id=bot_id, user_id=current_user.id)
        
        return bot_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update bot", bot_id=bot_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bot"
        )

@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete bot
    """
    try:
        db_client = get_db_client()
        
        # Verify bot exists and belongs to user
        existing_bot = db_client.get_bot_by_id(bot_id, current_user.id)
        if not existing_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Delete bot from database
        success = db_client.delete_bot(bot_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete bot"
            )
        
        logger.info("Bot deleted", bot_id=bot_id, user_id=current_user.id)
        
        return {"message": "Bot deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete bot", bot_id=bot_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bot"
        )

@router.post("/{bot_id}/start")
async def start_bot(
    bot_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Start trading bot
    """
    try:
        db_client = get_db_client()
        
        # Verify bot exists and belongs to user
        existing_bot = db_client.get_bot_by_id(bot_id, current_user.id)
        if not existing_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if bot is already running
        if existing_bot.get("status") == "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is already running"
            )
        
        # Update bot status to running
        update_data = {
            "status": "running",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        updated_bot = db_client.update_bot(bot_id, current_user.id, update_data)
        
        if not updated_bot:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start bot"
            )
        
        # TODO: In future, this would also:
        # 1. Add bot to Redis queue for execution
        # 2. Initialize bot runner process
        # 3. Start real-time monitoring
        
        logger.info("Bot started", bot_id=bot_id, user_id=current_user.id)
        
        return {
            "message": "Bot started successfully",
            "status": "running",
            "bot_id": bot_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start bot", bot_id=bot_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start bot"
        )

@router.post("/{bot_id}/stop")
async def stop_bot(
    bot_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Stop trading bot
    """
    try:
        db_client = get_db_client()
        
        # Verify bot exists and belongs to user
        existing_bot = db_client.get_bot_by_id(bot_id, current_user.id)
        if not existing_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Check if bot is already stopped
        if existing_bot.get("status") == "stopped":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is already stopped"
            )
        
        # Update bot status to stopped
        update_data = {
            "status": "stopped",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        updated_bot = db_client.update_bot(bot_id, current_user.id, update_data)
        
        if not updated_bot:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to stop bot"
            )
        
        # TODO: In future, this would also:
        # 1. Remove bot from Redis queue
        # 2. Stop bot runner process gracefully
        # 3. Close any open positions if required
        # 4. Save current state for next start
        
        logger.info("Bot stopped", bot_id=bot_id, user_id=current_user.id)
        
        return {
            "message": "Bot stopped successfully",
            "status": "stopped",
            "bot_id": bot_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop bot", bot_id=bot_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop bot"
        )

@router.get("/{bot_id}/status")
async def get_bot_status(
    bot_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get real-time bot status
    """
    try:
        db_client = get_db_client()
        
        # Verify bot exists and belongs to user
        bot = db_client.get_bot_by_id(bot_id, current_user.id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found"
            )
        
        # Get recent trades for performance calculation
        trades = db_client.get_bot_trades(bot_id, current_user.id, limit=100)
        recent_trades = trades[:10]  # Last 10 trades
        
        # Calculate real-time metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get("profit", 0) > 0])
        losing_trades = total_trades - winning_trades
        total_profit = sum(t.get("profit", 0) for t in trades)
        current_balance = bot.get("initial_balance", 0) + total_profit
        
        # Calculate win rate
        win_rate = (winning_trades / max(total_trades, 1)) * 100 if total_trades > 0 else 0
        
        # Get last trade information
        last_trade = trades[0] if trades else None
        last_trade_time = None
        last_trade_profit = None
        
        if last_trade:
            try:
                last_trade_time = datetime.fromisoformat(last_trade.get("created_at", datetime.utcnow().isoformat()))
                last_trade_profit = last_trade.get("profit", 0)
            except:
                pass
        
        # Calculate today's performance
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = [t for t in trades if t.get("created_at") and 
                       datetime.fromisoformat(t.get("created_at")) >= today_start]
        today_profit = sum(t.get("profit", 0) for t in today_trades)
        
        # Get bot configuration
        config = {
            "name": bot["name"],
            "exchange": bot["exchange"],
            "trading_pair": bot["trading_pair"],
            "timeframe": bot["timeframe"],
            "strategy": bot["strategy"],
            "initial_balance": bot.get("initial_balance", 0),
            "max_open_trades": bot.get("max_open_trades", 1),
            "stake_amount": bot.get("stake_amount", 0)
        }
        
        # Prepare comprehensive status response
        status_response = {
            "bot_id": bot_id,
            "status": bot.get("status", "stopped"),
            "created_at": bot.get("created_at"),
            "updated_at": bot.get("updated_at"),
            "last_activity": last_trade_time.isoformat() if last_trade_time else None,
            
            # Performance metrics
            "performance": {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(win_rate, 2),
                "total_profit": round(total_profit, 6),
                "current_balance": round(current_balance, 6),
                "initial_balance": bot.get("initial_balance", 0),
                "profit_percentage": round((total_profit / max(bot.get("initial_balance", 1), 1)) * 100, 2),
                "today_profit": round(today_profit, 6),
                "today_trades": len(today_trades)
            },
            
            # Last trade information
            "last_trade": {
                "timestamp": last_trade_time.isoformat() if last_trade_time else None,
                "profit": last_trade_profit,
                "trading_pair": last_trade.get("trading_pair", bot.get("trading_pair", "")),
                "side": last_trade.get("side", "buy"),
                "amount": last_trade.get("amount", 0)
            } if last_trade else None,
            
            # Configuration
            "config": config,
            
            # Recent trades for debugging
            "recent_trades": [
                {
                    "timestamp": t.get("created_at"),
                    "profit": t.get("profit", 0),
                    "side": t.get("side", "buy"),
                    "trading_pair": t.get("trading_pair", ""),
                    "amount": t.get("amount", 0)
                }
                for t in recent_trades
            ]
        }
        
        logger.info("Retrieved bot status", bot_id=bot_id, user_id=current_user.id, status=bot.get("status"))
        
        return status_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get bot status", bot_id=bot_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bot status"
        )