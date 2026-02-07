"""
Solana Copilot - Transactions Router
Transaction history, details, and management
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from app.db.session import get_db
from app.models import User, Transaction
from app.api.v1.auth import get_current_user
from app.schemas import TransactionResponse, TransactionListResponse, TransactionCreate

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Transaction Endpoints
# ============================================

@router.get("/", response_model=TransactionListResponse)
async def get_transactions(
    limit: int = Query(50, ge=1, le=100, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get transaction history with pagination and filtering.
    
    Args:
        limit: Number of transactions per page
        offset: Pagination offset
        action: Filter by action (swap, send, stake, etc.)
        status: Filter by status (pending, success, failed)
    
    Returns:
        Paginated list of transactions
    """
    
    try:
        # Build query
        query = select(Transaction).where(Transaction.user_id == current_user.id)
        
        # Apply filters
        if action:
            query = query.where(Transaction.action == action)
        if status:
            query = query.where(Transaction.status == status)
        
        # Order by most recent
        query = query.order_by(desc(Transaction.created_at))
        
        # Get total count
        count_query = select(Transaction).where(Transaction.user_id == current_user.id)
        if action:
            count_query = count_query.where(Transaction.action == action)
        if status:
            count_query = count_query.where(Transaction.status == status)
        
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return TransactionListResponse(
            transactions=[TransactionResponse.model_validate(tx) for tx in transactions],
            total=total,
            limit=limit,
            offset=offset,
        )
    
    except Exception as e:
        logger.error(f"Error getting transactions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transactions: {str(e)}"
        )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific transaction.
    
    Args:
        transaction_id: Transaction ID
    
    Returns:
        Transaction details
    """
    
    try:
        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.id == transaction_id,
                    Transaction.user_id == current_user.id
                )
            )
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return TransactionResponse.model_validate(transaction)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transaction: {str(e)}"
        )


@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new transaction record.
    
    Args:
        transaction: Transaction data
    
    Returns:
        Created transaction
    """
    
    try:
        # Create transaction
        new_transaction = Transaction(
            user_id=current_user.id,
            action=transaction.action,
            source_token=transaction.source_token,
            dest_token=transaction.dest_token,
            amount_in=transaction.amount_in,
            amount_out=transaction.amount_out,
            status="pending",
        )
        
        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)
        
        logger.info(f"Created transaction: {new_transaction.id}")
        
        return TransactionResponse.model_validate(new_transaction)
    
    except Exception as e:
        logger.error(f"Error creating transaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}"
        )


@router.get("/stats/summary")
async def get_transaction_stats(
    timeframe: str = Query("30d", description="Timeframe: 7d, 30d, 90d, all"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get transaction statistics and summary.
    
    Args:
        timeframe: Time period for stats
    
    Returns:
        Transaction statistics
    """
    
    try:
        # Calculate date range
        if timeframe == "all":
            start_date = datetime(2020, 1, 1)
        else:
            days = int(timeframe.replace("d", ""))
            start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get transactions in timeframe
        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.user_id == current_user.id,
                    Transaction.created_at >= start_date
                )
            )
        )
        transactions = result.scalars().all()
        
        # Calculate stats
        total_transactions = len(transactions)
        successful_transactions = len([tx for tx in transactions if tx.status == "success"])
        failed_transactions = len([tx for tx in transactions if tx.status == "failed"])
        pending_transactions = len([tx for tx in transactions if tx.status == "pending"])
        
        # Calculate total volume
        total_volume_usd = sum(
            float(tx.amount_in or 0) * float(tx.price_at_execution or 0)
            for tx in transactions
            if tx.status == "success"
        )
        
        # Calculate total gas fees
        total_gas_fees = sum(
            float(tx.gas_fee or 0)
            for tx in transactions
            if tx.status == "success"
        )
        
        # Action breakdown
        action_counts = {}
        for tx in transactions:
            action_counts[tx.action] = action_counts.get(tx.action, 0) + 1
        
        return {
            "timeframe": timeframe,
            "total_transactions": total_transactions,
            "successful": successful_transactions,
            "failed": failed_transactions,
            "pending": pending_transactions,
            "success_rate": (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0,
            "total_volume_usd": total_volume_usd,
            "total_gas_fees": total_gas_fees,
            "action_breakdown": action_counts,
        }
    
    except Exception as e:
        logger.error(f"Error getting transaction stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transaction stats: {str(e)}"
        )


@router.get("/recent/activity")
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent transaction activity (simplified view).
    
    Args:
        limit: Number of recent transactions
    
    Returns:
        Recent activity
    """
    
    try:
        result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == current_user.id)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
        )
        transactions = result.scalars().all()
        
        activity = []
        for tx in transactions:
            activity.append({
                "id": str(tx.id),
                "action": tx.action,
                "description": _format_transaction_description(tx),
                "status": tx.status,
                "timestamp": tx.created_at.isoformat(),
                "tx_signature": tx.tx_signature,
            })
        
        return {
            "activity": activity,
            "count": len(activity),
        }
    
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent activity: {str(e)}"
        )


# ============================================
# Helper Functions
# ============================================

def _format_transaction_description(tx: Transaction) -> str:
    """Format transaction description for display"""
    
    if tx.action == "swap":
        return f"Swapped {tx.amount_in} {tx.source_token} → {tx.amount_out} {tx.dest_token}"
    
    elif tx.action == "send":
        return f"Sent {tx.amount_in} {tx.source_token}"
    
    elif tx.action == "stake":
        return f"Staked {tx.amount_in} {tx.source_token}"
    
    else:
        return f"{tx.action.capitalize()} transaction"
