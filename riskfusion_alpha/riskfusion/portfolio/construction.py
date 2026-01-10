import pandas as pd
import numpy as np
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("portfolio_construction")

class PortfolioOptimizer:
    def __init__(self):
        self.config = get_config()
        self.params = self.config.params['portfolio']

    def construct_weights(self, alpha_scores: pd.Series, risk_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Convert alpha scores to weights.
        alpha_scores: Series indexed by ticker
        risk_data: DataFrame with cols [vol_hat, var_hat, event_risk] indexed by ticker
        """
        # 1. Select Universe
        # Filter available tickers
        score = alpha_scores.dropna().sort_values(ascending=False)
        
        top_n = self.params.get('top_n', 20)
        long_only = self.params.get('long_only', True)
        
        selected = score.head(top_n)
        
        if selected.empty:
            return pd.DataFrame()
            
        # 2. Base Weights (Proportional to Score for now, or Equal Weight)
        # Using Rank weighting is robust
        # rank 1 = best
        ranks = pd.Series(np.arange(len(selected)) + 1, index=selected.index)
        # weight ~ 1/rank or linear? Let's use equal weight for MVP robustness
        # weights = pd.Series(1.0 / len(selected), index=selected.index)
        
        # Or score based:
        # Prevent negative scores if using regressor
        # scores = selected - selected.min() + 1e-6
        # weights = scores / scores.sum()
        
        # Simple Equal Weight for Top N
        weights = pd.Series(1.0 / len(selected), index=selected.index)
        
        # 3. Risk Scaling (Vol Target)
        target_vol = self.params.get('target_vol_ann', 0.10)
        
        if risk_data is not None:
            # Join risk data
            w_df = weights.to_frame('weight').join(risk_data)
            
            # Vol Scaling constraint: 
            # If (weight * vol) > budget? No.
            # Portfolio Vol approx = sqrt(sum (w * vol)^2) assuming uncorrelated
            # Real way: w_i = (TargetVol / N) / vol_i ? 
            # Inverse Volatility Weighting
            
            # Use Inverse Vol weighting
            if 'vol_hat' in w_df.columns:
                # Handle NaNs and Zeros robustness
                vol_safe = w_df['vol_hat'].fillna(0.0)
                # Clip negative or zero vol to small epsilon (e.g. 0.1% daily)
                vol_safe = vol_safe.clip(lower=0.001)
                
                inv_vol = 1.0 / vol_safe
                
                if inv_vol.sum() > 0:
                    weights = inv_vol / inv_vol.sum()
                    w_df['weight'] = weights
                else:
                    logger.warning("All volatilities invalid. Falling back to equal weight.")

            # 4. Event Overlay
            if self.params.get('event_overlay', {}).get('enabled', False):
                # Reduce weight if event risk is high
                if 'event_risk' in w_df.columns:
                    mult = 1.0 - (self.params['event_overlay']['alpha'] * w_df['event_risk'])
                    mult = mult.clip(lower=self.params['event_overlay']['multiplier_min'])
                    w_df['weight'] *= mult
            
            weights = w_df['weight']

        # 5. Normalize (Gross Exposure = 1.0 or less)
        # If long only, sum = 1
        if weights.sum() > 0:
            weights = weights / weights.sum()

        # 6. Max Weight Constraint
        max_w = self.params.get('max_weight', 0.10)
        weights = weights.clip(upper=max_w)
        
        # Renormalize after clip
        if weights.sum() > 0:
            weights = weights / weights.sum()
        # FINAL SAFETY CHECK (Extreme)
        weights = weights.astype(float)
        weights = weights.replace([np.inf, -np.inf], np.nan)
        
        if weights.isnull().any():
            nan_tickers = weights[weights.isnull()].index.tolist()
            logger.error(f"NaNs/Infs detected in final weights for: {nan_tickers}")
            weights = weights.fillna(0.0)
            
        return weights.to_frame('weight')

