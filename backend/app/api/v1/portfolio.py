"""
Solana Copilot - Portfolio Router
Portfolio analytics, risk assessment, and performance tracking
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.models import User, PortfolioSnapshot
from app.api.v1.auth import get_current_user
from app.schemas import PortfolioResponse, TokenHolding, PortfolioSummary, PortfolioPerformance, PortfolioRisk, AIInsights
from app.integrations.solana.client import get_solana_client
from app.integrations.birdeye.client import get_birdeye_client
from app.utils.cache import cache_portfolio, get_cached_portfolio

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Portfolio Endpoints
# ============================================

@router.get("/", response_model=PortfolioResponse)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get complete portfolio overview with holdings, performance, and risk metrics.
    
    Returns:
        Complete portfolio data
    """
    
    try:
        wallet = current_user.wallet_address
        
        # Check cache
        cached = await get_cached_portfolio(wallet)
        if cached:
            return PortfolioResponse(**cached)
        
        # Fetch portfolio data
        portfolio_data = await _build_portfolio(wallet, db)
        
        # Cache result
        await cache_portfolio(wallet, portfolio_data)
        
        return PortfolioResponse(**portfolio_data)
    
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch portfolio: {str(e)}"
        )


@router.get("/holdings", response_model=List[TokenHolding])
async def get_holdings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get token holdings only (faster than full portfolio).
    
    Returns:
        List of token holdings
    """
    
    try:
        wallet = current_user.wallet_address
        
        # Get balances
        solana = get_solana_client()
        balances = await solana.get_all_token_balances(wallet)
        
        # Get prices
        birdeye = get_birdeye_client()
        token_mints = [b["mint"] for b in balances]
        prices = await birdeye.get_multiple_prices(token_mints)
        
        # Calculate holdings
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
                "allocation_pct": 0,  # Calculate after total
            })
        
        # Calculate allocations
        for holding in holdings:
            holding["allocation_pct"] = (
                (holding["value_usd"] / total_value * 100) if total_value > 0 else 0
            )
        
        return [TokenHolding(**h) for h in holdings]
    
    except Exception as e:
        logger.error(f"Error getting holdings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch holdings: {str(e)}"
        )


@router.get("/performance", response_model=PortfolioPerformance)
async def get_performance(
    timeframe: str = Query("30d", description="Timeframe: 1d, 7d, 30d, 90d"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get portfolio performance metrics.
    
    Args:
        timeframe: Time period for analysis
    
    Returns:
        Performance metrics
    """
    
    try:
        wallet = current_user.wallet_address
        
        # Get historical snapshots
        days = int(timeframe.replace("d", ""))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = await db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.user_id == current_user.id)
            .where(PortfolioSnapshot.created_at >= start_date)
            .order_by(desc(PortfolioSnapshot.created_at))
        )
        snapshots = result.scalars().all()
        
        if not snapshots:
            # No historical data, return zeros
            return PortfolioPerformance(
                total_pnl_usd=0,
                total_pnl_pct=0,
                realized_gains_usd=0,
                unrealized_gains_usd=0,
                return_1d_pct=0,
                return_7d_pct=0,
                return_30d_pct=0,
            )
        
        # Calculate performance
        current_value = float(snapshots[0].total_value_usd)
        initial_value = float(snapshots[-1].total_value_usd)
        
        pnl_usd = current_value - initial_value
        pnl_pct = (pnl_usd / initial_value * 100) if initial_value > 0 else 0
        
        # Calculate returns for different periods
        returns = _calculate_returns(snapshots)
        
        return PortfolioPerformance(
            total_pnl_usd=pnl_usd,
            total_pnl_pct=pnl_pct,
            realized_gains_usd=0,  # TODO: Calculate from transactions
            unrealized_gains_usd=pnl_usd,
            return_1d_pct=returns.get("1d", 0),
            return_7d_pct=returns.get("7d", 0),
            return_30d_pct=returns.get("30d", 0),
        )
    
    except Exception as e:
        logger.error(f"Error getting performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch performance: {str(e)}"
        )


@router.get("/risk", response_model=PortfolioRisk)
async def get_risk_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get portfolio risk assessment.
    
    Returns:
        Risk metrics
    """
    
    try:
        # Get recent snapshots for volatility calculation
        result = await db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.user_id == current_user.id)
            .where(PortfolioSnapshot.created_at >= datetime.utcnow() - timedelta(days=90))
            .order_by(desc(PortfolioSnapshot.created_at))
        )
        snapshots = result.scalars().all()
        
        if not snapshots:
            return PortfolioRisk(
                risk_score=0,
                risk_level="unknown",
                volatility_90d_pct=0,
                max_drawdown_90d_pct=0,
                var_95_usd=0,
                concentration_top3_pct=0,
            )
        
        # Calculate risk metrics
        risk_metrics = _calculate_risk_metrics(snapshots)
        
        return PortfolioRisk(**risk_metrics)
    
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch risk metrics: {str(e)}"
        )


@router.post("/snapshot")
async def create_snapshot(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a portfolio snapshot (manual trigger).
    Normally done automatically by Celery worker.
    
    Returns:
        Created snapshot
    """
    
    try:
        wallet = current_user.wallet_address
        
        # Build portfolio
        portfolio_data = await _build_portfolio(wallet, db)
        
        # Create snapshot
        snapshot = PortfolioSnapshot(
            user_id=current_user.id,
            total_value_usd=portfolio_data["portfolio_summary"]["total_usd"],
            holdings=portfolio_data["holdings"],
            risk_score=portfolio_data["risk"]["risk_score"],
            volatility_90d=portfolio_data["risk"]["volatility_90d_pct"],
            max_drawdown_90d=portfolio_data["risk"]["max_drawdown_90d_pct"],
        )
        
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        
        logger.info(f"Created portfolio snapshot for {wallet}")
        
        return {
            "success": True,
            "snapshot_id": str(snapshot.id),
            "total_value_usd": float(snapshot.total_value_usd),
        }
    
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create snapshot: {str(e)}"
        )


@router.get("/history")
async def get_portfolio_history(
    timeframe: str = Query("30d", description="Timeframe: 7d, 30d, 90d, 1y"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get portfolio value history for charting.

    Args:
        timeframe: Time period for history

    Returns:
        Time series data for chart visualization
    """

    try:
        # Parse timeframe
        timeframe_days = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365,
        }
        days = timeframe_days.get(timeframe, 30)
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get historical snapshots
        result = await db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.user_id == current_user.id)
            .where(PortfolioSnapshot.created_at >= start_date)
            .order_by(PortfolioSnapshot.created_at)
        )
        snapshots = result.scalars().all()

        # Format for charting
        history = [
            {
                "timestamp": snapshot.created_at.isoformat(),
                "value_usd": float(snapshot.total_value_usd),
                "risk_score": snapshot.risk_score,
            }
            for snapshot in snapshots
        ]

        # Calculate summary stats
        if history:
            start_value = history[0]["value_usd"]
            end_value = history[-1]["value_usd"]
            change_usd = end_value - start_value
            change_pct = (change_usd / start_value * 100) if start_value > 0 else 0
            high_value = max(h["value_usd"] for h in history)
            low_value = min(h["value_usd"] for h in history)
        else:
            start_value = end_value = change_usd = change_pct = 0
            high_value = low_value = 0

        return {
            "timeframe": timeframe,
            "data_points": len(history),
            "history": history,
            "summary": {
                "start_value": start_value,
                "end_value": end_value,
                "change_usd": change_usd,
                "change_pct": round(change_pct, 2),
                "high": high_value,
                "low": low_value,
            },
        }

    except Exception as e:
        logger.error(f"Error getting portfolio history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch portfolio history: {str(e)}"
        )


# ============================================
# Helper Functions
# ============================================

async def _build_portfolio(wallet: str, db: AsyncSession) -> dict:
    """Build complete portfolio data"""
    
    # Get holdings
    solana = get_solana_client()
    balances = await solana.get_all_token_balances(wallet)
    
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
            "allocation_pct": 0,
        })
    
    # Calculate allocations
    for holding in holdings:
        holding["allocation_pct"] = (
            (holding["value_usd"] / total_value * 100) if total_value > 0 else 0
        )
    
    # Build response
    return {
        "portfolio_summary": {
            "total_usd": total_value,
            "token_count": len(holdings),
            "updated_at": datetime.utcnow(),
        },
        "holdings": holdings,
        "performance": {
            "total_pnl_usd": 0,
            "total_pnl_pct": 0,
            "realized_gains_usd": 0,
            "unrealized_gains_usd": 0,
            "return_1d_pct": 0,
            "return_7d_pct": 0,
            "return_30d_pct": 0,
        },
        "risk": {
            "risk_score": 50,
            "risk_level": "medium",
            "volatility_90d_pct": 0,
            "max_drawdown_90d_pct": 0,
            "var_95_usd": 0,
            "concentration_top3_pct": sum(
                sorted([h["allocation_pct"] for h in holdings], reverse=True)[:3]
            ),
        },
        "ai_insights": {
            "summary": "Portfolio analysis complete",
            "risks": [],
            "recommendations": [],
        },
    }


def _calculate_returns(snapshots: List[PortfolioSnapshot]) -> dict:
    """Calculate returns for different periods"""
    
    returns = {}
    
    # Sort by date
    sorted_snapshots = sorted(snapshots, key=lambda s: s.created_at)
    
    if len(sorted_snapshots) < 2:
        return {"1d": 0, "7d": 0, "30d": 0}
    
    current_value = float(sorted_snapshots[-1].total_value_usd)
    
    # 1-day return
    if len(sorted_snapshots) >= 2:
        value_1d_ago = float(sorted_snapshots[-2].total_value_usd)
        returns["1d"] = ((current_value - value_1d_ago) / value_1d_ago * 100) if value_1d_ago > 0 else 0
    
    # 7-day return
    snapshots_7d = [s for s in sorted_snapshots if s.created_at >= datetime.utcnow() - timedelta(days=7)]
    if snapshots_7d:
        value_7d_ago = float(snapshots_7d[0].total_value_usd)
        returns["7d"] = ((current_value - value_7d_ago) / value_7d_ago * 100) if value_7d_ago > 0 else 0
    
    # 30-day return
    snapshots_30d = [s for s in sorted_snapshots if s.created_at >= datetime.utcnow() - timedelta(days=30)]
    if snapshots_30d:
        value_30d_ago = float(snapshots_30d[0].total_value_usd)
        returns["30d"] = ((current_value - value_30d_ago) / value_30d_ago * 100) if value_30d_ago > 0 else 0
    
    return returns


def _calculate_risk_metrics(snapshots: List[PortfolioSnapshot]) -> dict:
    """Calculate risk metrics from snapshots"""
    
    import numpy as np
    
    values = [float(s.total_value_usd) for s in snapshots]
    
    if len(values) < 2:
        return {
            "risk_score": 0,
            "risk_level": "unknown",
            "volatility_90d_pct": 0,
            "max_drawdown_90d_pct": 0,
            "var_95_usd": 0,
            "concentration_top3_pct": 0,
        }
    
    # Calculate volatility (standard deviation of returns)
    returns = np.diff(values) / values[:-1]
    volatility = float(np.std(returns) * 100)
    
    # Calculate max drawdown
    peak = values[0]
    max_drawdown = 0
    for value in values:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Calculate VaR (95% confidence)
    var_95 = float(np.percentile(returns, 5) * values[-1])
    
    # Calculate risk score (0-100)
    risk_score = min(100, int(volatility * 2 + max_drawdown))
    
    # Determine risk level
    if risk_score < 30:
        risk_level = "low"
    elif risk_score < 60:
        risk_level = "medium"
    elif risk_score < 80:
        risk_level = "high"
    else:
        risk_level = "very_high"
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "volatility_90d_pct": volatility,
        "max_drawdown_90d_pct": max_drawdown,
        "var_95_usd": abs(var_95),
        "concentration_top3_pct": 0,  # Calculated in _build_portfolio
    }
