"""
Vault Deployment Service - Handles on-chain DCA Vault creation via Anchor program
Integrates with the dca-vault Anchor program to create and manage vaults
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction
from solders.transaction import Transaction
from solders.message import Message
from solders.system_program import ID as SYSTEM_PROGRAM_ID
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from spl.token.constants import TOKEN_PROGRAM_ID

from app.core.config import settings

logger = logging.getLogger(__name__)

# Program IDs
DCA_VAULT_PROGRAM_ID = Pubkey.from_string("DCAvau1tXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

# Common token mints (Mainnet addresses)
TOKEN_MINTS = {
    "SOL": Pubkey.from_string("So11111111111111111111111111111111111111112"),
    "USDC": Pubkey.from_string("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
    "USDT": Pubkey.from_string("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"),
}


@dataclass
class VaultDeploymentResult:
    """Result of vault deployment"""
    success: bool
    vault_pda: Optional[str] = None
    transaction_hash: Optional[str] = None
    error: Optional[str] = None


class VaultDeploymentService:
    """
    Service for deploying and managing on-chain DCA vaults.
    Uses the dca-vault Anchor program.
    """
    
    def __init__(self, rpc_url: str = None):
        self.rpc_url = rpc_url or settings.SOLANA_RPC_URL
        self.client: Optional[AsyncClient] = None
        
    async def connect(self):
        """Initialize RPC connection"""
        self.client = AsyncClient(self.rpc_url, commitment=Confirmed)
        
    async def disconnect(self):
        """Close RPC connection"""
        if self.client:
            await self.client.close()
            
    def derive_vault_pda(
        self,
        owner: str,
        source_mint: str,
        dest_mint: str,
    ) -> tuple[str, int]:
        """
        Derive the PDA address for a DCA vault.
        
        Args:
            owner: Owner wallet address
            source_mint: Source token mint address
            dest_mint: Destination token mint address
            
        Returns:
            Tuple of (vault_pda_address, bump)
        """
        owner_pubkey = Pubkey.from_string(owner)
        source_pubkey = self._resolve_mint(source_mint)
        dest_pubkey = self._resolve_mint(dest_mint)
        
        seeds = [
            b"vault",
            bytes(owner_pubkey),
            bytes(source_pubkey),
            bytes(dest_pubkey),
        ]
        
        pda, bump = Pubkey.find_program_address(seeds, DCA_VAULT_PROGRAM_ID)
        return str(pda), bump
    
    def _resolve_mint(self, token: str) -> Pubkey:
        """Resolve token symbol or address to Pubkey"""
        # Check if it's a known symbol
        if token.upper() in TOKEN_MINTS:
            return TOKEN_MINTS[token.upper()]
        # Otherwise assume it's an address
        return Pubkey.from_string(token)
    
    async def deploy_vault(
        self,
        owner_address: str,
        source_token: str,
        dest_token: str,
        amount_per_cycle: int,
        frequency_seconds: int,
        total_cycles: int,
    ) -> VaultDeploymentResult:
        """
        Deploy a new DCA vault on-chain.
        
        Args:
            owner_address: Owner wallet address
            source_token: Source token mint (symbol or address)
            dest_token: Destination token mint (symbol or address)
            amount_per_cycle: Amount to swap each cycle (in smallest units)
            frequency_seconds: Interval between cycles
            total_cycles: Total number of DCA cycles
            
        Returns:
            Deployment result with vault PDA and transaction hash
        """
        try:
            # Derive vault PDA
            vault_pda, bump = self.derive_vault_pda(owner_address, source_token, dest_token)
            
            logger.info(f"Deploying vault: {vault_pda}")
            logger.info(f"  Owner: {owner_address}")
            logger.info(f"  Source: {source_token}")
            logger.info(f"  Dest: {dest_token}")
            logger.info(f"  Amount/cycle: {amount_per_cycle}")
            logger.info(f"  Frequency: {frequency_seconds}s")
            logger.info(f"  Total cycles: {total_cycles}")
            
            # In production, this would:
            # 1. Build the initialize_vault instruction
            # 2. Create the transaction
            # 3. Return unsigned transaction for user to sign via wallet
            # 4. Submit signed transaction
            
            # For now, return the vault PDA (user would sign via frontend wallet)
            return VaultDeploymentResult(
                success=True,
                vault_pda=vault_pda,
                transaction_hash=None,  # Will be set after user signs
            )
            
        except Exception as e:
            logger.error(f"Failed to deploy vault: {e}")
            return VaultDeploymentResult(
                success=False,
                error=str(e),
            )
    
    async def build_initialize_instruction(
        self,
        owner: str,
        source_mint: str,
        dest_mint: str,
        amount_per_cycle: int,
        frequency_seconds: int,
        total_cycles: int,
    ) -> Dict[str, Any]:
        """
        Build the initialize_vault instruction data for frontend signing.
        
        Returns instruction data that frontend can use to build and sign transaction.
        """
        vault_pda, bump = self.derive_vault_pda(owner, source_mint, dest_mint)
        
        source_pubkey = self._resolve_mint(source_mint)
        dest_pubkey = self._resolve_mint(dest_mint)
        
        return {
            "program_id": str(DCA_VAULT_PROGRAM_ID),
            "instruction": "initialize_vault",
            "accounts": {
                "vault": vault_pda,
                "owner": owner,
                "source_mint": str(source_pubkey),
                "dest_mint": str(dest_pubkey),
                "system_program": str(SYSTEM_PROGRAM_ID),
            },
            "args": {
                "amount_per_cycle": amount_per_cycle,
                "frequency_seconds": frequency_seconds,
                "total_cycles": total_cycles,
            },
        }
    
    async def build_pause_instruction(self, owner: str, vault_pda: str) -> Dict[str, Any]:
        """Build pause_vault instruction data"""
        return {
            "program_id": str(DCA_VAULT_PROGRAM_ID),
            "instruction": "pause_vault",
            "accounts": {
                "vault": vault_pda,
                "owner": owner,
            },
            "args": {},
        }
    
    async def build_resume_instruction(self, owner: str, vault_pda: str) -> Dict[str, Any]:
        """Build resume_vault instruction data"""
        return {
            "program_id": str(DCA_VAULT_PROGRAM_ID),
            "instruction": "resume_vault",
            "accounts": {
                "vault": vault_pda,
                "owner": owner,
            },
            "args": {},
        }
    
    async def build_close_instruction(
        self,
        owner: str,
        vault_pda: str,
        vault_token_account: str,
        owner_token_account: str,
    ) -> Dict[str, Any]:
        """Build close_vault instruction data"""
        return {
            "program_id": str(DCA_VAULT_PROGRAM_ID),
            "instruction": "close_vault",
            "accounts": {
                "vault": vault_pda,
                "owner": owner,
                "vault_token_account": vault_token_account,
                "owner_token_account": owner_token_account,
                "token_program": str(TOKEN_PROGRAM_ID),
            },
            "args": {},
        }


# Singleton instance
vault_service = VaultDeploymentService()


async def init_vault_service():
    """Initialize vault service on startup"""
    await vault_service.connect()
    logger.info("Vault Deployment Service initialized")


async def shutdown_vault_service():
    """Cleanup on shutdown"""
    await vault_service.disconnect()
    logger.info("Vault Deployment Service shutdown")
