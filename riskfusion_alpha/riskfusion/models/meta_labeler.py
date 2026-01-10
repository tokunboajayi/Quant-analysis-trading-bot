"""
Meta-Labeler Model - Step 2 of Crazy Quant Ladder
==================================================
Predicts whether an alpha signal should be traded.
Acts as a trade filter to improve precision.
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
from pathlib import Path
from typing import Dict, Optional
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger
from riskfusion.labeling.meta_labels import create_meta_labels, create_meta_features

logger = get_logger("meta_labeler")


class MetaLabeler:
    """
    Meta-model that predicts whether to act on an alpha signal.
    
    P(good_trade | alpha_signal, features) -> meta_prob
    
    Usage in portfolio:
    - weight = base_weight * meta_prob (if apply_as_multiplier=True)
    - OR filter out where meta_prob < threshold
    """
    
    def __init__(self):
        self.config = get_config()
        self.meta_config = self.config.params.get('meta', {})
        self.threshold = self.meta_config.get('threshold', 0.55)
        self.apply_as_multiplier = self.meta_config.get('apply_as_multiplier', True)
        self.model: Optional[lgb.LGBMClassifier] = None
        self.model_path = Path(self.config.params['paths']['models']) / "meta_labeler.pkl"
        
        # Features for meta-model (combines base + meta-specific)
        self.base_features = [
            'ret_1d', 'ret_5d', 'ret_20d',
            'realized_vol_20d', 'rsi',
            'xs_mom_20d', 'xs_vol_20d'
        ]
        self.meta_features = [
            'vol_regime', 'vol_zscore',
            'momentum_consistency', 'rsi_extreme',
            'consensus_strength'
        ]
    
    def train(
        self,
        features_df: pd.DataFrame,
        alpha_predictions: pd.Series,
        forward_returns: pd.Series
    ) -> Dict[str, float]:
        """
        Train meta-labeler on historical data.
        
        Args:
            features_df: Features with date/ticker index
            alpha_predictions: Alpha model predictions
            forward_returns: Realized 5D returns
        
        Returns:
            Dict with training metrics
        """
        logger.info("Training Meta-Labeler...")
        
        # Create labels
        labels_df = create_meta_labels(features_df, alpha_predictions, forward_returns)
        
        # Create meta-specific features
        meta_feats = create_meta_features(features_df)
        
        # Combine features
        all_features = []
        for f in self.base_features:
            if f in features_df.columns:
                all_features.append(f)
        for f in self.meta_features:
            if f in meta_feats.columns:
                all_features.append(f)
        
        # Align data
        common_idx = labels_df.index.intersection(meta_feats.index)
        X = pd.concat([
            features_df.loc[common_idx, [f for f in self.base_features if f in features_df.columns]],
            meta_feats.loc[common_idx]
        ], axis=1).fillna(0)
        
        y = labels_df.loc[common_idx, 'meta_label']
        
        logger.info(f"Training data: {len(X)} samples, {len(X.columns)} features")
        logger.info(f"Label distribution: {y.value_counts().to_dict()}")
        
        # Train classifier
        self.model = lgb.LGBMClassifier(
            objective='binary',
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4,
            num_leaves=15,
            min_child_samples=30,
            class_weight='balanced',
            random_state=42,
            verbosity=-1
        )
        
        self.model.fit(X, y)
        
        # Calculate metrics
        probs = self.model.predict_proba(X)[:, 1]
        from sklearn.metrics import roc_auc_score, precision_score
        
        auc = roc_auc_score(y, probs)
        preds = (probs >= self.threshold).astype(int)
        precision = precision_score(y, preds, zero_division=0)
        
        metrics = {
            'auc': auc,
            'precision': precision,
            'threshold': self.threshold,
            'n_samples': len(X),
            'hit_rate': y.mean()
        }
        
        logger.info(f"Meta-Labeler trained: AUC={auc:.4f}, Precision={precision:.4f}")
        
        # Save model
        self.save()
        
        return metrics
    
    def predict(self, features_df: pd.DataFrame) -> pd.Series:
        """
        Predict meta-probability for each observation.
        
        Args:
            features_df: Features DataFrame
        
        Returns:
            Series of meta_prob values (0 to 1)
        """
        if self.model is None:
            self.load()
        
        if self.model is None:
            logger.warning("No meta-labeler model found. Returning 1.0 for all.")
            return pd.Series(1.0, index=features_df.index)
        
        # Create meta features
        meta_feats = create_meta_features(features_df)
        
        # Build feature matrix
        X = pd.concat([
            features_df[[f for f in self.base_features if f in features_df.columns]],
            meta_feats
        ], axis=1).fillna(0)
        
        # Ensure same columns as training
        missing_cols = set(self.model.feature_name_) - set(X.columns)
        for col in missing_cols:
            X[col] = 0
        X = X[self.model.feature_name_]
        
        probs = self.model.predict_proba(X)[:, 1]
        
        return pd.Series(probs, index=features_df.index, name='meta_prob')
    
    def apply_to_weights(self, weights: pd.DataFrame, meta_probs: pd.Series) -> pd.DataFrame:
        """
        Apply meta-filter to portfolio weights.
        
        Args:
            weights: DataFrame with 'weight' column, ticker as index
            meta_probs: Series of meta_prob values
        
        Returns:
            Adjusted weights DataFrame
        """
        result = weights.copy()
        
        # Align meta_probs to weights index
        aligned_probs = meta_probs.reindex(weights.index).fillna(1.0)
        
        if self.apply_as_multiplier:
            # Scale weights by meta_prob
            result['weight'] = result['weight'] * aligned_probs
            result['meta_applied'] = 'MULTIPLIER'
        else:
            # Filter out low-confidence trades
            mask = aligned_probs >= self.threshold
            result.loc[~mask, 'weight'] = 0
            result['meta_applied'] = mask.map({True: 'PASSED', False: 'FILTERED'})
        
        # Renormalize weights?
        # Optional: result['weight'] = result['weight'] / result['weight'].sum()
        
        return result
    
    def save(self):
        """Save model to disk."""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, self.model_path)
        logger.info(f"Meta-Labeler saved to {self.model_path}")
    
    def load(self):
        """Load model from disk."""
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)
            logger.info(f"Meta-Labeler loaded from {self.model_path}")
        else:
            logger.warning(f"Meta-Labeler not found at {self.model_path}")


def is_meta_enabled() -> bool:
    """Check if meta-labeler is enabled in config."""
    config = get_config()
    return config.params.get('meta', {}).get('enabled', False)
