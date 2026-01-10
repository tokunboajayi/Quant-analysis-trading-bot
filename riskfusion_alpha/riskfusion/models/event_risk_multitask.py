"""
Multi-Task Event Risk Model - Step 5 of Crazy Quant Ladder
============================================================
Extends event risk from binary impact to:
- P(high impact)
- P(negative direction)
- Magnitude bucket (small/medium/large)
"""
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from typing import Dict, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
import lightgbm as lgb
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("event_risk_multitask")


class MultiTaskEventRiskModel:
    """
    Multi-output Event Risk Model.
    
    Predicts:
    1. P(high_impact): Probability of >2% move
    2. P(negative): Probability move is negative
    3. magnitude_bucket: 0=small, 1=medium, 2=large
    
    Used in overlay to cut positions with P(high_impact) × P(negative) > threshold.
    """
    
    def __init__(self):
        self.config = get_config()
        self.model_dir = Path(self.config.params['paths']['models'])
        
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.impact_model: Optional[lgb.LGBMClassifier] = None
        self.direction_model: Optional[lgb.LGBMClassifier] = None
        self.magnitude_model: Optional[lgb.LGBMClassifier] = None
        
    def train(self, labeled_events: pd.DataFrame) -> Dict[str, float]:
        """
        Train multi-task models on labeled events.
        
        Required columns:
        - title, description: Event text
        - high_impact: 1 if |return| > 2%, else 0
        - negative: 1 if return < 0, else 0
        - magnitude_bucket: 0=small (<2%), 1=medium (2-5%), 2=large (>5%)
        
        Returns:
            Dict with training metrics per task
        """
        if labeled_events.empty:
            logger.warning("No data to train.")
            return {}
        
        logger.info(f"Training Multi-Task Event Risk on {len(labeled_events)} events...")
        
        # Prepare text
        X_text = labeled_events['title'].fillna('') + " " + labeled_events['description'].fillna('')
        
        # Vectorize
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        X = self.vectorizer.fit_transform(X_text)
        
        metrics = {}
        
        # Task 1: High Impact (binary)
        if 'high_impact' in labeled_events.columns:
            y_impact = labeled_events['high_impact'].fillna(0).astype(int)
            self.impact_model = lgb.LGBMClassifier(
                objective='binary', n_estimators=100, learning_rate=0.05,
                max_depth=5, is_unbalance=True, random_state=42, verbosity=-1
            )
            self.impact_model.fit(X, y_impact)
            
            # AUC on training
            from sklearn.metrics import roc_auc_score
            probs = self.impact_model.predict_proba(X)[:, 1]
            auc = roc_auc_score(y_impact, probs) if y_impact.sum() > 0 else 0.5
            metrics['impact_auc'] = auc
            logger.info(f"Impact model AUC: {auc:.4f}")
        
        # Task 2: Direction (binary - negative or not)
        if 'negative' in labeled_events.columns:
            y_neg = labeled_events['negative'].fillna(0).astype(int)
            self.direction_model = lgb.LGBMClassifier(
                objective='binary', n_estimators=100, learning_rate=0.05,
                max_depth=5, is_unbalance=True, random_state=42, verbosity=-1
            )
            self.direction_model.fit(X, y_neg)
            
            probs = self.direction_model.predict_proba(X)[:, 1]
            auc = roc_auc_score(y_neg, probs) if y_neg.sum() > 0 else 0.5
            metrics['direction_auc'] = auc
            logger.info(f"Direction model AUC: {auc:.4f}")
        
        # Task 3: Magnitude bucket (multiclass)
        if 'magnitude_bucket' in labeled_events.columns:
            y_mag = labeled_events['magnitude_bucket'].fillna(0).astype(int)
            self.magnitude_model = lgb.LGBMClassifier(
                objective='multiclass', num_class=3, n_estimators=100,
                learning_rate=0.05, max_depth=5, random_state=42, verbosity=-1
            )
            self.magnitude_model.fit(X, y_mag)
            
            from sklearn.metrics import accuracy_score
            preds = self.magnitude_model.predict(X)
            acc = accuracy_score(y_mag, preds)
            metrics['magnitude_accuracy'] = acc
            logger.info(f"Magnitude model accuracy: {acc:.4f}")
        
        # Save all models
        self.save()
        
        return metrics
    
    def predict(self, events: pd.DataFrame) -> pd.DataFrame:
        """
        Predict multi-task outputs.
        
        Returns:
            DataFrame with columns:
            - event_risk_prob: P(high impact)
            - event_neg_prob: P(negative)
            - event_mag_bucket: Predicted magnitude class
            - event_combined_risk: P(impact) * P(negative)
        """
        if events.empty:
            return pd.DataFrame()
        
        self.load()
        
        if self.vectorizer is None:
            logger.warning("Vectorizer not loaded. Returning zeros.")
            return pd.DataFrame({
                'event_risk_prob': 0.0,
                'event_neg_prob': 0.5,
                'event_mag_bucket': 0,
                'event_combined_risk': 0.0
            }, index=events.index)
        
        # Vectorize
        X_text = events['title'].fillna('') + " " + events['description'].fillna('')
        X = self.vectorizer.transform(X_text)
        
        result = pd.DataFrame(index=events.index)
        
        # Task 1: Impact
        if self.impact_model:
            result['event_risk_prob'] = self.impact_model.predict_proba(X)[:, 1]
        else:
            result['event_risk_prob'] = 0.0
        
        # Task 2: Direction
        if self.direction_model:
            result['event_neg_prob'] = self.direction_model.predict_proba(X)[:, 1]
        else:
            result['event_neg_prob'] = 0.5  # Neutral assumption
        
        # Task 3: Magnitude
        if self.magnitude_model:
            result['event_mag_bucket'] = self.magnitude_model.predict(X)
        else:
            result['event_mag_bucket'] = 0
        
        # Combined risk (for overlay)
        result['event_combined_risk'] = result['event_risk_prob'] * result['event_neg_prob']
        
        return result
    
    def save(self):
        """Save all models."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        if self.vectorizer:
            joblib.dump(self.vectorizer, self.model_dir / "event_vectorizer.pkl")
        if self.impact_model:
            joblib.dump(self.impact_model, self.model_dir / "event_impact_model.pkl")
        if self.direction_model:
            joblib.dump(self.direction_model, self.model_dir / "event_direction_model.pkl")
        if self.magnitude_model:
            joblib.dump(self.magnitude_model, self.model_dir / "event_magnitude_model.pkl")
        
        logger.info("Multi-task event models saved.")
    
    def load(self):
        """Load all models."""
        vec_path = self.model_dir / "event_vectorizer.pkl"
        if vec_path.exists():
            self.vectorizer = joblib.load(vec_path)
        
        imp_path = self.model_dir / "event_impact_model.pkl"
        if imp_path.exists():
            self.impact_model = joblib.load(imp_path)
        
        dir_path = self.model_dir / "event_direction_model.pkl"
        if dir_path.exists():
            self.direction_model = joblib.load(dir_path)
        
        mag_path = self.model_dir / "event_magnitude_model.pkl"
        if mag_path.exists():
            self.magnitude_model = joblib.load(mag_path)


def is_multitask_enabled() -> bool:
    """Check if multi-task event risk is enabled."""
    config = get_config()
    return config.params.get('event', {}).get('multitask', False)


def create_multitask_labels(events: pd.DataFrame, returns: pd.Series) -> pd.DataFrame:
    """
    Create labels for multi-task training.
    
    Args:
        events: Events DataFrame with date, ticker
        returns: Forward returns Series
    
    Returns:
        Labeled DataFrame with high_impact, negative, magnitude_bucket
    """
    result = events.copy()
    
    # Align returns
    aligned_returns = returns.reindex(events.index).fillna(0)
    
    # Binary labels
    result['high_impact'] = (np.abs(aligned_returns) > 0.02).astype(int)
    result['negative'] = (aligned_returns < 0).astype(int)
    
    # Magnitude buckets
    abs_returns = np.abs(aligned_returns)
    result['magnitude_bucket'] = 0  # small
    result.loc[abs_returns > 0.02, 'magnitude_bucket'] = 1  # medium
    result.loc[abs_returns > 0.05, 'magnitude_bucket'] = 2  # large
    
    return result
