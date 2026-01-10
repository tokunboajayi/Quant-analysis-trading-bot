"""
CVXPY Portfolio Optimizer - Step 3 of Crazy Quant Ladder
=========================================================
Convex optimization for portfolio construction with risk/cost awareness.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger
from riskfusion.portfolio.covariance import CovarianceEstimator

logger = get_logger("optimizer_cvxpy")

# Check if cvxpy is available
try:
    import cvxpy as cp
    CVXPY_AVAILABLE = True
except ImportError:
    CVXPY_AVAILABLE = False
    logger.warning("cvxpy not installed. Install with: pip install cvxpy")


class CVXPYOptimizer:
    """
    Convex portfolio optimizer using CVXPY.
    
    Objective:
        maximize: α'w - λ * w'Σw - cost * ||w - w_prev||₁
    
    Constraints:
        - 0 <= w <= max_weight (long only)
        - sum(w) <= gross_exposure
        - ||w - w_prev||₁ <= turnover_cap
    """
    
    def __init__(self):
        self.config = get_config()
        opt_config = self.config.params.get('optimizer', {})
        
        self.risk_aversion = opt_config.get('risk_aversion', 1.0)
        self.cost_bps = opt_config.get('cost_bps', 5)
        self.turnover_cap = opt_config.get('turnover_cap', 0.30)
        self.max_weight = self.config.params.get('portfolio', {}).get('max_weight', 0.10)
        self.long_only = self.config.params.get('portfolio', {}).get('long_only', True)
        
        self.cov_estimator = CovarianceEstimator(method='ledoit_wolf')
    
    def optimize(
        self,
        alpha: pd.Series,
        returns: pd.DataFrame,
        prev_weights: Optional[pd.Series] = None,
        gross_exposure: float = 1.0
    ) -> Tuple[pd.Series, Dict]:
        """
        Solve the portfolio optimization problem.
        
        Args:
            alpha: Expected returns/alpha scores per ticker
            returns: Historical returns for covariance estimation
            prev_weights: Previous portfolio weights (for turnover)
            gross_exposure: Target gross exposure (sum of |weights|)
        
        Returns:
            Tuple of (optimal weights Series, info dict)
        """
        if not CVXPY_AVAILABLE:
            raise ImportError("cvxpy is required for this optimizer")
        
        tickers = alpha.index.tolist()
        n = len(tickers)
        
        logger.info(f"Optimizing portfolio: {n} assets")
        
        # Estimate covariance
        returns_aligned = returns[tickers] if all(t in returns.columns for t in tickers) else returns
        cov_matrix = self.cov_estimator.estimate(returns_aligned)
        
        # Ensure dimensions match
        if cov_matrix.shape[0] != n:
            logger.warning(f"Covariance dimension mismatch. Using diagonal.")
            cov_matrix = np.diag(returns_aligned.var().values[:n])
        
        # Alpha vector
        alpha_vec = alpha.values
        
        # Previous weights (default to zero)
        if prev_weights is None:
            w_prev = np.zeros(n)
        else:
            w_prev = prev_weights.reindex(tickers).fillna(0).values
        
        # Define optimization variable
        w = cp.Variable(n)
        
        # Objective components
        # 1. Alpha (maximize)
        alpha_term = alpha_vec @ w
        
        # 2. Risk penalty (minimize variance)
        # Ensure covariance is PSD
        cov_matrix = self._ensure_psd(cov_matrix)
        risk_term = cp.quad_form(w, cov_matrix)
        
        # 3. Transaction cost (minimize turnover)
        cost_term = cp.norm(w - w_prev, 1)
        
        # Full objective
        cost_multiplier = self.cost_bps / 10000  # Convert bps to decimal
        objective = cp.Maximize(
            alpha_term 
            - self.risk_aversion * risk_term 
            - cost_multiplier * cost_term
        )
        
        # Constraints
        constraints = []
        
        # Long-only
        if self.long_only:
            constraints.append(w >= 0)
        
        # Max weight per asset
        constraints.append(w <= self.max_weight)
        
        # Gross exposure (fully invested or less)
        constraints.append(cp.sum(w) <= gross_exposure)
        constraints.append(cp.sum(w) >= 0)  # No shorting overall
        
        # Turnover constraint
        constraints.append(cp.norm(w - w_prev, 1) <= self.turnover_cap)
        
        # Solve
        problem = cp.Problem(objective, constraints)
        
        try:
            problem.solve(solver=cp.ECOS, verbose=False)
            
            if problem.status not in ['optimal', 'optimal_inaccurate']:
                logger.warning(f"Optimization status: {problem.status}")
                # Fallback to equal weight
                return self._fallback_weights(tickers), {'status': problem.status}
            
            # Extract solution
            optimal_weights = pd.Series(w.value, index=tickers)
            
            # Clip tiny weights to zero
            optimal_weights = optimal_weights.clip(lower=0)
            optimal_weights[optimal_weights < 0.001] = 0
            
            # Normalize to sum to gross_exposure
            if optimal_weights.sum() > 0:
                optimal_weights = optimal_weights / optimal_weights.sum() * gross_exposure
            
            # Info
            info = {
                'status': problem.status,
                'objective': problem.value,
                'risk': float(risk_term.value) if risk_term.value else 0,
                'turnover': float(np.sum(np.abs(optimal_weights.values - w_prev))),
                'n_positions': (optimal_weights > 0.001).sum()
            }
            
            logger.info(f"Optimization complete: {info['n_positions']} positions, "
                       f"turnover={info['turnover']:.2%}")
            
            return optimal_weights, info
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return self._fallback_weights(tickers), {'status': 'ERROR', 'error': str(e)}
    
    def _ensure_psd(self, cov: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
        """Ensure covariance matrix is positive semi-definite."""
        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        
        # Clip negative eigenvalues
        eigenvalues = np.maximum(eigenvalues, epsilon)
        
        # Reconstruct
        return eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    
    def _fallback_weights(self, tickers: list) -> pd.Series:
        """Return equal-weight fallback."""
        n = len(tickers)
        weight = min(1.0 / n, self.max_weight)
        return pd.Series(weight, index=tickers)


def is_cvxpy_enabled() -> bool:
    """Check if CVXPY optimizer is enabled in config."""
    config = get_config()
    method = config.params.get('optimizer', {}).get('method', 'heuristic')
    return method == 'cvxpy' and CVXPY_AVAILABLE
