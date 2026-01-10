"""
Regime Model - Step 6 of Crazy Quant Ladder
=============================================
Detects market regimes and enables strategy parameter switching.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("regime_model")


class RegimeModel:
    """
    Market Regime Detection Model.
    
    Classifies market state into:
    - CALM: Low volatility, normal conditions
    - VOLATILE: Elevated volatility
    - STRESSED: High volatility, correlation spikes, crisis-like
    
    Based on:
    - SPY realized volatility
    - Cross-asset correlation spikes
    - Volatility-of-volatility
    - Sector dispersion
    """
    
    CALM = 0
    VOLATILE = 1
    STRESSED = 2
    
    REGIME_NAMES = {0: 'CALM', 1: 'VOLATILE', 2: 'STRESSED'}
    
    def __init__(self):
        self.config = get_config()
        regime_config = self.config.params.get('regime', {})
        
        self.vol_threshold_volatile = regime_config.get('vol_threshold_volatile', 0.20)
        self.vol_threshold_stressed = regime_config.get('vol_threshold_stressed', 0.35)
        self.lookback = 20  # Days for vol calculation
        
    def detect_regime(self, prices: pd.DataFrame, benchmark: str = 'SPY') -> Tuple[int, Dict]:
        """
        Detect current market regime from price data.
        
        Args:
            prices: DataFrame with tickers as columns, dates as index
            benchmark: Ticker to use for volatility calculation
        
        Returns:
            Tuple of (regime_id, regime_info dict)
        """
        if benchmark not in prices.columns:
            logger.warning(f"Benchmark {benchmark} not in prices. Assuming CALM.")
            return self.CALM, {'regime': 'CALM', 'reason': 'no_benchmark'}
        
        # Calculate returns
        returns = prices.pct_change().dropna()
        
        if len(returns) < self.lookback:
            logger.warning("Insufficient data for regime detection.")
            return self.CALM, {'regime': 'CALM', 'reason': 'insufficient_data'}
        
        # 1. Benchmark volatility (annualized)
        benchmark_returns = returns[benchmark].tail(self.lookback)
        realized_vol = benchmark_returns.std() * np.sqrt(252)
        
        # 2. Correlation spike detection
        recent_corr = returns.tail(self.lookback).corr()
        avg_corr = (recent_corr.sum().sum() - len(recent_corr)) / (len(recent_corr) ** 2 - len(recent_corr))
        corr_spike = avg_corr > 0.6  # High correlation = crisis
        
        # 3. Volatility-of-volatility
        rolling_vol = returns[benchmark].rolling(5).std() * np.sqrt(252)
        vol_of_vol = rolling_vol.tail(self.lookback).std()
        vol_unstable = vol_of_vol > 0.10
        
        # 4. Sector dispersion (if possible)
        dispersion = returns.tail(self.lookback).std().std()
        
        # Regime logic
        info = {
            'realized_vol': realized_vol,
            'avg_correlation': avg_corr,
            'vol_of_vol': vol_of_vol,
            'dispersion': dispersion,
            'corr_spike': corr_spike,
            'vol_unstable': vol_unstable
        }
        
        if realized_vol >= self.vol_threshold_stressed or (corr_spike and vol_unstable):
            regime = self.STRESSED
        elif realized_vol >= self.vol_threshold_volatile or vol_unstable:
            regime = self.VOLATILE
        else:
            regime = self.CALM
        
        info['regime'] = self.REGIME_NAMES[regime]
        
        logger.info(f"Detected regime: {info['regime']} (vol={realized_vol:.2%})")
        
        return regime, info
    
    def get_regime_name(self, regime_id: int) -> str:
        """Get human-readable regime name."""
        return self.REGIME_NAMES.get(regime_id, 'UNKNOWN')


def is_regime_enabled() -> bool:
    """Check if regime switching is enabled."""
    config = get_config()
    return config.params.get('regime', {}).get('enabled', False)
