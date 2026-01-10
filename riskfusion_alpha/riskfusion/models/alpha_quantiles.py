"""
Alpha Quantiles Model - Step 1 of Crazy Quant Ladder
=====================================================
Trains LightGBM quantile regressors for q10, q50, q90 forward 5D returns.
Uses quantile-derived score for ranking instead of single alpha.
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
from pathlib import Path
from typing import Dict, List, Tuple
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("alpha_quantiles")


class AlphaQuantilesModel:
    """
    Distributional Alpha Model using LightGBM Quantile Regression.
    
    Predicts q10, q50, q90 of forward 5D returns.
    Score = q50 / (|q10| + eps) -> higher is better (upside/downside ratio)
    """
    
    def __init__(self):
        self.config = get_config()
        self.quantiles = self.config.params.get('alpha', {}).get('quantiles', [0.1, 0.5, 0.9])
        self.quality_formula = self.config.params.get('alpha', {}).get('quality_formula', 'q50_over_abs_q10')
        self.models: Dict[float, lgb.LGBMRegressor] = {}
        self.features = [
            'ret_1d', 'ret_5d', 'ret_20d',
            'realized_vol_20d', 'rsi',
            'xs_mom_20d', 'xs_vol_20d'
        ]
        self.target = 'target_fwd_5d'
        self.model_dir = Path(self.config.params['paths']['models'])
        
    def train(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Train quantile regressors for each quantile.
        
        Returns:
            Dict with training metrics per quantile
        """
        logger.info(f"Training Alpha Quantiles Model for q={self.quantiles}")
        
        # Prepare data
        train_df = df.dropna(subset=self.features + [self.target])
        X = train_df[self.features]
        y = train_df[self.target]
        
        if len(X) < 100:
            raise ValueError(f"Insufficient training data: {len(X)} rows")
        
        metrics = {}
        
        for q in self.quantiles:
            logger.info(f"Training quantile q={q}...")
            
            model = lgb.LGBMRegressor(
                objective='quantile',
                alpha=q,
                n_estimators=100,
                learning_rate=0.05,
                max_depth=5,
                num_leaves=31,
                min_child_samples=20,
                random_state=42,
                verbosity=-1
            )
            
            model.fit(X, y)
            self.models[q] = model
            
            # Calculate pinball loss on training data
            preds = model.predict(X)
            pinball = self._pinball_loss(y, preds, q)
            metrics[f'pinball_q{int(q*100)}'] = pinball
            logger.info(f"  q={q} Pinball Loss: {pinball:.6f}")
        
        # Save models
        self.save()
        
        return metrics
    
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict q10, q50, q90 and compute quality score.
        Enforces monotonicity: q10 <= q50 <= q90
        
        Returns:
            DataFrame with columns: q10, q50, q90, quantile_score
        """
        if not self.models:
            self.load()
            
        X = df[self.features].fillna(0)
        
        predictions = {}
        for q in self.quantiles:
            if q not in self.models:
                raise ValueError(f"Model for quantile {q} not found")
            predictions[f'q{int(q*100)}'] = self.models[q].predict(X)
        
        result = pd.DataFrame(predictions, index=df.index)
        
        # Enforce monotonicity: sort q10 <= q50 <= q90
        result = self._enforce_monotonicity(result)
        
        # Calculate quality score
        result['quantile_score'] = self._compute_quality_score(result)
        
        return result
    
    def _enforce_monotonicity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure q10 <= q50 <= q90 by sorting.
        Records violation rate.
        """
        q10_col = 'q10'
        q50_col = 'q50'
        q90_col = 'q90'
        
        # Check violations before fix
        violations = (df[q10_col] > df[q50_col]) | (df[q50_col] > df[q90_col])
        violation_rate = violations.sum() / len(df)
        
        if violation_rate > 0:
            logger.warning(f"Monotonicity violations: {violation_rate:.2%} of rows")
            
            # Fix by sorting each row
            for idx in df.index:
                vals = sorted([df.loc[idx, q10_col], df.loc[idx, q50_col], df.loc[idx, q90_col]])
                df.loc[idx, q10_col] = vals[0]
                df.loc[idx, q50_col] = vals[1]
                df.loc[idx, q90_col] = vals[2]
        
        return df
    
    def _compute_quality_score(self, df: pd.DataFrame) -> pd.Series:
        """
        Compute quality score based on config formula.
        """
        eps = 1e-6
        
        if self.quality_formula == 'q50_over_abs_q10':
            # Edge / Downside ratio
            return df['q50'] / (df['q10'].abs() + eps)
        elif self.quality_formula == 'q90_over_abs_q10':
            # Upside / Downside ratio
            return df['q90'] / (df['q10'].abs() + eps)
        else:
            # Default to q50
            return df['q50']
    
    def _pinball_loss(self, y_true: pd.Series, y_pred: np.ndarray, q: float) -> float:
        """Calculate pinball (quantile) loss."""
        errors = y_true.values - y_pred
        return np.mean(np.where(errors >= 0, q * errors, (q - 1) * errors))
    
    def save(self):
        """Save all quantile models."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        for q, model in self.models.items():
            path = self.model_dir / f"alpha_q{int(q*100)}.pkl"
            joblib.dump(model, path)
            logger.info(f"Saved quantile model to {path}")
    
    def load(self):
        """Load all quantile models."""
        for q in self.quantiles:
            path = self.model_dir / f"alpha_q{int(q*100)}.pkl"
            if path.exists():
                self.models[q] = joblib.load(path)
                logger.info(f"Loaded quantile model from {path}")
            else:
                logger.warning(f"Quantile model not found: {path}")


def is_quantiles_enabled() -> bool:
    """Check if quantile alpha is enabled in config."""
    config = get_config()
    return config.params.get('alpha', {}).get('use_quantiles', False)
