"""
Health check and monitoring endpoints for NusaNexus NoFOMO
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import structlog
import psutil
import os

from app.core.database import get_db_client
from app.core.config import settings
from app.models.common import HealthStatus, DatabaseHealth, RedisHealth, ExchangeHealth

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=HealthStatus)
async def health_check():
    """
    Comprehensive health check endpoint
    """
    try:
        # Check database health
        db_client = get_db_client()
        db_health = db_client.health_check()
        
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check Redis (placeholder - would need Redis client)
        redis_health = {
            "status": "healthy",
            "response_time_ms": 1.0,
            "connected": True
        }
        
        # Check exchange connectivity (placeholder)
        exchange_health = {
            "status": "healthy",
            "exchanges": {
                "binance": "connected",
                "bybit": "connected"
            },
            "response_time_ms": 150.0
        }
        
        # Determine overall status
        overall_status = "healthy"
        if db_health["status"] != "healthy":
            overall_status = "unhealthy"
        elif cpu_percent > 90 or memory.percent > 90:
            overall_status = "degraded"
        
        services = {
            "database": db_health["status"],
            "redis": redis_health["status"],
            "exchanges": exchange_health["status"],
            "system": overall_status,
            "system_cpu": f"{cpu_percent:.1f}%",
            "system_memory": f"{memory.percent:.1f}%",
            "system_disk": f"{disk.percent:.1f}%"
        }
        
        health_status = HealthStatus(
            status=overall_status,
            services=services
        )
        
        logger.info("Health check completed", status=overall_status, services=services)
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthStatus(
            status="unhealthy",
            services={"error": str(e)}
        )


@router.get("/database", response_model=DatabaseHealth)
async def database_health():
    """
    Database-specific health check
    """
    try:
        db_client = get_db_client()
        health = db_client.health_check()
        
        return DatabaseHealth(
            status=health["status"],
            response_time_ms=health["response_time_ms"],
            connected_clients=1  # Placeholder
        )
        
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return DatabaseHealth(
            status="unhealthy",
            response_time_ms=None,
            connected_clients=0
        )


@router.get("/redis", response_model=RedisHealth)
async def redis_health():
    """
    Redis health check
    """
    try:
        # Placeholder Redis health check
        # In a real implementation, this would check actual Redis connectivity
        return RedisHealth(
            status="healthy",
            response_time_ms=2.0,
            connected_clients=1
        )
        
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return RedisHealth(
            status="unhealthy",
            response_time_ms=None,
            connected_clients=0
        )


@router.get("/exchanges", response_model=ExchangeHealth)
async def exchanges_health():
    """
    Exchange API health check
    """
    try:
        # This would test actual API connections
        # For now, returning mock data
        exchanges = {
            "binance": "connected",
            "bybit": "connected"
        }
        
        return ExchangeHealth(
            status="healthy",
            response_time_ms=120.0,
            exchanges=exchanges
        )
        
    except Exception as e:
        logger.error("Exchanges health check failed", error=str(e))
        return ExchangeHealth(
            status="unhealthy",
            response_time_ms=None,
            exchanges={"error": str(e)}
        )


@router.get("/system")
async def system_metrics():
    """
    System metrics and resource usage
    """
    try:
        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Process info
        process = psutil.Process()
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent()
        
        # Load average (Unix only)
        load_avg = None
        if hasattr(os, 'getloadavg'):
            load_avg = os.getloadavg()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "load_average": load_avg
            },
            "process": {
                "cpu_percent": process_cpu,
                "memory_mb": round(process_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                "threads": process.num_threads(),
                "status": process.status()
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        }
        
    except Exception as e:
        logger.error("System metrics failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch system metrics"
        )


@router.get("/detailed")
async def detailed_health_check():
    """
    Detailed health check with all service status
    """
    try:
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "services": {},
            "metrics": {}
        }
        
        # Database check
        try:
            db_client = get_db_client()
            db_result = db_client.health_check()
            health_data["services"]["database"] = db_result
        except Exception as e:
            health_data["services"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "unhealthy"
        
        # System metrics
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            health_data["metrics"] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "uptime": "unknown"  # Would calculate from process start time
            }
            
            # Mark as degraded if resources are high
            if cpu_percent > 90 or memory.percent > 90:
                health_data["status"] = "degraded"
                
        except Exception as e:
            health_data["metrics"]["error"] = str(e)
            health_data["status"] = "degraded"
        
        # Configuration check
        health_data["config"] = {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
            "supabase_configured": bool(settings.supabase_url and settings.supabase_key),
            "redis_configured": bool(settings.redis_url),
            "ai_configured": bool(settings.openrouter_api_key)
        }
        
        return health_data
        
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/readiness")
async def readiness_probe():
    """
    Kubernetes-style readiness probe
    """
    try:
        # Check if service is ready to receive traffic
        db_client = get_db_client()
        db_health = db_client.health_check()
        
        if db_health["status"] == "healthy":
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
            
    except Exception as e:
        logger.error("Readiness probe failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/liveness")
async def liveness_probe():
    """
    Kubernetes-style liveness probe
    """
    # Basic liveness check - service is running
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
