"""
DCA Service - Interfaces with the on-chain DCA Vault Anchor Program
Handles vault creation, deposits, execution, and management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import ID as SYSTEM_PROGRAM_ID
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Provider, Wallet, Program, Idl
from spl.token.constants import TOKEN_PROGRAM_ID

from app.core.config import settings

logger = logging.getLogger(__name__)

# Program ID from the Anchor program
DCA_VAULT_PROGRAM_ID = Pubkey.from_string("DCAvau1tXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")


class VaultStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class DCAVaultConfig:
    """Configuration for creating a DCA vault"""
    source_mint: str  # Token to swap FROM (e.g., USDC)
    dest_mint: str    # Token to swap TO (e.g., SOL)
    amount_per_cycle: int  # Amount in smallest units per cycle
    frequency_seconds: int  # Interval between executions
    total_cycles: int  # Total number of DCA cycles


@dataclass
class DCAVaultInfo:
    """Information about an existing DCA vault"""
    vault_address: str
    owner: str
    source_mint: str
    dest_mint: str
    amount_per_cycle: int
    frequency_seconds: int
    total_cycles: int
    executed_cycles: int
    total_deposited: int
    total_received: int
    last_execution: int
    next_execution: int
    status: VaultStatus


class DCAService:
    """
    Service for interacting with the DCA Vault Anchor program.
    Provides methods to create, manage, and execute DCA vaults.
    """
    
    def __init__(self, rpc_url: str = None):
        self.rpc_url = rpc_url or settings.SOLANA_RPC_URL
        self.client: Optional[AsyncClient] = None
        self.program: Optional[Program] = None
        
    async def connect(self):
        """Initialize connection to Solana RPC"""
        self.client = AsyncClient(self.rpc_url, commitment=Confirmed)
        logger.info(f"Connected to Solana RPC: {self.rpc_url}")
        
    async def disconnect(self):
        """Close RPC connection"""
        if self.client:
            await self.client.close()
            
    def _derive_vault_pda(
        self, 
        owner: Pubkey, 
        source_mint: Pubkey, 
        dest_mint: Pubkey
    ) -> tuple[Pubkey, int]:
        """Derive the PDA for a DCA vault"""
        seeds = [
            b"vault",
            bytes(owner),
            bytes(source_mint),
            bytes(dest_mint),
        ]
        return Pubkey.find_program_address(seeds, DCA_VAULT_PROGRAM_ID)
    
    async def get_vault_info(self, vault_address: str) -> Optional[DCAVaultInfo]:
        """Fetch vault account data from chain"""
        try:
            vault_pubkey = Pubkey.from_string(vault_address)
            response = await self.client.get_account_info(vault_pubkey)
            
            if response.value is None:
                return None
                
            # Parse account data (simplified - in production use anchorpy IDL)
            data = response.value.data
            
            # This is a simplified parser - production would use proper deserialization
            return DCAVaultInfo(
                vault_address=vault_address,
                owner=str(Pubkey.from_bytes(data[8:40])),
                source_mint=str(Pubkey.from_bytes(data[40:72])),
                dest_mint=str(Pubkey.from_bytes(data[72:104])),
                amount_per_cycle=int.from_bytes(data[104:112], 'little'),
                frequency_seconds=int.from_bytes(data[112:120], 'little', signed=True),
                total_cycles=int.from_bytes(data[120:122], 'little'),
                executed_cycles=int.from_bytes(data[122:124], 'little'),
                total_deposited=int.from_bytes(data[124:132], 'little'),
                total_received=int.from_bytes(data[132:140], 'little'),
                last_execution=int.from_bytes(data[140:148], 'little', signed=True),
                next_execution=int.from_bytes(data[148:156], 'little', signed=True),
                status=VaultStatus.ACTIVE,  # Parse status byte
            )
        except Exception as e:
            logger.error(f"Failed to fetch vault info: {e}")
            return None
            
    async def get_user_vaults(self, owner_address: str) -> List[DCAVaultInfo]:
        """Get all DCA vaults for a user"""
        # In production, use getProgramAccounts with filters
        # This is a simplified version
        vaults = []
        try:
            owner_pubkey = Pubkey.from_string(owner_address)
            
            # Query program accounts filtered by owner
            # Note: This requires memcmp filters on the owner field
            response = await self.client.get_program_accounts(
                DCA_VAULT_PROGRAM_ID,
                encoding="base64",
                filters=[
                    {"memcmp": {"offset": 8, "bytes": str(owner_pubkey)}}
                ]
            )
            
            for account in response.value:
                vault_info = await self.get_vault_info(str(account.pubkey))
                if vault_info:
                    vaults.append(vault_info)
                    
        except Exception as e:
            logger.error(f"Failed to get user vaults: {e}")
            
        return vaults
    
    async def check_vault_ready_for_execution(self, vault_address: str) -> bool:
        """Check if a vault is ready to execute its next DCA cycle"""
        vault_info = await self.get_vault_info(vault_address)
        
        if not vault_info:
            return False
            
        if vault_info.status != VaultStatus.ACTIVE:
            return False
            
        if vault_info.executed_cycles >= vault_info.total_cycles:
            return False
            
        current_time = int(datetime.now().timestamp())
        if current_time < vault_info.next_execution:
            return False
            
        return True
    
    async def get_pending_executions(self) -> List[str]:
        """Get all vaults that are ready for DCA execution"""
        pending = []
        
        try:
            # Get all active vaults
            response = await self.client.get_program_accounts(
                DCA_VAULT_PROGRAM_ID,
                encoding="base64",
            )
            
            current_time = int(datetime.now().timestamp())
            
            for account in response.value:
                vault_info = await self.get_vault_info(str(account.pubkey))
                if vault_info and vault_info.status == VaultStatus.ACTIVE:
                    if vault_info.next_execution <= current_time:
                        if vault_info.executed_cycles < vault_info.total_cycles:
                            pending.append(vault_info.vault_address)
                            
        except Exception as e:
            logger.error(f"Failed to get pending executions: {e}")
            
        return pending


# Singleton instance
dca_service = DCAService()


async def init_dca_service():
    """Initialize the DCA service on startup"""
    await dca_service.connect()
    logger.info("DCA Service initialized")


async def shutdown_dca_service():
    """Cleanup on shutdown"""
    await dca_service.disconnect()
    logger.info("DCA Service shutdown")
