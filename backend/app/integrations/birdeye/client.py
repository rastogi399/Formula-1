"""
Schumacher - Birdeye API Client
Real-time price feeds and market data for Solana tokens
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import httpx

from app.core.config import settings
from app.utils.cache import cache_price, get_cached_price

logger = logging.getLogger(__name__)


# ============================================
# Birdeye Client
# ============================================

class BirdeyeClient:
    """
    Client for Birdeye API.
    Provides real-time price feeds, historical data, and market analytics.
    """
    
    def __init__(self):
        """Initialize Birdeye client"""
        self.base_url = settings.BIRDEYE_API_URL
        self.api_key = settings.BIRDEYE_API_KEY
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-API-KEY": self.api_key,
                "Accept": "application/json",
            } if self.api_key else {},
            timeout=30.0,
        )
        
        logger.info("Initialized Birdeye client")
    
    async def get_token_price(
        self,
        token_address: str,
    ) -> Dict[str, Any]:
        """
        Get current token price.
        
        Args:
            token_address: Token mint address or symbol
        
        Returns:
            Price data
        """
        try:
            # Check cache first
            cached = await get_cached_price(token_address)
            if cached:
                return cached
            
            # Make request
            response = await self.client.get(
                f"/defi/price",
                params={"address": token_address}
            )
            response.raise_for_status()
            
            data = response.json()
            
            price_data = {
                "token": token_address,
                "price": float(data["data"]["value"]),
                "price_change_24h": float(data["data"].get("priceChange24h", 0)),
                "volume_24h": float(data["data"].get("volume24h", 0)),
                "liquidity": float(data["data"].get("liquidity", 0)),
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            # Cache for 5 minutes
            await cache_price(token_address, price_data, ttl=300)
            
            logger.info(f"Birdeye price for {token_address}: ${price_data['price']}")
            
            return price_data
        
        except httpx.HTTPError as e:
            logger.error(f"Birdeye API error: {e}")
            # Fallback to CoinGecko
            return await self._get_price_from_coingecko(token_address)
        except Exception as e:
            logger.error(f"Error getting token price: {e}")
            raise
    
    async def get_multiple_prices(
        self,
        token_addresses: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get prices for multiple tokens.
        
        Args:
            token_addresses: List of token addresses
        
        Returns:
            Dictionary of {address: price_data}
        """
        try:
            # Make request
            response = await self.client.get(
                "/defi/multi_price",
                params={"list_address": ",".join(token_addresses)}
            )
            response.raise_for_status()
            
            data = response.json()
            
            prices = {}
            for token_data in data["data"]:
                address = token_data["address"]
                prices[address] = {
                    "price": float(token_data["value"]),
                    "price_change_24h": float(token_data.get("priceChange24h", 0)),
                    "updated_at": datetime.utcnow().isoformat(),
                }
                
                # Cache each price
                await cache_price(address, prices[address], ttl=300)
            
            return prices
        
        except Exception as e:
            logger.error(f"Error getting multiple prices: {e}")
            raise
    
    async def get_token_ohlcv(
        self,
        token_address: str,
        timeframe: str = "1D",
        limit: int = 90,
    ) -> List[Dict[str, Any]]:
        """
        Get OHLCV (candlestick) data for token.
        
        Args:
            token_address: Token mint address
            timeframe: Timeframe (1m, 5m, 15m, 1H, 4H, 1D)
            limit: Number of candles
        
        Returns:
            List of OHLCV data
        """
        try:
            response = await self.client.get(
                "/defi/ohlcv",
                params={
                    "address": token_address,
                    "type": timeframe,
                    "time_from": int((datetime.utcnow() - timedelta(days=limit)).timestamp()),
                    "time_to": int(datetime.utcnow().timestamp()),
                }
            )
            response.raise_for_status()
            
            data = response.json()
            
            ohlcv = []
            for item in data["data"]["items"]:
                ohlcv.append({
                    "timestamp": item["unixTime"],
                    "open": float(item["o"]),
                    "high": float(item["h"]),
                    "low": float(item["l"]),
                    "close": float(item["c"]),
                    "volume": float(item["v"]),
                })
            
            return ohlcv
        
        except Exception as e:
            logger.error(f"Error getting OHLCV data: {e}")
            raise
    
    async def get_token_metadata(
        self,
        token_address: str,
    ) -> Dict[str, Any]:
        """
        Get token metadata (name, symbol, decimals, etc.).
        
        Args:
            token_address: Token mint address
        
        Returns:
            Token metadata
        """
        try:
            response = await self.client.get(
                "/defi/token_overview",
                params={"address": token_address}
            )
            response.raise_for_status()
            
            data = response.json()
            token_data = data["data"]
            
            return {
                "address": token_address,
                "symbol": token_data.get("symbol"),
                "name": token_data.get("name"),
                "decimals": token_data.get("decimals"),
                "logo_uri": token_data.get("logoURI"),
                "market_cap": float(token_data.get("mc", 0)),
                "total_supply": float(token_data.get("supply", 0)),
            }
        
        except Exception as e:
            logger.error(f"Error getting token metadata: {e}")
            raise
    
    async def _get_price_from_coingecko(
        self,
        token_address: str,
    ) -> Dict[str, Any]:
        """
        Fallback to CoinGecko for price data.
        
        Args:
            token_address: Token address
        
        Returns:
            Price data
        """
        try:
            async with httpx.AsyncClient(
                base_url=settings.COINGECKO_API_URL,
                timeout=30.0,
            ) as client:
                # Note: CoinGecko requires token ID, not address
                # This is simplified - in production, maintain a mapping
                response = await client.get(
                    f"/simple/price",
                    params={
                        "ids": "solana",  # Placeholder
                        "vs_currencies": "usd",
                        "include_24hr_change": "true",
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                
                return {
                    "token": token_address,
                    "price": float(data["solana"]["usd"]),
                    "price_change_24h": float(data["solana"].get("usd_24h_change", 0)),
                    "updated_at": datetime.utcnow().isoformat(),
                    "source": "coingecko",
                }
        
        except Exception as e:
            logger.error(f"CoinGecko fallback error: {e}")
            raise
    
    async def close(self):
        """Close the client"""
        await self.client.aclose()


# ============================================
# Global Client Instance
# ============================================

_birdeye_client: Optional[BirdeyeClient] = None


def get_birdeye_client() -> BirdeyeClient:
    """
    Get global Birdeye client instance.
    
    Returns:
        BirdeyeClient instance
    """
    global _birdeye_client
    
    if _birdeye_client is None:
        _birdeye_client = BirdeyeClient()
    
    return _birdeye_client


async def close_birdeye_client():
    """Close global Birdeye client"""
    global _birdeye_client
    
    if _birdeye_client:
        await _birdeye_client.close()
        _birdeye_client = None
