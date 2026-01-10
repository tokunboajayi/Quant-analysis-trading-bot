from typing import Dict, List
import pandas as pd
from riskfusion.utils.logging import get_logger
from riskfusion.execution.alpaca_connector import AlpacaConnector

logger = get_logger("oms")

class OMS:
    """
    Order Management System.
    Translates Target Weights -> Orders.
    """
    def __init__(self):
        self.alpaca = AlpacaConnector()
        
    def execute_rebalance(self, target_weights: pd.DataFrame, capital: float = None):
        """
        Execute rebalance based on target weights.
        Uses Alpaca's fractional/notional order feature for simplicity.
        """
        logger.info("Starting Execution Cycle...")
        
        # 1. Get Capital
        account = self.alpaca.get_account()
        if capital is None:
            capital = float(account['equity'])
            
        logger.info(f"Account Equity: ${capital:.2f}")
        
        # 2. Aggregate weights by ticker (in case of duplicates)
        if isinstance(target_weights, pd.DataFrame):
            # If DataFrame, expect 'weight' column with ticker as index
            weights_series = target_weights['weight'].groupby(level=0).first()
        else:
            weights_series = target_weights.groupby(level=0).first()
            
        # 3. Submit Orders
        import numpy as np
        orders_submitted = []
        for ticker, weight in weights_series.items():
            # Skip invalid weights (NaN, infinity, negative, zero)
            if not np.isfinite(weight) or weight <= 0:
                logger.warning(f"Skipping {ticker}: invalid weight {weight}")
                continue
                
            # Calculate notional value
            notional = capital * weight
            
            # Skip tiny orders (less than $1)
            if notional < 1.0:
                continue
                
            try:
                logger.info(f"Submitting: BUY ${notional:.2f} of {ticker}")
                order = self.alpaca.submit_order(
                    symbol=ticker,
                    notional=round(notional, 2),
                    side="buy"
                )
                orders_submitted.append(order)
            except Exception as e:
                logger.error(f"Failed to submit order for {ticker}: {e}")
                
        logger.info(f"Submitted {len(orders_submitted)} orders.")
        return {"orders_submitted": len(orders_submitted), "details": orders_submitted}

    def submit_test_order(self, symbol="SPY", qty=1, side="buy"):
        return self.alpaca.submit_order(symbol=symbol, qty=qty, side=side)
