from typing import Dict, List
import pandas as pd
from riskfusion.utils.logging import get_logger
from riskfusion.execution.alpaca_connector import AlpacaConnector

logger = get_logger("oms")

class OMS:
    """
    Order Management System.
    Translates Target Weights -> Orders.
    Supports both buying and selling during rebalancing.
    """
    
    # Minimum order threshold in dollars
    MIN_ORDER_NOTIONAL = 1.0
    # Delta threshold (%) - skip rebalancing if change is less than this
    REBALANCE_THRESHOLD = 0.005  # 0.5%
    
    def __init__(self):
        self.alpaca = AlpacaConnector()
    
    def _get_current_positions_map(self) -> Dict[str, float]:
        """
        Fetch current positions and return as {ticker: market_value} dict.
        """
        positions = self.alpaca.get_positions()
        position_map = {}
        for pos in positions:
            ticker = pos.get('symbol')
            market_value = float(pos.get('market_value', 0))
            position_map[ticker] = market_value
        return position_map
        
    def execute_rebalance(self, target_weights: pd.DataFrame, capital: float = None):
        """
        Execute rebalance based on target weights.
        Compares current positions vs target and submits BUY/SELL orders.
        """
        import numpy as np
        
        logger.info("Starting Execution Cycle...")
        
        # 0. Cancel any pending orders to free up shares
        try:
            pending = self.alpaca.get_orders(status="open")
            if pending:
                logger.info(f"Cancelling {len(pending)} pending orders...")
                self.alpaca.cancel_all_orders()
                # Brief pause to let cancellations process
                import time
                time.sleep(1)
        except Exception as e:
            logger.warning(f"Could not cancel pending orders: {e}")
        
        # 1. Get Capital
        account = self.alpaca.get_account()
        if capital is None:
            capital = float(account['equity'])
            
        logger.info(f"Account Equity: ${capital:.2f}")
        
        # 2. Fetch current positions
        current_positions = self._get_current_positions_map()
        logger.info(f"Current positions: {len(current_positions)} tickers")
        
        # 3. Aggregate weights by ticker (in case of duplicates)
        if isinstance(target_weights, pd.DataFrame):
            weights_series = target_weights['weight'].groupby(level=0).first()
        else:
            weights_series = target_weights.groupby(level=0).first()
        
        # 4. Calculate target notional values
        target_positions = {}
        for ticker, weight in weights_series.items():
            if np.isfinite(weight) and weight >= 0:
                target_positions[ticker] = capital * weight
            else:
                logger.warning(f"Skipping {ticker}: invalid weight {weight}")
        
        # 5. Determine all tickers (union of current + target)
        all_tickers = set(current_positions.keys()) | set(target_positions.keys())
        
        # 6. Calculate deltas and submit orders
        orders_submitted = []
        sells_submitted = []
        buys_submitted = []
        
        for ticker in all_tickers:
            current_value = current_positions.get(ticker, 0.0)
            target_value = target_positions.get(ticker, 0.0)
            delta = target_value - current_value
            
            # Skip if delta is too small (within threshold)
            if abs(delta) < self.MIN_ORDER_NOTIONAL:
                continue
            if current_value > 0 and abs(delta / current_value) < self.REBALANCE_THRESHOLD:
                continue
            
            try:
                if delta > 0:
                    # BUY: Increase position
                    logger.info(f"Submitting: BUY ${delta:.2f} of {ticker}")
                    order = self.alpaca.submit_order(
                        symbol=ticker,
                        notional=round(delta, 2),
                        side="buy"
                    )
                    buys_submitted.append(order)
                    orders_submitted.append(order)
                elif delta < 0:
                    # SELL: Reduce or close position
                    sell_amount = abs(delta)
                    
                    # Use close_position API for full closures (more reliable)
                    if target_value < self.MIN_ORDER_NOTIONAL:
                        logger.info(f"Closing entire position: {ticker}")
                        order = self.alpaca.close_position(ticker)
                        sells_submitted.append(order)
                        orders_submitted.append(order)
                    else:
                        # Partial sell - cap to 99% of current to avoid precision issues
                        sell_amount = min(sell_amount, current_value * 0.99)
                        if sell_amount < self.MIN_ORDER_NOTIONAL:
                            continue
                        logger.info(f"Submitting: SELL ${sell_amount:.2f} of {ticker}")
                        order = self.alpaca.submit_order(
                            symbol=ticker,
                            notional=round(sell_amount, 2),
                            side="sell"
                        )
                        sells_submitted.append(order)
                        orders_submitted.append(order)
            except Exception as e:
                logger.error(f"Failed to submit order for {ticker}: {e}")
                
        logger.info(f"Submitted {len(orders_submitted)} orders ({len(buys_submitted)} buys, {len(sells_submitted)} sells).")
        return {
            "orders_submitted": len(orders_submitted),
            "buys": len(buys_submitted),
            "sells": len(sells_submitted),
            "details": orders_submitted
        }

    def submit_test_order(self, symbol="SPY", qty=1, side="buy"):
        return self.alpaca.submit_order(symbol=symbol, qty=qty, side=side)
