"""
Covariance Estimation - Step 3 of Crazy Quant Ladder
=====================================================
Provides covariance matrix estimation for portfolio optimization.
Uses Ledoit-Wolf shrinkage for robustness.
"""
import pandas as pd
import numpy as np
from typing import Optional
from riskfusion.utils.logging import get_logger

logger = get_logger("covariance")


class CovarianceEstimator:
    """
    Covariance matrix estimator with shrinkage.
    
    Methods:
    - sample: Raw sample covariance
    - ledoit_wolf: Shrunk covariance (more stable)
    - diagonal: Diagonal only (fastest, ignores correlations)
    """
    
    def __init__(self, method: str = "ledoit_wolf", lookback: int = 60):
        self.method = method
        self.lookback = lookback
    
    def estimate(self, returns: pd.DataFrame) -> np.ndarray:
        """
        Estimate covariance matrix from returns.
        
        Args:
            returns: DataFrame with tickers as columns, dates as index
        
        Returns:
            Covariance matrix as numpy array (n_assets x n_assets)
        """
        # Use most recent lookback period
        recent = returns.tail(self.lookback).dropna(axis=1, how='any')
        
        if len(recent) < 20:
            logger.warning(f"Insufficient data for covariance: {len(recent)} days")
            # Return diagonal matrix based on variance
            var = returns.var().values
            return np.diag(var)
        
        if self.method == "sample":
            return self._sample_cov(recent)
        elif self.method == "ledoit_wolf":
            return self._ledoit_wolf(recent)
        elif self.method == "diagonal":
            return self._diagonal(recent)
        else:
            logger.warning(f"Unknown method {self.method}, using ledoit_wolf")
            return self._ledoit_wolf(recent)
    
    def _sample_cov(self, returns: pd.DataFrame) -> np.ndarray:
        """Raw sample covariance."""
        return returns.cov().values
    
    def _diagonal(self, returns: pd.DataFrame) -> np.ndarray:
        """Diagonal covariance (variances only)."""
        return np.diag(returns.var().values)
    
    def _ledoit_wolf(self, returns: pd.DataFrame) -> np.ndarray:
        """
        Ledoit-Wolf shrinkage estimator.
        Shrinks towards scaled identity matrix.
        """
        try:
            from sklearn.covariance import LedoitWolf
            lw = LedoitWolf().fit(returns.values)
            logger.info(f"Ledoit-Wolf shrinkage: {lw.shrinkage_:.4f}")
            return lw.covariance_
        except ImportError:
            logger.warning("sklearn not available, using sample covariance")
            return self._sample_cov(returns)
        except Exception as e:
            logger.warning(f"Ledoit-Wolf failed: {e}, using sample")
            return self._sample_cov(returns)


def compute_correlation_matrix(returns: pd.DataFrame, lookback: int = 60) -> pd.DataFrame:
    """
    Compute rolling correlation matrix.
    
    Args:
        returns: DataFrame with tickers as columns
        lookback: Rolling window in days
    
    Returns:
        Correlation matrix as DataFrame
    """
    recent = returns.tail(lookback).dropna(axis=1, how='any')
    return recent.corr()


def estimate_factor_model_cov(
    returns: pd.DataFrame,
    n_factors: int = 5
) -> np.ndarray:
    """
    Factor model covariance (PCA-based).
    
    Decomposes returns into factors and estimates:
    Σ = B @ Σ_f @ B' + D
    
    Where B is factor loadings, Σ_f is factor cov, D is idiosyncratic var.
    """
    try:
        from sklearn.decomposition import PCA
        
        # Clean data
        clean = returns.dropna(axis=1, how='any').tail(252)
        
        if len(clean.columns) < n_factors:
            n_factors = len(clean.columns) - 1
        
        # Fit PCA
        pca = PCA(n_components=n_factors)
        factors = pca.fit_transform(clean.values)
        loadings = pca.components_.T  # n_assets x n_factors
        
        # Factor covariance
        factor_cov = np.cov(factors.T)
        
        # Idiosyncratic variance
        residuals = clean.values - factors @ loadings.T
        idio_var = np.var(residuals, axis=0)
        
        # Full covariance
        cov = loadings @ factor_cov @ loadings.T + np.diag(idio_var)
        
        return cov
        
    except Exception as e:
        logger.warning(f"Factor model failed: {e}")
        return CovarianceEstimator().estimate(returns)
