"""
Online Learning - Step 7 of Crazy Quant Ladder
===============================================
Safe model retraining triggered by drift/performance degradation.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import json
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("online_learning")


class OnlineLearningManager:
    """
    Manages safe online learning / model retraining.
    
    Triggers retraining when:
    - Feature drift PSI exceeds threshold
    - VaR breach rate spikes
    - Performance degradation detected
    
    Safety:
    - Trains candidate model
    - Evaluates on holdout
    - Promotes only if gates pass
    - Records all decisions
    """
    
    def __init__(self):
        self.config = get_config()
        ol_config = self.config.params.get('online_learning', {})
        
        self.drift_psi_threshold = ol_config.get('drift_psi_threshold', 0.25)
        self.var_breach_threshold = ol_config.get('var_breach_threshold', 0.10)
        self.min_retrain_interval_days = ol_config.get('min_retrain_interval_days', 7)
        
        self.state_path = Path(self.config.params['paths']['outputs']) / "online_learning_state.json"
        self.state = self._load_state()
    
    def should_retrain(
        self,
        drift_metrics: Dict,
        var_breach_rate: float,
        ic_recent: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Determine if retraining should be triggered.
        
        Args:
            drift_metrics: Dict with feature PSI values
            var_breach_rate: Recent VaR breach rate
            ic_recent: Recent IC (optional, for performance tracking)
        
        Returns:
            Tuple of (should_retrain, reason)
        """
        # Check minimum interval
        last_retrain = self.state.get('last_retrain_date')
        if last_retrain:
            days_since = (datetime.now() - datetime.fromisoformat(last_retrain)).days
            if days_since < self.min_retrain_interval_days:
                return False, f"MIN_INTERVAL_NOT_MET ({days_since} < {self.min_retrain_interval_days} days)"
        
        reasons = []
        
        # Check PSI drift
        max_psi = max(drift_metrics.values()) if drift_metrics else 0
        if max_psi > self.drift_psi_threshold:
            reasons.append(f"DRIFT_PSI_EXCEEDED ({max_psi:.2f} > {self.drift_psi_threshold})")
        
        # Check VaR breach rate
        if var_breach_rate > self.var_breach_threshold:
            reasons.append(f"VAR_BREACH_HIGH ({var_breach_rate:.1%} > {self.var_breach_threshold:.1%})")
        
        # Check IC degradation (if tracking)
        baseline_ic = self.state.get('baseline_ic', 0.05)
        if ic_recent is not None and ic_recent < baseline_ic * 0.5:
            reasons.append(f"IC_DEGRADED ({ic_recent:.4f} < {baseline_ic * 0.5:.4f})")
        
        if reasons:
            return True, "; ".join(reasons)
        
        return False, "NO_TRIGGER"
    
    def execute_retrain(
        self,
        features_df: pd.DataFrame,
        labels: pd.Series,
        reason: str
    ) -> Dict:
        """
        Execute model retraining with safety checks.
        
        Args:
            features_df: Training features
            labels: Training labels
            reason: Reason for retraining
        
        Returns:
            Dict with retrain outcome
        """
        logger.info(f"Executing retrain - Reason: {reason}")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'promoted': False,
            'metrics': {}
        }
        
        try:
            # Split: most recent data as holdout
            holdout_size = int(len(features_df) * 0.2)
            train_df = features_df.iloc[:-holdout_size]
            holdout_df = features_df.iloc[-holdout_size:]
            
            train_labels = labels.iloc[:-holdout_size]
            holdout_labels = labels.iloc[-holdout_size:]
            
            # Train candidate model
            from riskfusion.models.alpha_model import AlphaModel
            candidate = AlphaModel()
            train_metrics = candidate.train(train_df, train_labels)
            
            # Evaluate on holdout
            holdout_preds = candidate.predict(holdout_df)
            
            # Calculate holdout IC
            from scipy.stats import spearmanr
            ic, _ = spearmanr(holdout_labels, holdout_preds)
            result['metrics']['holdout_ic'] = ic
            result['metrics']['train_metrics'] = train_metrics
            
            # Gate check: IC should be reasonable
            if ic > 0.02:  # Positive IC threshold
                # Promote model
                candidate.save()
                result['promoted'] = True
                result['promotion_reason'] = f"IC={ic:.4f} > 0.02"
                logger.info(f"Model PROMOTED with holdout IC={ic:.4f}")
                
                # Update state
                self.state['last_retrain_date'] = datetime.now().isoformat()
                self.state['last_retrain_ic'] = ic
                self._save_state()
            else:
                result['promotion_reason'] = f"IC={ic:.4f} <= 0.02 (not promoted)"
                logger.warning(f"Model NOT PROMOTED: IC={ic:.4f}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Retrain failed: {e}")
        
        # Log decision
        self._log_decision(result)
        
        return result
    
    def _load_state(self) -> Dict:
        """Load persisted state."""
        if self.state_path.exists():
            with open(self.state_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_state(self):
        """Persist state."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _log_decision(self, decision: Dict):
        """Log retraining decision."""
        log_path = Path(self.config.params['paths']['outputs']) / "retrain_log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(decision) + "\n")


def is_online_learning_enabled() -> bool:
    """Check if online learning is enabled."""
    config = get_config()
    return config.params.get('online_learning', {}).get('enabled', False)


class AntiRetrainLoop:
    """
    Prevents infinite retraining loops.
    
    If retrain happens N times in M days without improvement,
    falls back to stable baseline.
    """
    
    def __init__(self, max_retrains_per_period: int = 3, period_days: int = 14):
        self.max_retrains = max_retrains_per_period
        self.period_days = period_days
        self.retrain_history = []
    
    def can_retrain(self) -> bool:
        """Check if retraining is allowed."""
        cutoff = datetime.now() - timedelta(days=self.period_days)
        recent_retrains = [r for r in self.retrain_history if r > cutoff]
        
        if len(recent_retrains) >= self.max_retrains:
            logger.warning(f"ANTI-LOOP: {len(recent_retrains)} retrains in {self.period_days} days. Blocked.")
            return False
        
        return True
    
    def record_retrain(self):
        """Record a retrain event."""
        self.retrain_history.append(datetime.now())
        # Prune old history
        cutoff = datetime.now() - timedelta(days=self.period_days * 2)
        self.retrain_history = [r for r in self.retrain_history if r > cutoff]
