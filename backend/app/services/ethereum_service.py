"""
Ethereum Service - Web3.py Integration
Handles all blockchain interactions with Polygon Mumbai
Non-custodial token swaps via Uniswap V3
"""

import logging
from typing import Dict, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from web3.contract import Contract
from web3.types import TxReceipt, HexBytes
import asyncio

logger = logging.getLogger(__name__)

# Mumbai testnet configuration
MUMBAI_RPC = "https://rpc-mumbai.maticvigil.com"
MUMBAI_CHAIN_ID = 80001
MUMBAI_EXPLORER = "https://mumbai.polygonscan.com"

# Token addresses on Mumbai
TOKENS = {
    "WETH": "0x9c3C9283D3e44854697Cd22EDB54CB57F23A5A13",
    "USDC": "0x0FA8781a83E46826621b3BC094Ea2A0212e71B23",
    "USDT": "0xA02f6aDB06d98B855f8e0285c053EDA4cD51C89b",
}

# Uniswap V3 addresses
UNISWAP_V3_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
UNISWAP_V3_QUOTER = "0xb27F1EF629B4CC20b86b40d41166FAACF0E5e5DF"

# Contract ABIs (simplified)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
]

SWAP_ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "bytes", "name": "path", "type": "bytes"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                ],
                "internalType": "struct ISwapRouter.ExactInputParams",
                "name": "params",
                "type": "tuple",
            }
        ],
        "name": "exactInput",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function",
    }
]


class EthereumService:
    """Service for Ethereum/Polygon interactions"""
    
    def __init__(self, rpc_url: str = MUMBAI_RPC, contract_address: Optional[str] = None):
        """
        Initialize Ethereum service
        
        Args:
            rpc_url: RPC endpoint URL
            contract_address: NexusTrading contract address (optional for now)
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = contract_address
        self.chain_id = MUMBAI_CHAIN_ID
        self.explorer_url = MUMBAI_EXPLORER
        
        if not self.w3.is_connected():
            logger.error(f"Failed to connect to {rpc_url}")
            raise ConnectionError(f"Cannot connect to Ethereum RPC: {rpc_url}")
        
        logger.info(f"✅ Connected to Mumbai testnet (Chain ID: {self.chain_id})")
    
    async def execute_swap(
        self,
        token_in: str,
        token_out: str,
        amount: Decimal,
        user_address: str,
        min_amount_out: Decimal = Decimal(0),
        private_key: Optional[str] = None,
    ) -> Dict:
        """
        Execute a token swap on Uniswap V3
        
        Args:
            token_in: Input token address or symbol
            token_out: Output token address or symbol
            amount: Amount to swap
            user_address: User wallet address
            min_amount_out: Minimum output amount (slippage protection)
            private_key: Private key for signing (optional)
        
        Returns:
            Dict with transaction hash, status, amount_out
        """
        try:
            # Convert token symbols to addresses
            token_in_addr = self._resolve_token_address(token_in)
            token_out_addr = self._resolve_token_address(token_out)
            
            logger.info(f"🔄 Executing swap: {token_in} -> {token_out}")
            logger.info(f"   Amount: {amount}")
            
            # Format amount with decimals
            amount_wei = Web3.to_wei(float(amount), 'ether')
            min_amount_out_wei = Web3.to_wei(float(min_amount_out), 'ether')
            
            # Create transaction data
            tx_data = {
                "from": user_address,
                "to": UNISWAP_V3_ROUTER,
                "value": 0,
                "gas": 300000,
                "gasPrice": self.w3.eth.gas_price,
                "nonce": self.w3.eth.get_transaction_count(user_address),
            }
            
            # Return mock response for now (requires private key for real execution)
            return {
                "status": "pending",
                "tx_hash": "0x" + "0" * 64,  # Placeholder
                "amount_in": str(amount),
                "amount_out": str(amount * Decimal(0.99)),  # Simplified
                "token_in": token_in,
                "token_out": token_out,
                "user": user_address,
                "timestamp": asyncio.get_event_loop().time(),
                "chain": "polygon-mumbai",
            }
        
        except Exception as e:
            logger.error(f"❌ Swap execution failed: {str(e)}")
            raise
    
    async def simulate_swap(
        self,
        token_in: str,
        token_out: str,
        amount: Decimal,
    ) -> Dict:
        """
        Simulate a swap without executing it
        
        Args:
            token_in: Input token address or symbol
            token_out: Output token address or symbol
            amount: Amount to swap
        
        Returns:
            Dict with expected output, gas cost, etc.
        """
        try:
            token_in_addr = self._resolve_token_address(token_in)
            token_out_addr = self._resolve_token_address(token_out)
            amount_wei = Web3.to_wei(float(amount), 'ether')
            
            logger.info(f"📊 Simulating swap: {token_in} -> {token_out} ({amount})")
            
            # Simplified simulation (returns 99% of input as output)
            expected_output = amount * Decimal("0.99")
            
            return {
                "token_in": token_in,
                "token_out": token_out,
                "amount_in": str(amount),
                "expected_amount_out": str(expected_output),
                "slippage_percent": 1.0,
                "estimated_gas": 175000,
                "estimated_gas_cost_usd": 5.25,  # Estimated
            }
        
        except Exception as e:
            logger.error(f"❌ Swap simulation failed: {str(e)}")
            raise
    
    async def get_balance(
        self,
        token: str,
        user_address: str,
    ) -> Dict:
        """
        Get token balance for a user
        
        Args:
            token: Token address or symbol
            user_address: User wallet address
        
        Returns:
            Dict with balance and formatted balance
        """
        try:
            token_addr = self._resolve_token_address(token)
            
            # Create ERC20 contract instance
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_addr),
                abi=ERC20_ABI
            )
            
            # Get balance
            balance_wei = contract.functions.balanceOf(
                Web3.to_checksum_address(user_address)
            ).call()
            
            balance = Web3.from_wei(balance_wei, 'ether')
            
            logger.info(f"💰 Balance check: {user_address} -> {balance} {token}")
            
            return {
                "token": token,
                "user": user_address,
                "balance_wei": str(balance_wei),
                "balance": str(balance),
                "chain": "polygon-mumbai",
            }
        
        except Exception as e:
            logger.error(f"❌ Balance check failed: {str(e)}")
            raise
    
    async def get_portfolio(self, user_address: str) -> Dict:
        """
        Get portfolio data for a user
        
        Args:
            user_address: User wallet address
        
        Returns:
            Dict with portfolio balances and total value
        """
        try:
            portfolio = {
                "user": user_address,
                "tokens": {},
                "total_value_usd": 0.0,
                "chain": "polygon-mumbai",
            }
            
            # Check balance of each known token
            for token_symbol, token_addr in TOKENS.items():
                try:
                    balance_data = await self.get_balance(token_addr, user_address)
                    portfolio["tokens"][token_symbol] = balance_data["balance"]
                except:
                    portfolio["tokens"][token_symbol] = "0"
            
            logger.info(f"📋 Portfolio retrieved for {user_address}")
            
            return portfolio
        
        except Exception as e:
            logger.error(f"❌ Portfolio retrieval failed: {str(e)}")
            raise
    
    async def wait_for_confirmation(
        self,
        tx_hash: str,
        timeout_seconds: int = 300,
        poll_interval_seconds: float = 1.0,
    ) -> Dict:
        """
        Wait for a transaction to be confirmed
        
        Args:
            tx_hash: Transaction hash to track
            timeout_seconds: Max time to wait
            poll_interval_seconds: How often to check
        
        Returns:
            Dict with transaction receipt and status
        """
        try:
            tx_hash = HexBytes(tx_hash)
            start_time = asyncio.get_event_loop().time()
            
            logger.info(f"⏳ Waiting for tx confirmation: {tx_hash.hex()}")
            
            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                
                if elapsed > timeout_seconds:
                    logger.warning(f"⏱️ Transaction confirmation timeout after {timeout_seconds}s")
                    return {
                        "status": "timeout",
                        "tx_hash": tx_hash.hex(),
                    }
                
                try:
                    receipt: Optional[TxReceipt] = self.w3.eth.get_transaction_receipt(tx_hash)
                    
                    if receipt is not None:
                        is_success = receipt["status"] == 1
                        logger.info(
                            f"{'✅' if is_success else '❌'} Transaction confirmed: "
                            f"Block {receipt['blockNumber']}, "
                            f"Gas used: {receipt['gasUsed']}"
                        )
                        
                        return {
                            "status": "success" if is_success else "failed",
                            "tx_hash": tx_hash.hex(),
                            "block_number": receipt["blockNumber"],
                            "block_hash": receipt["blockHash"].hex(),
                            "gas_used": receipt["gasUsed"],
                            "gas_price": receipt["gasPrice"],
                            "transaction_fee": Web3.from_wei(
                                receipt["gasUsed"] * receipt["gasPrice"],
                                'ether'
                            ),
                            "explorer_url": f"{MUMBAI_EXPLORER}/tx/{tx_hash.hex()}",
                        }
                
                except Exception as e:
                    logger.debug(f"Transaction not yet mined: {str(e)}")
                
                await asyncio.sleep(poll_interval_seconds)
        
        except Exception as e:
            logger.error(f"❌ Transaction confirmation failed: {str(e)}")
            raise
    
    def _resolve_token_address(self, token: str) -> str:
        """
        Resolve token symbol to address
        
        Args:
            token: Token symbol or address
        
        Returns:
            Checksummed token address
        """
        # Check if it's a known symbol
        if token.upper() in TOKENS:
            return TOKENS[token.upper()]
        
        # Assume it's already an address
        if token.startswith("0x"):
            return Web3.to_checksum_address(token)
        
        raise ValueError(f"Unknown token: {token}")
    
    def get_explorer_url(self, tx_hash: str = None, address: str = None) -> str:
        """Get blockchain explorer URL for transaction or address"""
        if tx_hash:
            return f"{MUMBAI_EXPLORER}/tx/{tx_hash}"
        if address:
            return f"{MUMBAI_EXPLORER}/address/{address}"
        return MUMBAI_EXPLORER
