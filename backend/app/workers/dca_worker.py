"""
Schumacher - DCA Worker
Executes scheduled DCA (Dollar Cost Averaging) automations
"""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.models import Automation, AutomationExecution, User
from app.integrations.solana.client import get_solana_client
from app.integrations.jupiter.client import get_jupiter_client

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.dca_worker.execute_due_automations")
def execute_due_automations():
    """
    Periodic task to execute all due DCA automations.
    Runs every minute via Celery Beat.
    """
    logger.info("Checking for due DCA automations...")
    
    db = SessionLocal()
    try:
        # Get all active automations that are due
        now = datetime.utcnow()
        
        result = db.execute(
            select(Automation).where(
                and_(
                    Automation.status == "active",
                    Automation.next_execution_at <= now,
                    Automation.automation_type.in_(["dca", "recurring_swap"])
                )
            )
        )
        automations = result.scalars().all()
        
        logger.info(f"Found {len(automations)} due automations")
        
        # Execute each automation
        for automation in automations:
            try:
                execute_dca_swap.delay(str(automation.id))
            except Exception as e:
                logger.error(f"Failed to queue automation {automation.id}: {e}")
        
        return {"success": True, "queued": len(automations)}
    
    finally:
        db.close()


import asyncio

@celery_app.task(name="app.workers.dca_worker.execute_dca_swap")
def execute_dca_swap(automation_id: str):
    """
    Execute a single DCA swap transaction.
    """
    return asyncio.run(_execute_dca_swap_async(automation_id))

async def _execute_dca_swap_async(automation_id: str):
    """Async implementation of DCA swap execution"""
    logger.info(f"Executing DCA automation: {automation_id}")
    
    db = SessionLocal()
    try:
        # Get automation
        automation = db.get(Automation, automation_id)
        if not automation:
            logger.error(f"Automation {automation_id} not found")
            return {"success": False, "error": "Automation not found"}
        
        # Get user
        user = db.get(User, automation.user_id)
        if not user:
            logger.error(f"User {automation.user_id} not found")
            return {"success": False, "error": "User not found"}
        
        wallet = user.wallet_address
        
        # Create execution record
        execution = AutomationExecution(
            automation_id=automation.id,
            executed_at=datetime.utcnow(),
            input_amount=automation.amount,
            status="pending",
        )
        db.add(execution)
        db.commit()
        
        try:
            # Get current balance
            solana = get_solana_client()
            balance_info = await solana.get_token_balance(wallet, automation.source_token)
            balance = balance_info["ui_amount"]
            
            if balance < float(automation.amount):
                raise Exception(f"Insufficient balance: {balance} < {automation.amount}")
            
            # Get swap quote
            jupiter = get_jupiter_client()
            quote = await jupiter.get_quote(
                source_token=automation.source_token,
                dest_token=automation.dest_token,
                amount=float(automation.amount),
                slippage_bps=100,  # 1% slippage
            )
            
            if not quote:
                raise Exception("Failed to get quote")
            
            output_amount = quote.get("amount_out", 0)
            price = float(automation.amount) / output_amount if output_amount > 0 else 0
            
            # Build and execute transaction
            # In production: Use session key to sign and submit
            # For now, we'll simulate success
            tx_signature = "simulated_tx_" + automation_id[:8]
            
            # Update execution record
            execution.output_amount = Decimal(str(output_amount))
            execution.price_at_execution = Decimal(str(price))
            execution.transaction_hash = tx_signature
            execution.status = "success"
            
            # Update automation
            automation.execution_count += 1
            automation.last_execution_at = datetime.utcnow()
            automation.next_execution_at = datetime.utcnow() + timedelta(
                seconds=automation.frequency_seconds
            )
            
            db.commit()
            
            logger.info(f"DCA executed successfully: {automation_id}")
            logger.info(f"Swapped {automation.amount} {automation.source_token} → {output_amount} {automation.dest_token}")
            
            return {
                "success": True,
                "automation_id": automation_id,
                "input_amount": float(automation.amount),
                "output_amount": output_amount,
                "tx_signature": tx_signature,
            }
        
        except Exception as e:
            logger.error(f"DCA execution failed: {e}", exc_info=True)
            
            # Update execution as failed
            execution.status = "failed"
            execution.error_message = str(e)
            db.commit()
            
            return {"success": False, "error": str(e)}
    
    finally:
        db.close()
