"""
NusaNexus NoFOMO - FastAPI Backend
AI-Powered Crypto Trading Bot SaaS
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog
from app.api.v1.api import api_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting NusaNexus NoFOMO API")
    yield
    # Shutdown
    logger.info("Shutting down NusaNexus NoFOMO API")

# Create FastAPI application
app = FastAPI(
    title="NusaNexus NoFOMO API",
    description="AI-Powered Crypto Trading Bot SaaS Platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add CORS middleware
from app.core.config import settings as app_settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=app_settings.trusted_hosts
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "service": "NusaNexus NoFOMO API",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
