"""
Transaction Service - Handles logging and retrieving transactions from the database
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction, User

logger = logging.getLogger(__name__)


class TransactionService:
    """
    Service for managing transaction records in the database.
    Handles creating, updating, and retrieving transaction history.
    """

    @staticmethod
    async def create_pending_transaction(
        db: AsyncSession,
        user_id: UUID,
        action: str,
        source_token: str,
        dest_token: str,
        amount_in: float,
        ai_reasoning: Optional[Dict[str, Any]] = None,
    ) -> Transaction:
        """
        Create a pending transaction record when a swap is initiated.

        Args:
            db: Database session
            user_id: User's UUID
            action: Transaction action (swap, send, stake)
            source_token: Source token symbol/mint
            dest_token: Destination token symbol/mint
            amount_in: Input amount
            ai_reasoning: Optional AI reasoning/trace data

        Returns:
            Created Transaction record
        """
        try:
            transaction = Transaction(
                user_id=user_id,
                action=action,
                source_token=source_token,
                dest_token=dest_token,
                amount_in=Decimal(str(amount_in)),
                status="pending",
                ai_reasoning=ai_reasoning or {},
            )

            db.add(transaction)
            await db.commit()
            await db.refresh(transaction)

            logger.info(f"Created pending transaction {transaction.id} for user {user_id}")
            return transaction

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create pending transaction: {e}", exc_info=True)
            raise

    @staticmethod
    async def update_transaction_approved(
        db: AsyncSession,
        transaction_id: UUID,
        amount_out: Optional[float] = None,
        price_at_execution: Optional[float] = None,
        gas_fee: Optional[float] = None,
    ) -> Optional[Transaction]:
        """
        Update transaction when user approves it.

        Args:
            db: Database session
            transaction_id: Transaction UUID
            amount_out: Expected output amount
            price_at_execution: Price at approval time
            gas_fee: Estimated gas fee

        Returns:
            Updated Transaction or None
        """
        try:
            result = await db.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            transaction = result.scalar_one_or_none()

            if not transaction:
                logger.warning(f"Transaction {transaction_id} not found")
                return None

            transaction.approval_timestamp = datetime.utcnow()
            if amount_out is not None:
                transaction.amount_out = Decimal(str(amount_out))
            if price_at_execution is not None:
                transaction.price_at_execution = Decimal(str(price_at_execution))
            if gas_fee is not None:
                transaction.gas_fee = Decimal(str(gas_fee))

            await db.commit()
            await db.refresh(transaction)

            logger.info(f"Transaction {transaction_id} approved")
            return transaction

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update transaction approval: {e}", exc_info=True)
            raise

    @staticmethod
    async def update_transaction_executed(
        db: AsyncSession,
        transaction_id: UUID,
        tx_signature: str,
        amount_out: Optional[float] = None,
        gas_fee: Optional[float] = None,
    ) -> Optional[Transaction]:
        """
        Update transaction after successful execution.

        Args:
            db: Database session
            transaction_id: Transaction UUID
            tx_signature: On-chain transaction signature
            amount_out: Actual output amount
            gas_fee: Actual gas fee

        Returns:
            Updated Transaction or None
        """
        try:
            result = await db.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            transaction = result.scalar_one_or_none()

            if not transaction:
                logger.warning(f"Transaction {transaction_id} not found")
                return None

            transaction.status = "success"
            transaction.tx_signature = tx_signature
            transaction.execution_timestamp = datetime.utcnow()
            if amount_out is not None:
                transaction.amount_out = Decimal(str(amount_out))
            if gas_fee is not None:
                transaction.gas_fee = Decimal(str(gas_fee))

            await db.commit()
            await db.refresh(transaction)

            logger.info(f"Transaction {transaction_id} executed: {tx_signature}")
            return transaction

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update transaction execution: {e}", exc_info=True)
            raise

    @staticmethod
    async def update_transaction_failed(
        db: AsyncSession,
        transaction_id: UUID,
        error_message: str,
    ) -> Optional[Transaction]:
        """
        Update transaction after failed execution.

        Args:
            db: Database session
            transaction_id: Transaction UUID
            error_message: Error description

        Returns:
            Updated Transaction or None
        """
        try:
            result = await db.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            transaction = result.scalar_one_or_none()

            if not transaction:
                logger.warning(f"Transaction {transaction_id} not found")
                return None

            transaction.status = "failed"
            transaction.execution_timestamp = datetime.utcnow()

            # Store error in ai_reasoning
            if transaction.ai_reasoning:
                transaction.ai_reasoning["error"] = error_message
            else:
                transaction.ai_reasoning = {"error": error_message}

            await db.commit()
            await db.refresh(transaction)

            logger.info(f"Transaction {transaction_id} failed: {error_message}")
            return transaction

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update transaction failure: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_user_transactions(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        action: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Transaction]:
        """
        Get transaction history for a user.

        Args:
            db: Database session
            user_id: User's UUID
            limit: Maximum number of records
            offset: Pagination offset
            action: Filter by action type
            status: Filter by status

        Returns:
            List of Transaction records
        """
        try:
            query = select(Transaction).where(Transaction.user_id == user_id)

            if action:
                query = query.where(Transaction.action == action)
            if status:
                query = query.where(Transaction.status == status)

            query = query.order_by(desc(Transaction.created_at))
            query = query.limit(limit).offset(offset)

            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get user transactions: {e}", exc_info=True)
            return []

    @staticmethod
    async def get_transaction_by_id(
        db: AsyncSession,
        transaction_id: UUID,
    ) -> Optional[Transaction]:
        """
        Get a specific transaction by ID.

        Args:
            db: Database session
            transaction_id: Transaction UUID

        Returns:
            Transaction or None
        """
        try:
            result = await db.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get transaction: {e}", exc_info=True)
            return None

    @staticmethod
    async def get_user_by_wallet(
        db: AsyncSession,
        wallet_address: str,
    ) -> Optional[User]:
        """
        Get user by wallet address.

        Args:
            db: Database session
            wallet_address: Solana wallet address

        Returns:
            User or None
        """
        try:
            result = await db.execute(
                select(User).where(User.wallet_address == wallet_address)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get user by wallet: {e}", exc_info=True)
            return None


# Create singleton instance
transaction_service = TransactionService()
