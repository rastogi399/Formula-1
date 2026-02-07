"""
Schumacher - Portfolio Worker
Creates portfolio snapshots for tracking performance and analytics
"""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.models import User, PortfolioSnapshot
from app.integrations.solana.client import get_solana_client
from app.integrations.birdeye.client import get_birdeye_client

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.portfolio_worker.create_all_snapshots")
def create_all_snapshots():
    """
    Periodic task to create portfolio snapshots for all active users.
    Runs hourly via Celery Beat.
    """
    logger.info("Creating portfolio snapshots for all users...")
    
    db = SessionLocal()
    try:
        # Get all users
        result = db.execute(select(User))
        users = result.scalars().all()
        
        logger.info(f"Found {len(users)} users")
        
        # Create snapshot for each user
        success_count = 0
        for user in users:
            try:
                create_portfolio_snapshot.delay(str(user.id))
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to queue snapshot for user {user.id}: {e}")
        
        return {"success": True, "queued": success_count}
    
    finally:
        db.close()


@celery_app.task(name="app.workers.portfolio_worker.create_portfolio_snapshot")
def create_portfolio_snapshot(user_id: str):
    """
    Create a portfolio snapshot for a specific user.
    
    Args:
        user_id: UUID of the user
    """
    logger.info(f"Creating portfolio snapshot for user: {user_id}")
    
    db = SessionLocal()
    try:
        # Get user
        user = db.get(User, user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            return {"success": False, "error": "User not found"}
        
        wallet = user.wallet_address
        
        # Get all token balances
        solana = get_solana_client()
        balances = await solana.get_all_token_balances(wallet)
        
        if not balances:
            logger.info(f"No balances found for user {user_id}")
            return {"success": True, "total_value": 0}
        
        # Get prices
        birdeye = get_birdeye_client()
        token_mints = [b["mint"] for b in balances]
        prices = await birdeye.get_multiple_prices(token_mints)
        
        # Calculate holdings and total value
        holdings = []
        total_value = 0
        
        for balance in balances:
            mint = balance["mint"]
            amount = balance["amount"]
            price = prices.get(mint, {}).get("price", 0)
            value = amount * price
            total_value += value
            
            holdings.append({
                "mint": mint,
                "symbol": balance["symbol"],
                "amount": amount,
                "price_usd": price,
                "value_usd": value,
            })
        
        # Calculate risk metrics (simplified)
        risk_score = calculate_risk_score(holdings, total_value)
        volatility = 0  # TODO: Calculate based on historical data
        max_drawdown = 0  # TODO: Calculate based on historical snapshots
        
        # Create snapshot
        snapshot = PortfolioSnapshot(
            user_id=user.id,
            total_value_usd=Decimal(str(total_value)),
            holdings=holdings,
            risk_score=risk_score,
            volatility_90d=Decimal(str(volatility)),
            max_drawdown_90d=Decimal(str(max_drawdown)),
        )
        
        db.add(snapshot)
        db.commit()
        
        logger.info(f"Portfolio snapshot created: Total value ${total_value:.2f}")
        
        return {
            "success": True,
            "user_id": user_id,
            "total_value_usd": total_value,
            "token_count": len(holdings),
        }
    
    except Exception as e:
        logger.error(f"Failed to create portfolio snapshot: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


def calculate_risk_score(holdings: list, total_value: float) -> int:
    """
    Calculate portfolio risk score (0-100).
    
    Args:
        holdings: List of token holdings
        total_value: Total portfolio value in USD
    
    Returns:
        Risk score (0 = low risk, 100 = high risk)
    """
    if total_value == 0:
        return 0
    
    # Calculate concentration (Herfindahl index)
    concentration = sum(
        (h["value_usd"] / total_value) ** 2 for h in holdings
    )
    
    # Higher concentration = higher risk
    # Scale from 0-1 to 0-100
    risk_score = int(concentration * 100)
    
    return min(100, max(0, risk_score))
