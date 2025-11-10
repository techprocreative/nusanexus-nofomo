"""
Security middleware and utilities for NusaNexus NoFOMO
"""

import time
import hashlib
import hmac
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import redis
import jwt
from jwt import PyJWTError, ExpiredSignature, InvalidTokenError

from .config import settings

logger = structlog.get_logger()


class RateLimiter:
    """Rate limiting implementation using sliding window"""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.limits: Dict[str, Dict[str, int]] = {
            "auth": {"requests": 5, "window": 300},  # 5 requests per 5 minutes
            "api": {"requests": 100, "window": 60},  # 100 requests per minute
            "websocket": {"connections": 10, "window": 60},  # 10 connections per minute
        }
    
    def is_rate_limited(self, key: str, limit_type: str = "api") -> bool:
        """Check if request should be rate limited"""
        now = time.time()
        window = self.limits[limit_type]["window"]
        max_requests = self.limits[limit_type]["requests"]
        
        # Clean old entries
        while self.requests[key] and now - self.requests[key][0] > window:
            self.requests[key].popleft()
        
        # Check limit
        if len(self.requests[key]) >= max_requests:
            return True
        
        # Add current request
        self.requests[key].append(now)
        return False
    
    def get_remaining_requests(self, key: str, limit_type: str = "api") -> int:
        """Get remaining requests in current window"""
        now = time.time()
        window = self.limits[limit_type]["window"]
        max_requests = self.limits[limit_type]["requests"]
        
        # Clean old entries
        while self.requests[key] and now - self.requests[key][0] > window:
            self.requests[key].popleft()
        
        return max(0, max_requests - len(self.requests[key]))


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request protection"""
    
    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limiter = RateLimiter()
        self.blocked_ips: Set[str] = set()
        self.failed_attempts: Dict[str, List[float]] = defaultdict(list)
        self.max_failed_attempts = 5
        self.block_duration = 1800  # 30 minutes
        
        # CSRF protection
        self.csrf_tokens: Dict[str, datetime] = {}
        self.csrf_expiry = 3600  # 1 hour
        
        # JWT secret for custom tokens
        self.jwt_secret = settings.secret_key.encode()
        self.jwt_algorithm = "HS256"
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        try:
            # Skip security checks for certain paths
            if self._should_skip_security(request):
                response = await call_next(request)
                return response
            
            # Rate limiting
            if not self._check_rate_limit(request, client_ip):
                logger.warning("Rate limit exceeded", ip=client_ip, path=request.url.path)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": 60
                    },
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": "100",
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + 60)
                    }
                )
            
            # IP blocking check
            if client_ip in self.blocked_ips:
                logger.warning("Blocked IP attempted access", ip=client_ip)
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "IP address blocked"}
                )
            
            # CSRF protection for state-changing requests
            if self._requires_csrf_protection(request):
                if not self._validate_csrf_token(request):
                    logger.warning("CSRF token validation failed", ip=client_ip, path=request.url.path)
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"error": "CSRF token validation failed"}
                    )
            
            # Security headers
            response = await call_next(request)
            response = self._add_security_headers(response, request)
            
            # Log security events
            processing_time = time.time() - start_time
            logger.info("Request processed", 
                       ip=client_ip, 
                       path=request.url.path, 
                       method=request.method,
                       user_agent=user_agent[:100],
                       processing_time=processing_time)
            
            return response
            
        except Exception as e:
            logger.error("Security middleware error", 
                        ip=client_ip, 
                        path=request.url.path, 
                        error=str(e))
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request.client, "host") and request.client:
            return request.client.host
        
        return "unknown"
    
    def _should_skip_security(self, request: Request) -> bool:
        """Check if security checks should be skipped for this path"""
        skip_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
        }
        
        # Allow WebSocket upgrades
        if "upgrade" in request.headers.get("connection", "").lower():
            return True
        
        return request.url.path in skip_paths
    
    def _check_rate_limit(self, request: Request, client_ip: str) -> bool:
        """Check rate limiting for request"""
        # Determine rate limit type
        if "/auth/" in request.url.path:
            limit_type = "auth"
        elif "/ws" in request.url.path:
            limit_type = "websocket"
        else:
            limit_type = "api"
        
        # Use user ID if authenticated
        rate_key = client_ip
        if self._is_authenticated(request):
            try:
                token = self._extract_token(request)
                if token:
                    user_id = self._get_user_id_from_token(token)
                    if user_id:
                        rate_key = f"user:{user_id}"
            except Exception:
                pass
        
        return not self.rate_limiter.is_rate_limited(rate_key, limit_type)
    
    def _requires_csrf_protection(self, request: Request) -> bool:
        """Check if request requires CSRF protection"""
        # Only protect state-changing methods
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return False
        
        # Skip for API endpoints that use authentication
        if "/api/v1/auth/" in request.url.path and request.method == "POST":
            return False
        
        # Skip for API endpoints
        if request.url.path.startswith("/api/"):
            return True
        
        return False
    
    def _validate_csrf_token(self, request: Request) -> bool:
        """Validate CSRF token"""
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return False
        
        # Check if token exists and is not expired
        if csrf_token not in self.csrf_tokens:
            return False
        
        token_time = self.csrf_tokens[csrf_token]
        if datetime.utcnow() - token_time > timedelta(seconds=self.csrf_expiry):
            del self.csrf_tokens[csrf_token]
            return False
        
        # Validate token using HMAC
        expected_token = self._generate_csrf_token()
        if not hmac.compare_digest(csrf_token, expected_token):
            return False
        
        return True
    
    def _generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        timestamp = str(int(time.time()))
        message = f"{timestamp}:{settings.secret_key}"
        token = hmac.new(
            self.jwt_secret, 
            message.encode(), 
            hashlib.sha256
        ).hexdigest()
        return f"{timestamp}:{token}"
    
    def _is_authenticated(self, request: Request) -> bool:
        """Check if request is authenticated"""
        return bool(self._extract_token(request))
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request"""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        return None
    
    def _get_user_id_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm]
            )
            return payload.get("sub")
        except (PyJWTError, InvalidTokenError, ExpiredSignature):
            return None
    
    def _add_security_headers(self, response: Response, request: Request) -> Response:
        """Add security headers to response"""
        # CORS headers
        origin = request.headers.get("origin")
        if origin and origin in settings.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRF-Token"
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HTTPS enforcement
        if settings.debug is False:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    def generate_csrf_token(self) -> Tuple[str, datetime]:
        """Generate new CSRF token"""
        token = self._generate_csrf_token()
        expires_at = datetime.utcnow() + timedelta(seconds=self.csrf_expiry)
        self.csrf_tokens[token] = expires_at
        return token, expires_at
    
    def block_ip(self, ip: str, duration: int = None):
        """Block IP address temporarily"""
        self.blocked_ips.add(ip)
        
        def unblock():
            self.blocked_ips.discard(ip)
        
        import threading
        timer = threading.Timer(
            duration or self.block_duration, 
            unblock
        )
        timer.start()
    
    def record_failed_attempt(self, ip: str):
        """Record failed authentication attempt"""
        now = time.time()
        self.failed_attempts[ip].append(now)
        
        # Clean old attempts (older than 1 hour)
        one_hour_ago = now - 3600
        self.failed_attempts[ip] = [
            attempt for attempt in self.failed_attempts[ip] 
            if attempt > one_hour_ago
        ]
        
        # Block IP if too many failures
        if len(self.failed_attempts[ip]) >= self.max_failed_attempts:
            self.block_ip(ip)
            logger.warning("IP blocked due to repeated failures", ip=ip)
    
    def get_security_status(self) -> Dict[str, any]:
        """Get current security status"""
        return {
            "blocked_ips": len(self.blocked_ips),
            "rate_limited_ips": len(self.rate_limiter.requests),
            "csrf_tokens": len(self.csrf_tokens),
            "failed_attempts": {ip: len(attempts) for ip, attempts in self.failed_attempts.items()}
        }


class JWTMiddleware(BaseHTTPMiddleware):
    """JWT authentication middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.jwt_secret = settings.secret_key.encode()
        self.jwt_algorithm = "HS256"
        self.public_paths: Set[str] = {
            "/health",
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/api/v1/auth/oauth",
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip JWT validation for public paths
        if request.url.path in self.public_paths or request.url.path.startswith("/static/"):
            return await call_next(request)
        
        # Extract token
        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "No token provided"}
            )
        
        try:
            # Validate token
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm]
            )
            
            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.user_email = payload.get("email")
            request.state.token_payload = payload
            
            response = await call_next(request)
            return response
            
        except ExpiredSignature:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Token expired"}
            )
        except InvalidTokenError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid token"}
            )
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request"""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        return None
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt


# Global security instances
security_middleware = None
jwt_middleware = None


def init_security_middleware(app, redis_client: Optional[redis.Redis] = None):
    """Initialize security middleware"""
    global security_middleware, jwt_middleware
    
    security_middleware = SecurityMiddleware(app, redis_client)
    jwt_middleware = JWTMiddleware(app)
    
    return security_middleware, jwt_middleware


def get_security_middleware() -> SecurityMiddleware:
    """Get security middleware instance"""
    return security_middleware


def get_jwt_middleware() -> JWTMiddleware:
    """Get JWT middleware instance"""
    return jwt_middleware
