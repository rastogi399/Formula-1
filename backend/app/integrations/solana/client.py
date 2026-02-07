"""
Schumacher - Solana RPC Client
Wrapper for Solana blockchain operations using Helius RPC
"""

import logging
from typing import Any, Dict, List, Optional
from decimal import Decimal

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Finalized
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.signature import Signature
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID

from app.core.config import settings
from app.utils.cache import cache_balance, get_cached_balance

logger = logging.getLogger(__name__)


# ============================================
# Solana Client
# ============================================

class SolanaClient:
    """
    Async Solana RPC client with caching and error handling.
    Uses Helius RPC for better performance and reliability.
    """
    
    def __init__(self):
        """Initialize Solana client"""
        # Use Helius if available, otherwise fallback to public RPC
        rpc_url = settings.helius_rpc_url_with_key or settings.SOLANA_RPC_URL
        
        self.client = AsyncClient(
            rpc_url,
            commitment=Confirmed,
        )
        
        logger.info(f"Initialized Solana client: {settings.SOLANA_NETWORK}")
    
    async def get_balance(self, wallet_address: str) -> int:
        """
        Get SOL balance in lamports.
        
        Args:
            wallet_address: Wallet public key
        
        Returns:
            Balance in lamports (1 SOL = 1,000,000,000 lamports)
        """
        try:
            # Check cache first
            cached = await get_cached_balance(wallet_address, "SOL")
            if cached is not None:
                return int(cached * 1_000_000_000)
            
            # Fetch from RPC
            pubkey = Pubkey.from_string(wallet_address)
            response = await self.client.get_balance(pubkey)
            balance_lamports = response.value
            
            # Cache result
            balance_sol = balance_lamports / 1_000_000_000
            await cache_balance(wallet_address, "SOL", balance_sol)
            
            return balance_lamports
        
        except Exception as e:
            logger.error(f"Error getting balance for {wallet_address}: {e}")
            raise
    
    async def get_token_balance(
        self,
        wallet_address: str,
        token_mint: str,
    ) -> Dict[str, Any]:
        """
        Get SPL token balance.
        
        Args:
            wallet_address: Wallet public key
            token_mint: Token mint address
        
        Returns:
            Dictionary with balance info
        """
        try:
            # Check cache
            cached = await get_cached_balance(wallet_address, token_mint)
            if cached is not None:
                return {
                    "amount": cached,
                    "decimals": 9,  # Default, should be fetched
                    "ui_amount": cached,
                }
            
            # Get token accounts
            pubkey = Pubkey.from_string(wallet_address)
            mint_pubkey = Pubkey.from_string(token_mint)
            
            response = await self.client.get_token_accounts_by_owner(
                pubkey,
                {"mint": mint_pubkey},
            )
            
            if not response.value:
                return {
                    "amount": 0,
                    "decimals": 0,
                    "ui_amount": 0,
                }
            
            # Get balance from first account
            token_account = response.value[0]
            balance_response = await self.client.get_token_account_balance(
                token_account.pubkey
            )
            
            balance_data = balance_response.value
            
            # Cache result
            await cache_balance(
                wallet_address,
                token_mint,
                float(balance_data.ui_amount or 0)
            )
            
            return {
                "amount": int(balance_data.amount),
                "decimals": balance_data.decimals,
                "ui_amount": float(balance_data.ui_amount or 0),
            }
        
        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            raise
    
    async def get_all_token_balances(
        self,
        wallet_address: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all SPL token balances for a wallet.
        
        Args:
            wallet_address: Wallet public key
        
        Returns:
            List of token balances
        """
        try:
            pubkey = Pubkey.from_string(wallet_address)
            
            # Get all token accounts
            response = await self.client.get_token_accounts_by_owner(
                pubkey,
                {"programId": TOKEN_PROGRAM_ID},
            )
            
            balances = []
            
            for account in response.value:
                try:
                    # Get balance for each account
                    balance_response = await self.client.get_token_account_balance(
                        account.pubkey
                    )
                    
                    balance_data = balance_response.value
                    
                    # Get mint address from account data
                    # Note: This is simplified - in production, parse account data properly
                    mint = str(account.account.data)  # Placeholder
                    
                    balances.append({
                        "mint": mint,
                        "symbol": "UNKNOWN",  # Should lookup from token registry
                        "amount": float(balance_data.ui_amount or 0),
                        "decimals": balance_data.decimals,
                    })
                
                except Exception as e:
                    logger.warning(f"Error processing token account: {e}")
                    continue
            
            return balances
        
        except Exception as e:
            logger.error(f"Error getting all token balances: {e}")
            raise
    
    async def simulate_transaction(
        self,
        transaction: Transaction,
    ) -> Dict[str, Any]:
        """
        Simulate a transaction before execution.
        
        Args:
            transaction: Transaction to simulate
        
        Returns:
            Simulation result
        """
        try:
            response = await self.client.simulate_transaction(transaction)
            
            return {
                "success": response.value.err is None,
                "logs": response.value.logs,
                "gas_estimate": response.value.units_consumed or 0,
                "error": str(response.value.err) if response.value.err else None,
            }
        
        except Exception as e:
            logger.error(f"Error simulating transaction: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def send_transaction(
        self,
        transaction: Transaction,
        signers: List[Keypair],
    ) -> str:
        """
        Send a transaction to the network.
        
        Args:
            transaction: Signed transaction
            signers: List of signers
        
        Returns:
            Transaction signature
        """
        try:
            response = await self.client.send_transaction(
                transaction,
                *signers,
            )
            
            signature = str(response.value)
            logger.info(f"Transaction sent: {signature}")
            
            return signature
        
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            raise
    
    async def confirm_transaction(
        self,
        signature: str,
        commitment: str = "confirmed",
    ) -> bool:
        """
        Wait for transaction confirmation.
        
        Args:
            signature: Transaction signature
            commitment: Commitment level
        
        Returns:
            True if confirmed successfully
        """
        try:
            sig = Signature.from_string(signature)
            
            response = await self.client.confirm_transaction(
                sig,
                commitment=Finalized if commitment == "finalized" else Confirmed,
            )
            
            return response.value
        
        except Exception as e:
            logger.error(f"Error confirming transaction: {e}")
            return False
    
    async def get_recent_blockhash(self) -> str:
        """Get recent blockhash for transactions"""
        try:
            response = await self.client.get_latest_blockhash()
            return str(response.value.blockhash)
        
        except Exception as e:
            logger.error(f"Error getting recent blockhash: {e}")
            raise
    
    async def close(self):
        """Close the client connection"""
        await self.client.close()


# ============================================
# Global Client Instance
# ============================================

_solana_client: Optional[SolanaClient] = None


def get_solana_client() -> SolanaClient:
    """
    Get global Solana client instance.
    
    Returns:
        SolanaClient instance
    """
    global _solana_client
    
    if _solana_client is None:
        _solana_client = SolanaClient()
    
    return _solana_client


async def close_solana_client():
    """Close global Solana client"""
    global _solana_client
    
    if _solana_client:
        await _solana_client.close()
        _solana_client = None
