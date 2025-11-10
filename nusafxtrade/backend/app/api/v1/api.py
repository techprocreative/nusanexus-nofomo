"""
API Router v1 for NusaNexus NoFOMO
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, bots, strategies, trades, ai, health

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(bots.router, prefix="/bots", tags=["bots"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(health.router, prefix="/health", tags=["health"])