"""
Schumacher - Main FastAPI Application
Entry point for the backend API server
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.middleware import RateLimitMiddleware, LoggingMiddleware
from app.db.session import async_engine
from app.api.v1 import auth, chat, portfolio, transactions, automations, session_keys

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================
# Lifespan Context Manager
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup and shutdown events.
    Replaces deprecated @app.on_event decorators.
    """
    # Startup
    logger.info("🚀 Starting Schumacher API Server...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Solana Network: {settings.SOLANA_NETWORK}")
    
    # Initialize Sentry (if configured)
    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        )
        logger.info("✅ Sentry initialized")
    
    # Test database connection
    try:
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        # raise  <-- Commented out to allow startup without DB for now
    
    logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Schumacher API Server...")
    await async_engine.dispose()
    logger.info("✅ Database connections closed")


# ============================================
# Create FastAPI Application
# ============================================
app = FastAPI(
    title="Schumacher API",
    description="AI Agent Wallet for Solana - Autonomous portfolio management through conversational AI",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)


# ============================================
# Middleware Configuration
# ============================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted Host (Production only)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["solanacopilot.com", "*.solanacopilot.com"]
    )

# Custom Middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


# ============================================
# Exception Handlers
# ============================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "body": exc.body,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Don't expose internal errors in production
    if settings.is_production:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error"},
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
        },
    )


# ============================================
# API Routes
# ============================================

# Health check endpoint (no auth required)
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns 200 OK if the service is healthy.
    """
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "solana_network": settings.SOLANA_NETWORK,
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Schumacher API",
        "version": "1.0.0",
        "description": "AI Agent Wallet for Solana",
        "docs": "/docs" if not settings.is_production else "Documentation disabled in production",
        "health": "/health",
    }


# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(automations.router, prefix="/api/v1/automations", tags=["Automations"])
app.include_router(session_keys.router, prefix="/api/v1", tags=["Session Keys"])


# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD and settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
