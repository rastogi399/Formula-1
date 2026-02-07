"""
Solana Copilot - Automations Router
DCA, recurring swaps, and portfolio rebalancing management
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from app.db.session import get_db
from app.models import User, Automation, AutomationExecution
from app.api.v1.auth import get_current_user
from app.schemas import (
    AutomationResponse,
    AutomationListResponse,
    AutomationCreate,
    AutomationUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Automation Endpoints
# ============================================

@router.get("/", response_model=AutomationListResponse)
async def get_automations(
    status: Optional[str] = Query(None, description="Filter by status"),
    automation_type: Optional[str] = Query(None, description="Filter by type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all automations for the current user.
    
    Args:
        status: Filter by status (active, paused, completed, cancelled)
        automation_type: Filter by type (dca, recurring_swap, rebalance)
    
    Returns:
        List of automations
    """
    
    try:
        # Build query
        query = select(Automation).where(Automation.user_id == current_user.id)
        
        # Apply filters
        if status:
            query = query.where(Automation.status == status)
        if automation_type:
            query = query.where(Automation.automation_type == automation_type)
        
        # Order by most recent
        query = query.order_by(desc(Automation.created_at))
        
        # Execute query
        result = await db.execute(query)
        automations = result.scalars().all()
        
        return AutomationListResponse(
            automations=[AutomationResponse.model_validate(auto) for auto in automations],
            total=len(automations),
        )
    
    except Exception as e:
        logger.error(f"Error getting automations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch automations: {str(e)}"
        )


@router.get("/{automation_id}", response_model=AutomationResponse)
async def get_automation(
    automation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific automation.
    
    Args:
        automation_id: Automation ID
    
    Returns:
        Automation details
    """
    
    try:
        result = await db.execute(
            select(Automation).where(
                and_(
                    Automation.id == automation_id,
                    Automation.user_id == current_user.id
                )
            )
        )
        automation = result.scalar_one_or_none()
        
        if not automation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Automation not found"
            )
        
        return AutomationResponse.model_validate(automation)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting automation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch automation: {str(e)}"
        )


@router.post("/", response_model=AutomationResponse)
async def create_automation(
    automation: AutomationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new automation (DCA, recurring swap, or rebalancing).
    
    Args:
        automation: Automation configuration
    
    Returns:
        Created automation
    """
    
    try:
        # Import vault service for PDA derivation
        from app.services.vault_service import vault_service
        
        # Convert frequency to seconds
        frequency_seconds = _parse_frequency(automation.frequency_seconds)
        
        # Calculate next execution time
        next_execution = datetime.utcnow() + timedelta(seconds=frequency_seconds)
        
        # Derive vault PDA for on-chain automations
        vault_pda = None
        if automation.automation_type in ["dca", "rebalance"]:
            vault_pda, _ = vault_service.derive_vault_pda(
                current_user.wallet_address,
                automation.source_token,
                automation.dest_token,
            )
        
        # Create automation with vault PDA
        new_automation = Automation(
            user_id=current_user.id,
            automation_type=automation.automation_type,
            name=automation.name,
            source_token=automation.source_token,
            dest_token=automation.dest_token,
            amount=automation.amount,
            frequency_seconds=frequency_seconds,
            next_execution_at=next_execution,
            status="pending_deployment" if vault_pda else "active",
            vault_pda=vault_pda,
            metadata=automation.metadata,
        )
        
        db.add(new_automation)
        await db.commit()
        await db.refresh(new_automation)
        
        logger.info(f"Created automation: {new_automation.id} ({new_automation.automation_type})")
        if vault_pda:
            logger.info(f"Vault PDA: {vault_pda}")
        
        return AutomationResponse.model_validate(new_automation)
    
    except Exception as e:
        logger.error(f"Error creating automation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create automation: {str(e)}"
        )


@router.patch("/{automation_id}", response_model=AutomationResponse)
async def update_automation(
    automation_id: UUID,
    update: AutomationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing automation.
    
    Args:
        automation_id: Automation ID
        update: Update data
    
    Returns:
        Updated automation
    """
    
    try:
        # Get automation
        result = await db.execute(
            select(Automation).where(
                and_(
                    Automation.id == automation_id,
                    Automation.user_id == current_user.id
                )
            )
        )
        automation = result.scalar_one_or_none()
        
        if not automation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Automation not found"
            )
        
        # Update fields
        if update.name is not None:
            automation.name = update.name
        if update.amount is not None:
            automation.amount = update.amount
        if update.frequency_seconds is not None:
            automation.frequency_seconds = _parse_frequency(update.frequency_seconds)
        if update.status is not None:
            automation.status = update.status
        if update.metadata is not None:
            automation.metadata = update.metadata
        
        await db.commit()
        await db.refresh(automation)
        
        logger.info(f"Updated automation: {automation_id}")
        
        return AutomationResponse.model_validate(automation)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating automation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update automation: {str(e)}"
        )


@router.post("/{automation_id}/pause")
async def pause_automation(
    automation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pause an active automation.
    
    Args:
        automation_id: Automation ID
    
    Returns:
        Success message
    """
    
    try:
        result = await db.execute(
            select(Automation).where(
                and_(
                    Automation.id == automation_id,
                    Automation.user_id == current_user.id
                )
            )
        )
        automation = result.scalar_one_or_none()
        
        if not automation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Automation not found"
            )
        
        automation.status = "paused"
        await db.commit()
        
        logger.info(f"Paused automation: {automation_id}")
        
        return {"success": True, "message": "Automation paused"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing automation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause automation: {str(e)}"
        )


@router.post("/{automation_id}/resume")
async def resume_automation(
    automation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Resume a paused automation.
    
    Args:
        automation_id: Automation ID
    
    Returns:
        Success message
    """
    
    try:
        result = await db.execute(
            select(Automation).where(
                and_(
                    Automation.id == automation_id,
                    Automation.user_id == current_user.id
                )
            )
        )
        automation = result.scalar_one_or_none()
        
        if not automation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Automation not found"
            )
        
        automation.status = "active"
        # Recalculate next execution
        automation.next_execution_at = datetime.utcnow() + timedelta(seconds=automation.frequency_seconds)
        await db.commit()
        
        logger.info(f"Resumed automation: {automation_id}")
        
        return {"success": True, "message": "Automation resumed"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming automation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume automation: {str(e)}"
        )


@router.delete("/{automation_id}")
async def delete_automation(
    automation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel and delete an automation.
    
    Args:
        automation_id: Automation ID
    
    Returns:
        Success message
    """
    
    try:
        result = await db.execute(
            select(Automation).where(
                and_(
                    Automation.id == automation_id,
                    Automation.user_id == current_user.id
                )
            )
        )
        automation = result.scalar_one_or_none()
        
        if not automation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Automation not found"
            )
        
        # Mark as cancelled instead of deleting (for history)
        automation.status = "cancelled"
        await db.commit()
        
        logger.info(f"Cancelled automation: {automation_id}")
        
        # TODO: Close on-chain vault if exists
        # if automation.vault_pda:
        #     await _close_vault(automation.vault_pda)
        
        return {"success": True, "message": "Automation cancelled"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting automation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete automation: {str(e)}"
        )


@router.get("/{automation_id}/executions")
async def get_automation_executions(
    automation_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get execution history for an automation.
    
    Args:
        automation_id: Automation ID
        limit: Number of executions to return
    
    Returns:
        Execution history
    """
    
    try:
        # Verify ownership
        result = await db.execute(
            select(Automation).where(
                and_(
                    Automation.id == automation_id,
                    Automation.user_id == current_user.id
                )
            )
        )
        automation = result.scalar_one_or_none()
        
        if not automation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Automation not found"
            )
        
        # Get executions
        result = await db.execute(
            select(AutomationExecution)
            .where(AutomationExecution.automation_id == automation_id)
            .order_by(desc(AutomationExecution.executed_at))
            .limit(limit)
        )
        executions = result.scalars().all()
        
        return {
            "automation_id": str(automation_id),
            "executions": [
                {
                    "id": str(exec.id),
                    "executed_at": exec.executed_at.isoformat(),
                    "input_amount": float(exec.input_amount),
                    "output_amount": float(exec.output_amount) if exec.output_amount else None,
                    "price": float(exec.price_at_execution) if exec.price_at_execution else None,
                    "status": exec.status,
                    "tx_hash": exec.transaction_hash,
                    "error": exec.error_message,
                }
                for exec in executions
            ],
            "total": len(executions),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting executions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch executions: {str(e)}"
        )


@router.get("/{automation_id}/deploy-instruction")
async def get_deploy_instruction(
    automation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the on-chain vault deployment instruction for frontend signing.
    
    Args:
        automation_id: Automation ID
    
    Returns:
        Instruction data for wallet signing
    """
    
    try:
        from app.services.vault_service import vault_service
        
        # Get automation
        result = await db.execute(
            select(Automation).where(
                and_(
                    Automation.id == automation_id,
                    Automation.user_id == current_user.id
                )
            )
        )
        automation = result.scalar_one_or_none()
        
        if not automation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Automation not found"
            )
        
        if automation.automation_type not in ["dca", "rebalance"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This automation type does not require on-chain vault"
            )
        
        # Build instruction data
        instruction = await vault_service.build_initialize_instruction(
            owner=current_user.wallet_address,
            source_mint=automation.source_token,
            dest_mint=automation.dest_token,
            amount_per_cycle=int(automation.amount * 1_000_000),  # Convert to smallest units
            frequency_seconds=automation.frequency_seconds,
            total_cycles=100,  # Default to 100 cycles
        )
        
        return {
            "automation_id": str(automation_id),
            "instruction": instruction,
            "vault_pda": automation.vault_pda,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deploy instruction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deploy instruction: {str(e)}"
        )


@router.post("/{automation_id}/confirm-deployment")
async def confirm_vault_deployment(
    automation_id: UUID,
    tx_hash: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm that the vault has been deployed on-chain.
    Called after frontend successfully signs and submits the transaction.
    
    Args:
        automation_id: Automation ID
        tx_hash: Transaction hash from on-chain deployment
    
    Returns:
        Success message
    """
    
    try:
        # Get automation
        result = await db.execute(
            select(Automation).where(
                and_(
                    Automation.id == automation_id,
                    Automation.user_id == current_user.id
                )
            )
        )
        automation = result.scalar_one_or_none()
        
        if not automation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Automation not found"
            )
        
        # Update automation status
        automation.status = "active"
        automation.metadata = automation.metadata or {}
        automation.metadata["deployment_tx"] = tx_hash
        automation.next_execution_at = datetime.utcnow() + timedelta(seconds=automation.frequency_seconds)
        
        await db.commit()
        
        logger.info(f"Vault deployment confirmed for automation {automation_id}: {tx_hash}")
        
        return {
            "success": True,
            "automation_id": str(automation_id),
            "vault_pda": automation.vault_pda,
            "tx_hash": tx_hash,
            "status": "active",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming deployment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm deployment: {str(e)}"
        )


# ============================================
# Helper Functions
# ============================================

def _parse_frequency(frequency: int) -> int:
    """Parse frequency to seconds"""
    # If already in seconds, return as-is
    if frequency > 0:
        return frequency
    
    # Otherwise, convert from common intervals
    # This is simplified - in production, accept string like "1d", "12h", etc.
    return frequency

