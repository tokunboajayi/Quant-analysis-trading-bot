"""
Tests for CVXPY Optimizer (Step 3)
===================================
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock


class TestCovarianceEstimator:
    """Test covariance estimation."""
    
    def test_sample_covariance(self):
        """Test sample covariance calculation."""
        from riskfusion.portfolio.covariance import CovarianceEstimator
        
        # Create test returns
        np.random.seed(42)
        returns = pd.DataFrame(
            np.random.randn(100, 3) * 0.02,
            columns=['A', 'B', 'C']
        )
        
        estimator = CovarianceEstimator(method='sample', lookback=60)
        cov = estimator.estimate(returns)
        
        assert cov.shape == (3, 3)
        assert np.allclose(cov, cov.T)  # Symmetric
        assert np.all(np.linalg.eigvals(cov) >= -1e-10)  # PSD
    
    def test_diagonal_covariance(self):
        """Test diagonal covariance (variances only)."""
        from riskfusion.portfolio.covariance import CovarianceEstimator
        
        np.random.seed(42)
        returns = pd.DataFrame(
            np.random.randn(100, 3) * 0.02,
            columns=['A', 'B', 'C']
        )
        
        estimator = CovarianceEstimator(method='diagonal', lookback=60)
        cov = estimator.estimate(returns)
        
        # Should be diagonal
        off_diag = cov - np.diag(np.diag(cov))
        assert np.allclose(off_diag, 0)


class TestCVXPYOptimizer:
    """Test CVXPY optimizer."""
    
    @patch('riskfusion.portfolio.optimizer_cvxpy.get_config')
    def test_optimizer_returns_weights(self, mock_config):
        """Test that optimizer returns valid weights."""
        pytest.importorskip('cvxpy')  # Skip if cvxpy not installed
        
        from riskfusion.portfolio.optimizer_cvxpy import CVXPYOptimizer
        
        mock_config.return_value.params = {
            'optimizer': {'risk_aversion': 1.0, 'cost_bps': 5, 'turnover_cap': 0.30},
            'portfolio': {'max_weight': 0.20, 'long_only': True}
        }
        
        optimizer = CVXPYOptimizer()
        
        # Test data
        alpha = pd.Series([0.05, 0.03, 0.01], index=['A', 'B', 'C'])
        returns = pd.DataFrame(
            np.random.randn(100, 3) * 0.02,
            columns=['A', 'B', 'C']
        )
        
        weights, info = optimizer.optimize(alpha, returns)
        
        # Weights should be valid
        assert len(weights) == 3
        assert all(weights >= 0)  # Long only
        assert all(weights <= 0.21)  # Max weight (with tolerance)
        assert info['status'] in ['optimal', 'optimal_inaccurate']
    
    @patch('riskfusion.portfolio.optimizer_cvxpy.get_config')
    def test_turnover_constraint_respected(self, mock_config):
        """Test that turnover constraint is respected."""
        pytest.importorskip('cvxpy')
        
        from riskfusion.portfolio.optimizer_cvxpy import CVXPYOptimizer
        
        mock_config.return_value.params = {
            'optimizer': {'risk_aversion': 1.0, 'cost_bps': 5, 'turnover_cap': 0.30},
            'portfolio': {'max_weight': 0.50, 'long_only': True}
        }
        
        optimizer = CVXPYOptimizer()
        
        alpha = pd.Series([0.05, 0.03, 0.01], index=['A', 'B', 'C'])
        returns = pd.DataFrame(
            np.random.randn(100, 3) * 0.02,
            columns=['A', 'B', 'C']
        )
        
        # Previous weights
        prev_weights = pd.Series([0.4, 0.4, 0.2], index=['A', 'B', 'C'])
        
        weights, info = optimizer.optimize(alpha, returns, prev_weights)
        
        # Turnover should be within constraint
        turnover = np.sum(np.abs(weights.values - prev_weights.values))
        assert turnover <= 0.31  # Allowing small tolerance
    
    @patch('riskfusion.portfolio.optimizer_cvxpy.get_config')
    def test_fallback_on_infeasible(self, mock_config):
        """Test fallback when optimization is infeasible."""
        from riskfusion.portfolio.optimizer_cvxpy import CVXPYOptimizer
        
        mock_config.return_value.params = {
            'optimizer': {'risk_aversion': 1.0, 'cost_bps': 5, 'turnover_cap': 0.001},
            'portfolio': {'max_weight': 0.001, 'long_only': True}  # Impossible constraints
        }
        
        optimizer = CVXPYOptimizer()
        
        alpha = pd.Series([0.05, 0.03], index=['A', 'B'])
        returns = pd.DataFrame(np.random.randn(100, 2) * 0.02, columns=['A', 'B'])
        
        # Should not crash, returns fallback
        weights, info = optimizer.optimize(alpha, returns)
        
        assert len(weights) == 2
        # May be optimal or fallback


class TestIsCvxpyEnabled:
    """Test feature flag detection."""
    
    @patch('riskfusion.portfolio.optimizer_cvxpy.get_config')
    def test_heuristic_mode(self, mock_config):
        from riskfusion.portfolio.optimizer_cvxpy import is_cvxpy_enabled
        mock_config.return_value.params = {'optimizer': {'method': 'heuristic'}}
        assert is_cvxpy_enabled() == False
    
    @patch('riskfusion.portfolio.optimizer_cvxpy.get_config')
    def test_cvxpy_mode(self, mock_config):
        from riskfusion.portfolio.optimizer_cvxpy import is_cvxpy_enabled, CVXPY_AVAILABLE
        mock_config.return_value.params = {'optimizer': {'method': 'cvxpy'}}
        # Result depends on whether cvxpy is installed
        assert is_cvxpy_enabled() == CVXPY_AVAILABLE
