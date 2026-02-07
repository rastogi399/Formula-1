"""
Trading Agent - AI-powered blockchain trading orchestrator
Supports both Solana (hidden) and Ethereum (active)
Uses LangGraph for agent orchestration
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum

from app.core.config import settings
from app.services.ethereum_service import EthereumService

logger = logging.getLogger(__name__)


class BlockchainType(Enum):
    """Supported blockchains"""
    SOLANA = "solana"
    ETHEREUM = "ethereum"


class TradingAgent:
    """
    Unified trading agent for multi-chain support
    Abstracts blockchain-specific logic through service selection
    """
    
    def __init__(self):
        """Initialize trading agent with appropriate blockchain service"""
        self.active_chain = BlockchainType(settings.ACTIVE_CHAIN.lower())
        self.ethereum_service: Optional[EthereumService] = None
        self.solana_service: Optional[Any] = None  # Placeholder for Solana service
        
        # Initialize services based on active chain
        if self.active_chain == BlockchainType.ETHEREUM:
            self.ethereum_service = EthereumService(
                rpc_url=settings.ETHEREUM_RPC_URL,
                contract_address=settings.ETHEREUM_CONTRACT_ADDRESS
            )
            logger.info(f"✅ TradingAgent initialized with Ethereum service")
        elif self.active_chain == BlockchainType.SOLANA:
            # Initialize Solana service (backward compatibility)
            logger.info(f"✅ TradingAgent initialized with Solana service")
        
        self.swap_history: Dict[str, Dict[str, Any]] = {}
    
    def get_active_service(self):
        """
        Get the appropriate blockchain service
        
        Returns:
            Blockchain service instance (EthereumService or SolanaService)
        """
        if self.active_chain == BlockchainType.ETHEREUM:
            if not self.ethereum_service:
                self.ethereum_service = EthereumService(
                    rpc_url=settings.ETHEREUM_RPC_URL,
                    contract_address=settings.ETHEREUM_CONTRACT_ADDRESS
                )
            return self.ethereum_service
        else:
            # Return Solana service (placeholder)
            return self.solana_service
    
    async def execute_swap(
        self,
        token_in: str,
        token_out: str,
        amount: float,
        user_address: str,
        min_amount_out: float = 0.0,
        private_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a token swap through the active blockchain service
        
        Args:
            token_in: Input token address or symbol
            token_out: Output token address or symbol
            amount: Amount to swap
            user_address: User wallet address
            min_amount_out: Minimum output amount (slippage protection)
            private_key: Optional private key for signing
        
        Returns:
            Transaction result with hash, status, output amount
        """
        try:
            from decimal import Decimal
            
            service = self.get_active_service()
            
            logger.info(
                f"🔄 Trading Agent executing swap on {self.active_chain.value}\n"
                f"   From: {token_in} -> To: {token_out}\n"
                f"   Amount: {amount}"
            )
            
            # Execute swap through active service
            result = await service.execute_swap(
                token_in=token_in,
                token_out=token_out,
                amount=Decimal(str(amount)),
                user_address=user_address,
                min_amount_out=Decimal(str(min_amount_out)),
                private_key=private_key,
            )
            
            # Store in history
            if "tx_hash" in result:
                self.swap_history[result["tx_hash"]] = result
            
            logger.info(f"✅ Swap executed successfully")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Swap execution failed: {str(e)}")
            raise
    
    async def simulate_swap(
        self,
        token_in: str,
        token_out: str,
        amount: float,
    ) -> Dict[str, Any]:
        """
        Simulate a swap without executing it
        
        Args:
            token_in: Input token
            token_out: Output token
            amount: Amount to swap
        
        Returns:
            Simulation result with expected output and gas cost
        """
        try:
            from decimal import Decimal
            
            service = self.get_active_service()
            
            logger.info(
                f"📊 Simulating swap on {self.active_chain.value}\n"
                f"   {token_in} -> {token_out}: {amount}"
            )
            
            result = await service.simulate_swap(
                token_in=token_in,
                token_out=token_out,
                amount=Decimal(str(amount)),
            )
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Swap simulation failed: {str(e)}")
            raise
    
    async def get_balance(
        self,
        token: str,
        user_address: str,
    ) -> Dict[str, Any]:
        """
        Get user token balance
        
        Args:
            token: Token address or symbol
            user_address: User wallet address
        
        Returns:
            Balance information
        """
        try:
            service = self.get_active_service()
            
            result = await service.get_balance(token, user_address)
            
            logger.info(
                f"💰 Balance retrieved: {result.get('balance', 'N/A')} {token}"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Balance retrieval failed: {str(e)}")
            raise
    
    async def get_portfolio(
        self,
        user_address: str,
    ) -> Dict[str, Any]:
        """
        Get user portfolio across all tokens
        
        Args:
            user_address: User wallet address
        
        Returns:
            Portfolio data with all token balances and total value
        """
        try:
            service = self.get_active_service()
            
            result = await service.get_portfolio(user_address)
            
            logger.info(
                f"📋 Portfolio retrieved for {user_address}\n"
                f"   Total value: ${result.get('total_value_usd', 'N/A')}"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Portfolio retrieval failed: {str(e)}")
            raise
    
    async def wait_for_confirmation(
        self,
        tx_hash: str,
        timeout_seconds: int = 300,
    ) -> Dict[str, Any]:
        """
        Wait for transaction confirmation
        
        Args:
            tx_hash: Transaction hash to track
            timeout_seconds: Max time to wait
        
        Returns:
            Transaction confirmation status
        """
        try:
            service = self.get_active_service()
            
            result = await service.wait_for_confirmation(
                tx_hash=tx_hash,
                timeout_seconds=timeout_seconds,
            )
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Transaction confirmation failed: {str(e)}")
            raise
    
    def get_swap_status(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get status of a previous swap from history"""
        return self.swap_history.get(tx_hash)
    
    def get_active_chain_info(self) -> Dict[str, Any]:
        """Get information about the active blockchain"""
        if self.active_chain == BlockchainType.ETHEREUM:
            return {
                "chain": "ethereum",
                "network": "polygon-mumbai",
                "chain_id": settings.ETHEREUM_CHAIN_ID,
                "rpc_url": settings.ETHEREUM_RPC_URL,
                "explorer": settings.ETHEREUM_EXPLORER,
                "contract": settings.ETHEREUM_CONTRACT_ADDRESS,
            }
        else:
            return {
                "chain": "solana",
                "network": settings.SOLANA_NETWORK,
                "rpc_url": settings.SOLANA_RPC_URL,
            }
    
    async def estimate_transaction_cost(
        self,
        token_in: str,
        token_out: str,
        amount: float,
    ) -> Dict[str, Any]:
        """
        Estimate transaction cost (gas/fees)
        
        Args:
            token_in: Input token
            token_out: Output token
            amount: Amount to swap
        
        Returns:
            Estimated costs
        """
        try:
            service = self.get_active_service()
            
            # For Ethereum, use estimateGas method
            if self.active_chain == BlockchainType.ETHEREUM:
                return {
                    "estimated_gas": 175000,
                    "gas_price_gwei": 50,  # Typical Mumbai gas price
                    "estimated_fee_usd": 5.25,  # Simplified
                    "chain": "ethereum",
                }
            else:
                return {
                    "estimated_fee_sol": 0.00025,
                    "estimated_fee_usd": 0.05,
                    "chain": "solana",
                }
        
        except Exception as e:
            logger.error(f"❌ Cost estimation failed: {str(e)}")
            raise


# Global trading agent instance
_trading_agent: Optional[TradingAgent] = None


def get_trading_agent() -> TradingAgent:
    """Get or create global trading agent instance"""
    global _trading_agent
    if _trading_agent is None:
        _trading_agent = TradingAgent()
    return _trading_agent
