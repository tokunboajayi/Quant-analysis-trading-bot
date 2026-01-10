"""
Strategy Selector - Step 6 of Crazy Quant Ladder
=================================================
Modifies strategy parameters based on detected regime.
"""
import pandas as pd
from typing import Dict, Optional
from riskfusion.config import get_config
from riskfusion.models.regime_model import RegimeModel, is_regime_enabled
from riskfusion.utils.logging import get_logger

logger = get_logger("strategy_selector")


class StrategySelector:
    """
    Adjusts strategy parameters based on market regime.
    
    Parameters modified:
    - Target volatility
    - Gross exposure
    - Risk aversion (for optimizer)
    - Event overlay alpha
    """
    
    # Default parameters by regime
    REGIME_PARAMS = {
        RegimeModel.CALM: {
            'target_vol': 0.12,      # Normal target
            'gross_exposure': 1.0,   # Fully invested
            'risk_aversion': 1.0,    # Normal risk aversion
            'event_overlay_alpha': 0.5,
            'max_position': 0.10,
        },
        RegimeModel.VOLATILE: {
            'target_vol': 0.08,      # Reduce target vol
            'gross_exposure': 0.7,   # Reduce exposure
            'risk_aversion': 2.0,    # More risk averse
            'event_overlay_alpha': 0.7,  # Stronger event cuts
            'max_position': 0.07,
        },
        RegimeModel.STRESSED: {
            'target_vol': 0.05,      # Much lower target
            'gross_exposure': 0.4,   # Defensive
            'risk_aversion': 4.0,    # Very risk averse
            'event_overlay_alpha': 0.9,  # Aggressive event cuts
            'max_position': 0.05,
        }
    }
    
    def __init__(self):
        self.config = get_config()
        self.regime_model = RegimeModel()
        self.current_regime = RegimeModel.CALM
        self.current_params = self.REGIME_PARAMS[RegimeModel.CALM].copy()
    
    def update_regime(self, prices: pd.DataFrame) -> Dict:
        """
        Detect regime and update parameters.
        
        Args:
            prices: Price DataFrame for regime detection
        
        Returns:
            Dict with current parameters and regime info
        """
        if not is_regime_enabled():
            # Return base config parameters
            return self._get_base_params()
        
        # Detect regime
        regime, info = self.regime_model.detect_regime(prices)
        self.current_regime = regime
        
        # Get regime-specific parameters
        self.current_params = self.REGIME_PARAMS[regime].copy()
        
        logger.info(f"Strategy params updated for {info['regime']} regime: {self.current_params}")
        
        return {
            'regime': info['regime'],
            'regime_id': regime,
            'params': self.current_params,
            'info': info
        }
    
    def _get_base_params(self) -> Dict:
        """Get parameters from base config (regime disabled)."""
        portfolio = self.config.params.get('portfolio', {})
        optimizer = self.config.params.get('optimizer', {})
        
        return {
            'regime': 'DISABLED',
            'regime_id': -1,
            'params': {
                'target_vol': portfolio.get('target_vol_ann', 0.10),
                'gross_exposure': 1.0,
                'risk_aversion': optimizer.get('risk_aversion', 1.0),
                'event_overlay_alpha': portfolio.get('event_overlay', {}).get('alpha', 0.5),
                'max_position': portfolio.get('max_weight', 0.10),
            }
        }
    
    def get_current_params(self) -> Dict:
        """Get current strategy parameters."""
        return self.current_params
    
    def apply_to_weights(
        self,
        weights: pd.DataFrame,
        regime_params: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Apply regime-based adjustments to portfolio weights.
        
        Args:
            weights: DataFrame with 'weight' column
            regime_params: Optional params dict (uses current if None)
        
        Returns:
            Adjusted weights
        """
        params = regime_params or self.current_params
        result = weights.copy()
        
        # Scale by gross exposure
        gross_exposure = params.get('gross_exposure', 1.0)
        if gross_exposure < 1.0:
            result['weight'] = result['weight'] * gross_exposure
            result['regime_scaled'] = True
            logger.info(f"Weights scaled by gross exposure: {gross_exposure:.0%}")
        else:
            result['regime_scaled'] = False
        
        # Cap individual positions
        max_pos = params.get('max_position', 0.10)
        over_max = result['weight'] > max_pos
        if over_max.any():
            result.loc[over_max, 'weight'] = max_pos
            logger.info(f"Capped {over_max.sum()} positions to {max_pos:.0%}")
        
        return result


def get_regime_adjusted_params(prices: pd.DataFrame) -> Dict:
    """
    Convenience function to get regime-adjusted parameters.
    
    Args:
        prices: Price DataFrame
    
    Returns:
        Dict with regime and adjusted parameters
    """
    selector = StrategySelector()
    return selector.update_regime(prices)
