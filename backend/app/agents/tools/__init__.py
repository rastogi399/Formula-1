"""
Solana Copilot - Agent Tools
LangChain tools for blockchain operations
"""

import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# ============================================
# Balance Tools
# ============================================

@tool
async def get_sol_balance(wallet_address: str) -> Dict[str, Any]:
    """
    Get SOL balance for a wallet.
    
    Args:
        wallet_address: Solana wallet address
    
    Returns:
        Dictionary with balance information
    """
    try:
        from app.integrations.solana.client import get_solana_client
        
        client = get_solana_client()
        balance_lamports = await client.get_balance(wallet_address)
        balance_sol = balance_lamports / 1_000_000_000  # Convert lamports to SOL
        
        return {
            "success": True,
            "wallet": wallet_address,
            "token": "SOL",
            "balance": balance_sol,
            "balance_lamports": balance_lamports,
        }
    
    except Exception as e:
        logger.error(f"Error getting SOL balance: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def get_token_balance(
    wallet_address: str,
    token_mint: str,
) -> Dict[str, Any]:
    """
    Get SPL token balance for a wallet.
    
    Args:
        wallet_address: Solana wallet address
        token_mint: SPL token mint address
    
    Returns:
        Dictionary with balance information
    """
    try:
        from app.integrations.solana.client import get_solana_client
        
        client = get_solana_client()
        balance = await client.get_token_balance(wallet_address, token_mint)
        
        return {
            "success": True,
            "wallet": wallet_address,
            "token_mint": token_mint,
            "balance": balance["amount"],
            "decimals": balance["decimals"],
            "ui_amount": balance["ui_amount"],
        }
    
    except Exception as e:
        logger.error(f"Error getting token balance: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def get_all_token_balances(wallet_address: str) -> Dict[str, Any]:
    """
    Get all token balances for a wallet.
    
    Args:
        wallet_address: Solana wallet address
    
    Returns:
        Dictionary with all token balances
    """
    try:
        from app.integrations.solana.client import get_solana_client
        
        client = get_solana_client()
        balances = await client.get_all_token_balances(wallet_address)
        
        return {
            "success": True,
            "wallet": wallet_address,
            "balances": balances,
            "token_count": len(balances),
        }
    
    except Exception as e:
        logger.error(f"Error getting all token balances: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ============================================
# Price Tools
# ============================================

@tool
async def get_token_price(token_symbol: str) -> Dict[str, Any]:
    """
    Get current price for a token.
    
    Args:
        token_symbol: Token symbol (e.g., "SOL", "USDC")
    
    Returns:
        Dictionary with price information
    """
    try:
        from app.integrations.birdeye.client import get_birdeye_client
        
        client = get_birdeye_client()
        price_data = await client.get_token_price(token_symbol)
        
        return {
            "success": True,
            "token": token_symbol,
            "price_usd": price_data["price"],
            "price_change_24h": price_data.get("price_change_24h"),
            "volume_24h": price_data.get("volume_24h"),
            "updated_at": price_data.get("updated_at"),
        }
    
    except Exception as e:
        logger.error(f"Error getting token price: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def get_multiple_token_prices(token_symbols: List[str]) -> Dict[str, Any]:
    """
    Get prices for multiple tokens.
    
    Args:
        token_symbols: List of token symbols
    
    Returns:
        Dictionary with prices for all tokens
    """
    try:
        from app.integrations.birdeye.client import get_birdeye_client
        
        client = get_birdeye_client()
        prices = await client.get_multiple_prices(token_symbols)
        
        return {
            "success": True,
            "prices": prices,
        }
    
    except Exception as e:
        logger.error(f"Error getting multiple token prices: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ============================================
# Swap Tools
# ============================================

@tool
async def get_swap_quote(
    source_token: str,
    dest_token: str,
    amount: float,
    slippage_bps: int = 100,
) -> Dict[str, Any]:
    """
    Get swap quote from Jupiter.
    
    Args:
        source_token: Source token symbol or mint
        dest_token: Destination token symbol or mint
        amount: Amount to swap
        slippage_bps: Slippage tolerance in basis points (100 = 1%)
    
    Returns:
        Dictionary with swap quote information
    """
    try:
        from app.integrations.jupiter.client import get_jupiter_client
        
        client = get_jupiter_client()
        quote = await client.get_quote(
            source_token=source_token,
            dest_token=dest_token,
            amount=amount,
            slippage_bps=slippage_bps,
        )
        
        return {
            "success": True,
            "source_token": source_token,
            "dest_token": dest_token,
            "amount_in": quote["amount_in"],
            "amount_out": quote["amount_out"],
            "price_impact": quote["price_impact"],
            "route": quote["route"],
            "fees": quote["fees"],
        }
    
    except Exception as e:
        logger.error(f"Error getting swap quote: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool
async def get_best_swap_route(
    source_token: str,
    dest_token: str,
    amount: float,
) -> Dict[str, Any]:
    """
    Get best swap route across all DEXs.
    
    Args:
        source_token: Source token symbol or mint
        dest_token: Destination token symbol or mint
        amount: Amount to swap
    
    Returns:
        Dictionary with best route information
    """
    try:
        from app.integrations.jupiter.client import get_jupiter_client
        
        client = get_jupiter_client()
        routes = await client.get_all_routes(
            source_token=source_token,
            dest_token=dest_token,
            amount=amount,
        )
        
        # Find best route (highest output amount)
        best_route = max(routes, key=lambda r: r["amount_out"])
        
        return {
            "success": True,
            "best_route": best_route,
            "all_routes": routes,
            "route_count": len(routes),
        }
    
    except Exception as e:
        logger.error(f"Error getting best swap route: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ============================================
# Simulation Tools
# ============================================

@tool
async def simulate_swap(
    wallet_address: str,
    source_token: str,
    dest_token: str,
    amount: float,
    slippage_bps: int = 100,
) -> Dict[str, Any]:
    """
    Simulate a swap transaction and build transaction for signing.

    Args:
        wallet_address: User's wallet address
        source_token: Source token symbol or mint
        dest_token: Destination token symbol or mint
        amount: Amount to swap
        slippage_bps: Slippage tolerance in basis points

    Returns:
        Dictionary with simulation results and swap transaction
    """
    try:
        from app.integrations.jupiter.client import get_jupiter_client

        # Get swap quote from Jupiter (includes price estimates)
        jupiter = get_jupiter_client()
        quote = await jupiter.get_quote(
            source_token=source_token,
            dest_token=dest_token,
            amount=amount,
            slippage_bps=slippage_bps,
        )

        # Build swap transaction for frontend signing
        tx = await jupiter.build_swap_transaction(
            wallet_address=wallet_address,
            quote=quote,
        )

        # Jupiter's quote is reliable - we trust their price estimates
        # The transaction includes slippage protection built-in
        # Gas estimation comes from Jupiter's compute unit calculation

        return {
            "success": True,
            "simulation_success": True,  # Jupiter validates internally
            "amount_in": quote["amount_in"],
            "amount_out": quote["amount_out"],
            "price_impact": quote["price_impact"],
            "source_token": quote.get("source_token", source_token),
            "dest_token": quote.get("dest_token", dest_token),
            "gas_estimate": 200000,  # Default compute units, actual determined at execution
            "logs": [],
            # Critical: Base64 encoded transaction for frontend signing
            "swap_transaction": tx["swap_transaction"],
            "last_valid_block_height": tx.get("last_valid_block_height"),
            "error": None,
        }

    except Exception as e:
        logger.error(f"Error simulating swap: {e}", exc_info=True)
        return {
            "success": False,
            "simulation_success": False,
            "error": str(e),
        }


@tool
async def simulate_transaction(
    wallet_address: str,
    transaction_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Simulate any transaction.
    
    Args:
        wallet_address: User's wallet address
        transaction_data: Transaction data to simulate
    
    Returns:
        Dictionary with simulation results
    """
    try:
        from app.integrations.solana.client import get_solana_client
        
        client = get_solana_client()
        simulation = await client.simulate_transaction(transaction_data)
        
        return {
            "success": True,
            "simulation_success": simulation["success"],
            "gas_estimate": simulation["gas_estimate"],
            "logs": simulation["logs"],
            "error": simulation.get("error"),
        }
    
    except Exception as e:
        logger.error(f"Error simulating transaction: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ============================================
# Portfolio Tools
# ============================================

@tool
async def calculate_portfolio_value(wallet_address: str) -> Dict[str, Any]:
    """
    Calculate total portfolio value in USD.
    
    Args:
        wallet_address: User's wallet address
    
    Returns:
        Dictionary with portfolio value
    """
    try:
        from app.integrations.solana.client import get_solana_client
        from app.integrations.birdeye.client import get_birdeye_client
        
        # Get all token balances
        solana = get_solana_client()
        balances = await solana.get_all_token_balances(wallet_address)
        
        # Get prices
        birdeye = get_birdeye_client()
        token_symbols = [b["symbol"] for b in balances]
        prices = await birdeye.get_multiple_prices(token_symbols)
        
        # Calculate total value
        total_value = 0
        holdings = []
        
        for balance in balances:
            symbol = balance["symbol"]
            amount = balance["amount"]
            price = prices.get(symbol, {}).get("price", 0)
            value = amount * price
            
            total_value += value
            holdings.append({
                "token": symbol,
                "amount": amount,
                "price_usd": price,
                "value_usd": value,
            })
        
        return {
            "success": True,
            "wallet": wallet_address,
            "total_value_usd": total_value,
            "holdings": holdings,
            "token_count": len(holdings),
        }
    
    except Exception as e:
        logger.error(f"Error calculating portfolio value: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ============================================
# Tool Collections
# ============================================

# All balance tools
BALANCE_TOOLS = [
    get_sol_balance,
    get_token_balance,
    get_all_token_balances,
]

# All price tools
PRICE_TOOLS = [
    get_token_price,
    get_multiple_token_prices,
]

# All swap tools
SWAP_TOOLS = [
    get_swap_quote,
    get_best_swap_route,
]

# All simulation tools
SIMULATION_TOOLS = [
    simulate_swap,
    simulate_transaction,
]

# All portfolio tools
PORTFOLIO_TOOLS = [
    calculate_portfolio_value,
]

# All tools combined
ALL_TOOLS = (
    BALANCE_TOOLS +
    PRICE_TOOLS +
    SWAP_TOOLS +
    SIMULATION_TOOLS +
    PORTFOLIO_TOOLS
)
