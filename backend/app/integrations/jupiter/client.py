"""
Schumacher - Jupiter Aggregator Client
Integration with Jupiter for optimal swap routing
"""

import logging
from typing import Any, Dict, List, Optional
from decimal import Decimal

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.utils.cache import cache_set, cache_get

logger = logging.getLogger(__name__)


# ============================================
# Custom Exceptions
# ============================================

class JupiterError(Exception):
    """Base exception for Jupiter client errors"""
    pass


class JupiterQuoteError(JupiterError):
    """Error getting swap quote"""
    pass


class JupiterTransactionError(JupiterError):
    """Error building swap transaction"""
    pass


class JupiterNetworkError(JupiterError):
    """Network-related errors (timeout, connection)"""
    pass


class InsufficientLiquidityError(JupiterError):
    """Not enough liquidity for the swap"""
    pass


class TokenNotFoundError(JupiterError):
    """Token not found in registry"""
    pass


# ============================================
# Token Registry (Simplified)
# ============================================

# In production, fetch from Jupiter token list API
TOKEN_MINTS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "ORCA": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "PYTH": "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3",
}

# Token decimals - critical for correct amount calculation
TOKEN_DECIMALS = {
    "SOL": 9,
    "USDC": 6,
    "USDT": 6,
    "ORCA": 6,
    "RAY": 6,
    "BONK": 5,
    "JUP": 6,
    "WIF": 6,
    "PYTH": 6,
}

# Reverse lookup: mint address -> decimals
MINT_DECIMALS = {
    "So11111111111111111111111111111111111111112": 9,  # SOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": 6,  # USDC
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": 6,  # USDT
    "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE": 6,  # ORCA
    "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R": 6,  # RAY
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": 5,  # BONK
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN": 6,  # JUP
    "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm": 6,  # WIF
    "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3": 6,  # PYTH
}


# ============================================
# Jupiter Client
# ============================================

class JupiterClient:
    """
    Client for Jupiter Aggregator API.
    Provides swap routing, quotes, and transaction building.
    """
    
    def __init__(self):
        """Initialize Jupiter client"""
        self.base_url = settings.JUPITER_API_URL
        self.price_url = settings.JUPITER_PRICE_API_URL
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
        )
        
        logger.info("Initialized Jupiter client")
    
    def _get_token_mint(self, token: str) -> str:
        """Get token mint address from symbol"""
        # If already a mint address (32-44 chars base58), return as-is
        if len(token) >= 32 and len(token) <= 44:
            return token

        # Lookup from registry
        mint = TOKEN_MINTS.get(token.upper())
        if not mint:
            raise TokenNotFoundError(f"Unknown token: {token}. Supported tokens: {', '.join(TOKEN_MINTS.keys())}")

        return mint

    def _get_token_decimals(self, token: str) -> int:
        """Get token decimals from symbol or mint address"""
        # If it's a mint address, use MINT_DECIMALS
        if len(token) >= 32 and len(token) <= 44:
            return MINT_DECIMALS.get(token, 9)  # Default to 9 if unknown

        # Otherwise use TOKEN_DECIMALS
        return TOKEN_DECIMALS.get(token.upper(), 9)  # Default to 9 if unknown

    def _parse_jupiter_error(self, response: httpx.Response) -> str:
        """Parse error message from Jupiter API response"""
        try:
            data = response.json()
            if "error" in data:
                return data["error"]
            if "message" in data:
                return data["message"]
            return f"HTTP {response.status_code}: {response.text[:200]}"
        except Exception:
            return f"HTTP {response.status_code}: {response.text[:200]}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    async def get_quote(
        self,
        source_token: str,
        dest_token: str,
        amount: float,
        slippage_bps: int = 100,
    ) -> Dict[str, Any]:
        """
        Get swap quote from Jupiter with retry logic.

        Args:
            source_token: Source token symbol or mint
            dest_token: Destination token symbol or mint
            amount: Amount to swap (in token units)
            slippage_bps: Slippage tolerance in basis points (100 = 1%)

        Returns:
            Quote data

        Raises:
            TokenNotFoundError: If token is not supported
            InsufficientLiquidityError: If not enough liquidity
            JupiterQuoteError: For other quote errors
            JupiterNetworkError: For network issues
        """
        try:
            # Validate amount
            if amount <= 0:
                raise JupiterQuoteError("Amount must be greater than 0")

            # Get mint addresses
            source_mint = self._get_token_mint(source_token)
            dest_mint = self._get_token_mint(dest_token)

            # Get correct decimals for each token
            source_decimals = self._get_token_decimals(source_token)
            dest_decimals = self._get_token_decimals(dest_token)

            # Convert amount to smallest unit using correct decimals
            amount_smallest = int(amount * (10 ** source_decimals))

            # Build request
            params = {
                "inputMint": source_mint,
                "outputMint": dest_mint,
                "amount": amount_smallest,
                "slippageBps": slippage_bps,
            }

            # Make request
            response = await self.client.get("/quote", params=params)

            # Handle errors
            if response.status_code == 400:
                error_msg = self._parse_jupiter_error(response)
                if "insufficient" in error_msg.lower() or "liquidity" in error_msg.lower():
                    raise InsufficientLiquidityError(f"Not enough liquidity for {amount} {source_token} → {dest_token}")
                raise JupiterQuoteError(f"Invalid quote request: {error_msg}")

            if response.status_code == 404:
                raise TokenNotFoundError(f"Token pair not found: {source_token} → {dest_token}")

            if response.status_code >= 500:
                raise JupiterNetworkError(f"Jupiter API server error: {response.status_code}")

            response.raise_for_status()
            data = response.json()

            # Check for empty/invalid response
            if not data or "outAmount" not in data:
                raise JupiterQuoteError("Invalid response from Jupiter API")

            # Parse response with correct output decimals
            out_amount_raw = int(data["outAmount"])
            amount_out = out_amount_raw / (10 ** dest_decimals)

            # Check for zero output (no liquidity)
            if out_amount_raw == 0:
                raise InsufficientLiquidityError(f"No route available for {amount} {source_token} → {dest_token}")

            quote = {
                "source_mint": source_mint,
                "dest_mint": dest_mint,
                "source_token": source_token.upper(),
                "dest_token": dest_token.upper(),
                "source_decimals": source_decimals,
                "dest_decimals": dest_decimals,
                "amount_in": amount,
                "amount_in_smallest": amount_smallest,
                "amount_out": amount_out,
                "amount_out_smallest": out_amount_raw,
                "price_impact": float(data.get("priceImpactPct", 0)),
                "route": data.get("routePlan", []),
                "fees": {
                    "platform_fee": float(data.get("platformFee", {}).get("amount", 0)),
                },
                "quote_data": data,  # Full quote for transaction building
            }

            logger.info(
                f"Jupiter quote: {amount} {source_token} → "
                f"{quote['amount_out']:.6f} {dest_token} "
                f"(impact: {quote['price_impact']}%)"
            )

            return quote

        except (TokenNotFoundError, InsufficientLiquidityError, JupiterQuoteError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Jupiter API timeout: {e}")
            raise JupiterNetworkError(f"Jupiter API timeout. Please try again.")
        except httpx.ConnectError as e:
            logger.error(f"Jupiter API connection error: {e}")
            raise JupiterNetworkError(f"Cannot connect to Jupiter API. Please check your connection.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Jupiter API HTTP error: {e}")
            raise JupiterQuoteError(f"Jupiter API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error getting Jupiter quote: {e}", exc_info=True)
            raise JupiterQuoteError(f"Failed to get quote: {str(e)}")
    
    async def get_all_routes(
        self,
        source_token: str,
        dest_token: str,
        amount: float,
    ) -> List[Dict[str, Any]]:
        """
        Get all available swap routes.
        
        Args:
            source_token: Source token symbol or mint
            dest_token: Destination token symbol or mint
            amount: Amount to swap
        
        Returns:
            List of routes sorted by output amount
        """
        try:
            # Get quote (Jupiter returns multiple routes)
            quote = await self.get_quote(source_token, dest_token, amount)
            
            # In production, Jupiter API returns multiple routes
            # For now, return single best route
            return [quote]
        
        except Exception as e:
            logger.error(f"Error getting all routes: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    async def build_swap_transaction(
        self,
        wallet_address: str,
        quote: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build swap transaction from quote with retry logic.

        Args:
            wallet_address: User's wallet address
            quote: Quote from get_quote()

        Returns:
            Transaction data with base64 encoded swap transaction

        Raises:
            JupiterTransactionError: If transaction building fails
            JupiterNetworkError: For network issues
        """
        try:
            # Validate inputs
            if not wallet_address or len(wallet_address) < 32:
                raise JupiterTransactionError("Invalid wallet address")

            if "quote_data" not in quote:
                raise JupiterTransactionError("Invalid quote: missing quote_data")

            # Build request
            payload = {
                "quoteResponse": quote["quote_data"],
                "userPublicKey": wallet_address,
                "wrapAndUnwrapSol": True,
                "computeUnitPriceMicroLamports": "auto",
                "dynamicComputeUnitLimit": True,
            }

            # Make request
            response = await self.client.post("/swap", json=payload)

            # Handle errors
            if response.status_code == 400:
                error_msg = self._parse_jupiter_error(response)
                raise JupiterTransactionError(f"Failed to build transaction: {error_msg}")

            if response.status_code >= 500:
                raise JupiterNetworkError(f"Jupiter API server error: {response.status_code}")

            response.raise_for_status()
            data = response.json()

            # Validate response
            if "swapTransaction" not in data:
                raise JupiterTransactionError("Invalid response: missing swapTransaction")

            logger.info(f"Built swap transaction for {wallet_address[:8]}...")

            return {
                "swap_transaction": data["swapTransaction"],
                "last_valid_block_height": data.get("lastValidBlockHeight"),
            }

        except (JupiterTransactionError, JupiterNetworkError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Jupiter API timeout building transaction: {e}")
            raise JupiterNetworkError("Jupiter API timeout. Please try again.")
        except httpx.ConnectError as e:
            logger.error(f"Jupiter API connection error: {e}")
            raise JupiterNetworkError("Cannot connect to Jupiter API. Please check your connection.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Jupiter API HTTP error: {e}")
            raise JupiterTransactionError(f"Jupiter API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error building swap transaction: {e}", exc_info=True)
            raise JupiterTransactionError(f"Failed to build transaction: {str(e)}")
    
    async def get_token_price(
        self,
        token: str,
        vs_token: str = "USDC",
    ) -> Dict[str, Any]:
        """
        Get token price from Jupiter Price API.
        
        Args:
            token: Token symbol or mint
            vs_token: Quote token (default: USDC)
        
        Returns:
            Price data
        """
        try:
            # Check cache
            cache_key = f"jupiter_price:{token}:{vs_token}"
            cached = await cache_get(cache_key)
            if cached:
                return cached
            
            # Get mint address
            token_mint = self._get_token_mint(token)
            
            # Make request to price API
            async with httpx.AsyncClient(base_url=self.price_url) as client:
                response = await client.get(
                    "/price",
                    params={"ids": token_mint}
                )
                response.raise_for_status()
                
                data = response.json()
                price_data = data["data"][token_mint]
                
                result = {
                    "token": token,
                    "mint": token_mint,
                    "price": float(price_data["price"]),
                    "timestamp": price_data.get("timestamp"),
                }
                
                # Cache for 1 minute
                await cache_set(cache_key, result, ttl=60)
                
                return result
        
        except Exception as e:
            logger.error(f"Error getting token price: {e}")
            raise
    
    async def get_multiple_prices(
        self,
        tokens: List[str],
    ) -> Dict[str, float]:
        """
        Get prices for multiple tokens.
        
        Args:
            tokens: List of token symbols
        
        Returns:
            Dictionary of {token: price}
        """
        try:
            # Get mint addresses
            mints = [self._get_token_mint(t) for t in tokens]
            
            # Make request
            async with httpx.AsyncClient(base_url=self.price_url) as client:
                response = await client.get(
                    "/price",
                    params={"ids": ",".join(mints)}
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Map back to symbols
                prices = {}
                for token, mint in zip(tokens, mints):
                    if mint in data["data"]:
                        prices[token] = float(data["data"][mint]["price"])
                
                return prices
        
        except Exception as e:
            logger.error(f"Error getting multiple prices: {e}")
            raise
    
    async def close(self):
        """Close the client"""
        await self.client.aclose()


# ============================================
# Global Client Instance
# ============================================

_jupiter_client: Optional[JupiterClient] = None


def get_jupiter_client() -> JupiterClient:
    """
    Get global Jupiter client instance.
    
    Returns:
        JupiterClient instance
    """
    global _jupiter_client
    
    if _jupiter_client is None:
        _jupiter_client = JupiterClient()
    
    return _jupiter_client


async def close_jupiter_client():
    """Close global Jupiter client"""
    global _jupiter_client
    
    if _jupiter_client:
        await _jupiter_client.close()
        _jupiter_client = None
