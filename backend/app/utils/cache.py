"""
Schumacher - Redis Cache Utilities
Centralized Redis client and caching utilities
"""

import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================
# Redis Client Singleton
# ============================================

class RedisClient:
    """
    Singleton Redis client for async operations.
    Provides convenient methods for caching and pub/sub.
    """
    
    _instance: Optional[Redis] = None
    
    @classmethod
    async def get_client(cls) -> Redis:
        """Get or create Redis client instance"""
        if cls._instance is None:
            cls._instance = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
            )
            logger.info("✅ Redis client initialized")
        return cls._instance
    
    @classmethod
    async def close(cls):
        """Close Redis connection"""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
            logger.info("Redis connection closed")


# Global redis client instance
redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """
    Get Redis client instance.
    Use this in FastAPI dependencies or startup.
    """
    global redis_client
    if redis_client is None:
        redis_client = await RedisClient.get_client()
    return redis_client


# ============================================
# Cache Utilities
# ============================================

async def cache_set(
    key: str,
    value: Any,
    ttl: Optional[int] = None,
    serialize: bool = True,
) -> bool:
    """
    Set value in cache with optional TTL.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (None = no expiration)
        serialize: Whether to JSON serialize the value
    
    Returns:
        True if successful
    """
    try:
        client = await get_redis()
        
        # Serialize if needed
        if serialize and not isinstance(value, (str, bytes)):
            value = json.dumps(value)
        
        # Set with or without TTL
        if ttl:
            await client.setex(key, ttl, value)
        else:
            await client.set(key, value)
        
        return True
    
    except Exception as e:
        logger.error(f"Cache set error for key {key}: {e}")
        return False


async def cache_get(
    key: str,
    deserialize: bool = True,
) -> Optional[Any]:
    """
    Get value from cache.
    
    Args:
        key: Cache key
        deserialize: Whether to JSON deserialize the value
    
    Returns:
        Cached value or None if not found
    """
    try:
        client = await get_redis()
        value = await client.get(key)
        
        if value is None:
            return None
        
        # Deserialize if needed
        if deserialize:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        
        return value
    
    except Exception as e:
        logger.error(f"Cache get error for key {key}: {e}")
        return None


async def cache_delete(key: str) -> bool:
    """
    Delete value from cache.
    
    Args:
        key: Cache key
    
    Returns:
        True if successful
    """
    try:
        client = await get_redis()
        await client.delete(key)
        return True
    
    except Exception as e:
        logger.error(f"Cache delete error for key {key}: {e}")
        return False


async def cache_exists(key: str) -> bool:
    """
    Check if key exists in cache.
    
    Args:
        key: Cache key
    
    Returns:
        True if key exists
    """
    try:
        client = await get_redis()
        return await client.exists(key) > 0
    
    except Exception as e:
        logger.error(f"Cache exists error for key {key}: {e}")
        return False


async def cache_increment(key: str, amount: int = 1) -> Optional[int]:
    """
    Increment counter in cache.
    
    Args:
        key: Cache key
        amount: Amount to increment by
    
    Returns:
        New value or None if error
    """
    try:
        client = await get_redis()
        return await client.incrby(key, amount)
    
    except Exception as e:
        logger.error(f"Cache increment error for key {key}: {e}")
        return None


async def cache_expire(key: str, ttl: int) -> bool:
    """
    Set expiration time for existing key.
    
    Args:
        key: Cache key
        ttl: Time to live in seconds
    
    Returns:
        True if successful
    """
    try:
        client = await get_redis()
        return await client.expire(key, ttl)
    
    except Exception as e:
        logger.error(f"Cache expire error for key {key}: {e}")
        return False


# ============================================
# Specialized Cache Functions
# ============================================

async def cache_price(
    token_mint: str,
    price_data: dict,
    ttl: Optional[int] = None,
) -> bool:
    """
    Cache token price data.
    
    Args:
        token_mint: Token mint address
        price_data: Price data dictionary
        ttl: TTL in seconds (default from settings)
    
    Returns:
        True if successful
    """
    key = f"price:{token_mint}"
    ttl = ttl or settings.CACHE_TTL_PRICES
    return await cache_set(key, price_data, ttl=ttl)


async def get_cached_price(token_mint: str) -> Optional[dict]:
    """
    Get cached token price.
    
    Args:
        token_mint: Token mint address
    
    Returns:
        Price data or None
    """
    key = f"price:{token_mint}"
    return await cache_get(key)


async def cache_portfolio(
    wallet_address: str,
    portfolio_data: dict,
    ttl: Optional[int] = None,
) -> bool:
    """
    Cache portfolio data.
    
    Args:
        wallet_address: Wallet address
        portfolio_data: Portfolio data dictionary
        ttl: TTL in seconds (default from settings)
    
    Returns:
        True if successful
    """
    key = f"portfolio:{wallet_address}"
    ttl = ttl or settings.CACHE_TTL_PORTFOLIO
    return await cache_set(key, portfolio_data, ttl=ttl)


async def get_cached_portfolio(wallet_address: str) -> Optional[dict]:
    """
    Get cached portfolio data.
    
    Args:
        wallet_address: Wallet address
    
    Returns:
        Portfolio data or None
    """
    key = f"portfolio:{wallet_address}"
    return await cache_get(key)


async def cache_balance(
    wallet_address: str,
    token_mint: str,
    balance: float,
    ttl: Optional[int] = None,
) -> bool:
    """
    Cache token balance.
    
    Args:
        wallet_address: Wallet address
        token_mint: Token mint address
        balance: Token balance
        ttl: TTL in seconds (default from settings)
    
    Returns:
        True if successful
    """
    key = f"balance:{wallet_address}:{token_mint}"
    ttl = ttl or settings.CACHE_TTL_BALANCES
    return await cache_set(key, balance, ttl=ttl, serialize=False)


async def get_cached_balance(
    wallet_address: str,
    token_mint: str,
) -> Optional[float]:
    """
    Get cached token balance.
    
    Args:
        wallet_address: Wallet address
        token_mint: Token mint address
    
    Returns:
        Balance or None
    """
    key = f"balance:{wallet_address}:{token_mint}"
    value = await cache_get(key, deserialize=False)
    return float(value) if value is not None else None


# ============================================
# Pub/Sub Utilities
# ============================================

async def publish_message(channel: str, message: dict) -> bool:
    """
    Publish message to Redis channel.
    
    Args:
        channel: Channel name
        message: Message dictionary
    
    Returns:
        True if successful
    """
    try:
        client = await get_redis()
        await client.publish(channel, json.dumps(message))
        return True
    
    except Exception as e:
        logger.error(f"Publish error for channel {channel}: {e}")
        return False


async def subscribe_channel(channel: str):
    """
    Subscribe to Redis channel.
    
    Args:
        channel: Channel name
    
    Yields:
        Messages from channel
    """
    client = await get_redis()
    pubsub = client.pubsub()
    
    try:
        await pubsub.subscribe(channel)
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    yield data
                except json.JSONDecodeError:
                    yield message["data"]
    
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


# ============================================
# Cache Decorators
# ============================================

def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Usage:
        @cached(ttl=600, key_prefix="user")
        async def get_user(user_id: str):
            ...
    
    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key
    
    Returns:
        Decorated function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = await cache_get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache_set(cache_key, result, ttl=ttl)
            logger.debug(f"Cache miss for {cache_key}, cached result")
            
            return result
        
        return wrapper
    return decorator
