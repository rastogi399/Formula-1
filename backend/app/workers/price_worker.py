"""
Schumacher - Price Worker
Updates token prices in cache for fast API responses
"""

import logging
from typing import Dict, Any

from app.workers.celery_app import celery_app
from app.integrations.birdeye.client import get_birdeye_client
from app.integrations.jupiter.client import get_jupiter_client
from app.utils.cache import cache_price

logger = logging.getLogger(__name__)

# Top tokens to track (can be expanded)
TRACKED_TOKENS = [
    "So11111111111111111111111111111111111111112",  # SOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
    "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",  # ETH (Wormhole)
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",  # mSOL
    "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj",  # stSOL
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",  # JUP
]


@celery_app.task(name="app.workers.price_worker.update_all_prices")
def update_all_prices():
    """
    Periodic task to update prices for tracked tokens.
    Runs every 30 seconds via Celery Beat.
    """
    logger.info("Updating token prices...")
    
    try:
        # Get prices from Birdeye
        birdeye = get_birdeye_client()
        prices = await birdeye.get_multiple_prices(TRACKED_TOKENS)
        
        # Also get from Jupiter as backup
        jupiter = get_jupiter_client()
        jupiter_prices = await jupiter.get_multiple_prices(TRACKED_TOKENS)
        
        # Cache all prices
        cached_count = 0
        for mint in TRACKED_TOKENS:
            try:
                # Use Birdeye price if available, otherwise Jupiter
                price_data = prices.get(mint) or jupiter_prices.get(mint)
                
                if price_data:
                    await cache_price(mint, price_data)
                    cached_count += 1
                    logger.debug(f"Cached price for {mint}: ${price_data.get('price', 0)}")
            
            except Exception as e:
                logger.error(f"Failed to cache price for {mint}: {e}")
        
        logger.info(f"Successfully updated {cached_count}/{len(TRACKED_TOKENS)} prices")
        
        return {
            "success": True,
            "updated": cached_count,
            "total": len(TRACKED_TOKENS),
        }
    
    except Exception as e:
        logger.error(f"Failed to update prices: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@celery_app.task(name="app.workers.price_worker.update_single_price")
def update_single_price(mint: str):
    """
    Update price for a single token.
    
    Args:
        mint: Token mint address
    """
    logger.info(f"Updating price for token: {mint}")
    
    try:
        birdeye = get_birdeye_client()
        price_data = await birdeye.get_token_price(mint)
        
        if price_data:
            await cache_price(mint, price_data)
            logger.info(f"Price updated: {mint} = ${price_data.get('price', 0)}")
            return {"success": True, "price": price_data}
        
        return {"success": False, "error": "No price data"}
    
    except Exception as e:
        logger.error(f"Failed to update price: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
