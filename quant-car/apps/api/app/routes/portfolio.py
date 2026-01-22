"""
Portfolio Control API - Full portfolio management endpoints
============================================================
Provides endpoints for viewing positions, closing positions, rebalancing,
and getting AI-powered optimization recommendations.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import sys

# Add riskfusion to path
riskfusion_path = os.environ.get(
    "RISKFUSION_PATH",
    r"C:\Users\olato\OneDrive\Documents\finance ai\riskfusion_alpha"
)
sys.path.insert(0, riskfusion_path)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


# ============ Pydantic Models ============

class Position(BaseModel):
    symbol: str
    qty: float
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    current_price: float
    avg_entry_price: float
    side: str  # 'long' or 'short'
    pct_of_portfolio: float


class PortfolioSummary(BaseModel):
    equity: float
    cash: float
    buying_power: float
    positions_count: int
    day_pl: float
    day_pl_pct: float
    total_pl: float
    total_pl_pct: float


class Order(BaseModel):
    id: str
    symbol: str
    side: str
    qty: Optional[float]
    notional: Optional[float]
    status: str
    created_at: str
    filled_qty: Optional[float]
    filled_avg_price: Optional[float]


class RebalanceRequest(BaseModel):
    weights: Dict[str, float]  # {ticker: weight}


class Recommendation(BaseModel):
    type: str  # 'reduce', 'increase', 'close', 'rebalance'
    symbol: Optional[str]
    reason: str
    priority: str  # 'low', 'medium', 'high'
    suggested_action: str


class ClosePositionRequest(BaseModel):
    symbol: str


# ============ Helper Functions ============

def get_alpaca_connector():
    """Get AlpacaConnector instance with proper imports."""
    try:
        from riskfusion.execution.alpaca_connector import AlpacaConnector
        return AlpacaConnector()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize Alpaca: {e}")


def get_oms():
    """Get OMS instance."""
    try:
        from riskfusion.execution.oms import OMS
        return OMS()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize OMS: {e}")


# ============ Endpoints ============

@router.get("/positions", response_model=List[Position])
async def get_positions():
    """Get all current positions with P&L."""
    try:
        alpaca = get_alpaca_connector()
        account = alpaca.get_account()
        positions = alpaca.get_positions()
        
        equity = float(account.get('equity', 0))
        
        result = []
        for pos in positions:
            market_value = float(pos.get('market_value', 0))
            pct_of_portfolio = (market_value / equity * 100) if equity > 0 else 0
            
            result.append(Position(
                symbol=pos.get('symbol'),
                qty=float(pos.get('qty', 0)),
                market_value=market_value,
                cost_basis=float(pos.get('cost_basis', 0)),
                unrealized_pl=float(pos.get('unrealized_pl', 0)),
                unrealized_plpc=float(pos.get('unrealized_plpc', 0)) * 100,
                current_price=float(pos.get('current_price', 0)),
                avg_entry_price=float(pos.get('avg_entry_price', 0)),
                side=pos.get('side', 'long'),
                pct_of_portfolio=round(pct_of_portfolio, 2)
            ))
        
        # Sort by market value descending
        result.sort(key=lambda x: x.market_value, reverse=True)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary():
    """Get portfolio summary including equity, cash, P&L."""
    try:
        alpaca = get_alpaca_connector()
        account = alpaca.get_account()
        
        equity = float(account.get('equity', 0))
        last_equity = float(account.get('last_equity', equity))
        day_pl = equity - last_equity
        day_pl_pct = (day_pl / last_equity * 100) if last_equity > 0 else 0
        
        # Calculate total P&L from positions
        positions = alpaca.get_positions()
        total_pl = sum(float(p.get('unrealized_pl', 0)) for p in positions)
        total_cost = sum(float(p.get('cost_basis', 0)) for p in positions)
        total_pl_pct = (total_pl / total_cost * 100) if total_cost > 0 else 0
        
        return PortfolioSummary(
            equity=equity,
            cash=float(account.get('cash', 0)),
            buying_power=float(account.get('buying_power', 0)),
            positions_count=len(positions),
            day_pl=round(day_pl, 2),
            day_pl_pct=round(day_pl_pct, 2),
            total_pl=round(total_pl, 2),
            total_pl_pct=round(total_pl_pct, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close/{symbol}")
async def close_position(symbol: str):
    """Close a specific position."""
    try:
        alpaca = get_alpaca_connector()
        result = alpaca.close_position(symbol)
        return {
            "message": f"Position {symbol} closed",
            "order": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close-all")
async def close_all_positions():
    """Liquidate entire portfolio. USE WITH CAUTION."""
    try:
        alpaca = get_alpaca_connector()
        result = alpaca.close_all_positions()
        return {
            "message": "All positions closed",
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders", response_model=List[Order])
async def get_orders(status: str = "open"):
    """Get orders by status (open, closed, all)."""
    try:
        alpaca = get_alpaca_connector()
        orders = alpaca.get_orders(status=status)
        
        result = []
        for o in orders:
            result.append(Order(
                id=o.get('id'),
                symbol=o.get('symbol'),
                side=o.get('side'),
                qty=float(o.get('qty')) if o.get('qty') else None,
                notional=float(o.get('notional')) if o.get('notional') else None,
                status=o.get('status'),
                created_at=o.get('created_at'),
                filled_qty=float(o.get('filled_qty')) if o.get('filled_qty') else None,
                filled_avg_price=float(o.get('filled_avg_price')) if o.get('filled_avg_price') else None
            ))
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel-orders")
async def cancel_all_orders():
    """Cancel all pending orders."""
    try:
        alpaca = get_alpaca_connector()
        result = alpaca.cancel_all_orders()
        return {
            "message": "All orders cancelled",
            "cancelled": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebalance")
async def trigger_rebalance(request: RebalanceRequest):
    """Trigger manual rebalance with specified target weights."""
    try:
        import pandas as pd
        
        oms = get_oms()
        
        # Convert weights dict to DataFrame
        weights_df = pd.DataFrame([
            {'ticker': ticker, 'weight': weight}
            for ticker, weight in request.weights.items()
        ]).set_index('ticker')
        
        result = oms.execute_rebalance(weights_df)
        
        return {
            "message": "Rebalance executed",
            "orders_submitted": result.get('orders_submitted', 0),
            "buys": result.get('buys', 0),
            "sells": result.get('sells', 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", response_model=List[Recommendation])
async def get_recommendations():
    """Get AI-powered optimization recommendations based on current portfolio."""
    try:
        alpaca = get_alpaca_connector()
        account = alpaca.get_account()
        positions = alpaca.get_positions()
        
        equity = float(account.get('equity', 0))
        recommendations = []
        
        # Analyze concentration risk
        for pos in positions:
            symbol = pos.get('symbol')
            market_value = float(pos.get('market_value', 0))
            pct = (market_value / equity * 100) if equity > 0 else 0
            unrealized_pl = float(pos.get('unrealized_pl', 0))
            unrealized_plpc = float(pos.get('unrealized_plpc', 0)) * 100
            
            # Over-concentrated position (>15%)
            if pct > 15:
                recommendations.append(Recommendation(
                    type="reduce",
                    symbol=symbol,
                    reason=f"{symbol} is {pct:.1f}% of portfolio - exceeds 15% concentration limit",
                    priority="high",
                    suggested_action=f"Reduce {symbol} to ~10% of portfolio"
                ))
            
            # Big winner - consider taking profits (>30% gain)
            if unrealized_plpc > 30:
                recommendations.append(Recommendation(
                    type="reduce",
                    symbol=symbol,
                    reason=f"{symbol} is up {unrealized_plpc:.1f}% - consider taking profits",
                    priority="medium",
                    suggested_action=f"Trim {symbol} position by 20-30%"
                ))
            
            # Big loser - consider cutting (>20% loss)
            if unrealized_plpc < -20:
                recommendations.append(Recommendation(
                    type="close",
                    symbol=symbol,
                    reason=f"{symbol} is down {unrealized_plpc:.1f}% - consider cutting losses",
                    priority="high",
                    suggested_action=f"Close or reduce {symbol} position"
                ))
        
        # Check for too many positions
        if len(positions) > 20:
            recommendations.append(Recommendation(
                type="rebalance",
                symbol=None,
                reason=f"Portfolio has {len(positions)} positions - consider consolidating",
                priority="low",
                suggested_action="Reduce to top 15-20 conviction positions"
            ))
        
        # Check for high cash
        cash = float(account.get('cash', 0))
        cash_pct = (cash / equity * 100) if equity > 0 else 0
        if cash_pct > 20:
            recommendations.append(Recommendation(
                type="increase",
                symbol=None,
                reason=f"Cash is {cash_pct:.1f}% of portfolio - may be underinvested",
                priority="low",
                suggested_action="Consider deploying cash to high-conviction positions"
            ))
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
