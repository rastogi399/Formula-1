"""
Solana Copilot - Custom Middleware
Rate limiting, logging, and security middleware
"""

import time
import logging
from typing import Callable
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================
# Rate Limiting Middleware
# ============================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse.
    Limits requests per wallet address or IP.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Store: {identifier: [(timestamp, count), ...]}
        self.request_counts: defaultdict = defaultdict(list)
        self.window_seconds = 60  # 1 minute window
        self.max_requests = settings.RATE_LIMIT_PER_MINUTE
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get identifier (wallet address from auth or IP)
        identifier = self._get_identifier(request)
        
        # Clean old entries
        current_time = time.time()
        self.request_counts[identifier] = [
            (ts, count) for ts, count in self.request_counts[identifier]
            if current_time - ts < self.window_seconds
        ]
        
        # Count requests in current window
        total_requests = sum(count for _, count in self.request_counts[identifier])
        
        # Check if rate limit exceeded
        if total_requests >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.max_requests} requests per minute allowed",
                    "retry_after": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )
        
        # Add current request
        self.request_counts[identifier].append((current_time, 1))
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.max_requests - total_requests - 1)
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(current_time + self.window_seconds)
        )
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Try to get wallet address from state (set by auth middleware)
        if hasattr(request.state, "wallet"):
            return f"wallet:{request.state.wallet}"
        
        # Fallback to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"


# ============================================
# Logging Middleware
# ============================================

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logging middleware to track all requests and responses.
    Logs request details, response status, and execution time.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging"""
        
        # Start timer
        start_time = time.time()
        
        # Get request details
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(f"→ {method} {url} from {client_ip}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"← {method} {url} - Status: {response.status_code} - "
                f"Time: {execution_time:.3f}s"
            )
            
            # Add execution time header
            response.headers["X-Process-Time"] = f"{execution_time:.3f}"
            
            return response
        
        except Exception as e:
            # Log error
            execution_time = time.time() - start_time
            logger.error(
                f"✗ {method} {url} - Error: {str(e)} - "
                f"Time: {execution_time:.3f}s",
                exc_info=True
            )
            raise


# ============================================
# Security Headers Middleware
# ============================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    Implements OWASP best practices.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy (adjust as needed)
        if settings.is_production:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.solana.com wss://api.solana.com"
            )
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        
        return response


# ============================================
# Request ID Middleware
# ============================================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request for tracing.
    Useful for debugging and log correlation.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request and response"""
        
        import uuid
        
        # Generate or use existing request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
