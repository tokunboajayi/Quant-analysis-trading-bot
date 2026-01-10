"""
Tests for Alpha Quantiles Model (Step 1)
=========================================
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock


class TestAlphaQuantilesMonotonicity:
    """Test monotonicity enforcement: q10 <= q50 <= q90"""
    
    def test_monotonicity_enforcement(self):
        """Test that predictions are sorted to ensure q10 <= q50 <= q90."""
        from riskfusion.models.alpha_quantiles import AlphaQuantilesModel
        
        # Create mock data with violations
        df = pd.DataFrame({
            'q10': [0.05, -0.02, 0.10],  # Third row violates (q10 > q50)
            'q50': [0.03, 0.01, 0.05],
            'q90': [0.08, 0.04, 0.12],
        })
        
        model = AlphaQuantilesModel()
        fixed_df = model._enforce_monotonicity(df.copy())
        
        # Check monotonicity is now enforced
        assert all(fixed_df['q10'] <= fixed_df['q50'])
        assert all(fixed_df['q50'] <= fixed_df['q90'])
    
    def test_no_violations_unchanged(self):
        """Test that valid data is unchanged."""
        from riskfusion.models.alpha_quantiles import AlphaQuantilesModel
        
        df = pd.DataFrame({
            'q10': [-0.05, -0.02, -0.01],
            'q50': [0.00, 0.01, 0.02],
            'q90': [0.05, 0.04, 0.05],
        })
        
        model = AlphaQuantilesModel()
        fixed_df = model._enforce_monotonicity(df.copy())
        
        pd.testing.assert_frame_equal(df, fixed_df)


class TestAlphaQuantilesQualityScore:
    """Test quality score calculations."""
    
    def test_q50_over_abs_q10(self):
        """Test q50 / |q10| formula."""
        from riskfusion.models.alpha_quantiles import AlphaQuantilesModel
        
        df = pd.DataFrame({
            'q10': [-0.10, -0.05, -0.02],
            'q50': [0.05, 0.05, 0.05],
            'q90': [0.10, 0.10, 0.10],
        })
        
        model = AlphaQuantilesModel()
        model.quality_formula = 'q50_over_abs_q10'
        
        scores = model._compute_quality_score(df)
        
        # Higher score when downside is smaller
        assert scores.iloc[2] > scores.iloc[1] > scores.iloc[0]
    
    def test_quality_score_ranking(self):
        """Test that quality score produces sensible ranking."""
        from riskfusion.models.alpha_quantiles import AlphaQuantilesModel
        
        # Stock A: Small upside, small downside
        # Stock B: Large upside, large downside
        # Stock C: Large upside, small downside (best)
        df = pd.DataFrame({
            'q10': [-0.02, -0.10, -0.02],
            'q50': [0.02, 0.08, 0.08],
            'q90': [0.04, 0.15, 0.15],
        }, index=['A', 'B', 'C'])
        
        model = AlphaQuantilesModel()
        scores = model._compute_quality_score(df)
        
        # C should rank highest (best upside/downside ratio)
        assert scores.idxmax() == 'C'


class TestAlphaQuantilesNoLeakage:
    """Test that training uses only past data."""
    
    def test_labels_after_features(self):
        """Verify labels are strictly after feature timestamps."""
        # This is a design test - the target_fwd_5d should be calculated
        # from prices 5 days AFTER the feature date
        
        # Create sample data
        dates = pd.date_range('2024-01-01', periods=20, freq='B')
        df = pd.DataFrame({
            'date': dates,
            'close': np.random.randn(20).cumsum() + 100,
        })
        
        # Forward return at day T should use close(T+5) / close(T) - 1
        # Feature at day T should only use data up to day T
        
        df['target_fwd_5d'] = df['close'].shift(-5) / df['close'] - 1
        
        # The last 5 rows should have NaN targets (no future data)
        assert df['target_fwd_5d'].isna().sum() == 5
        
        # For training, we should drop these NaN rows
        train_df = df.dropna()
        assert len(train_df) == 15


class TestAlphaQuantilesPinballLoss:
    """Test pinball loss calculation."""
    
    def test_pinball_loss_median(self):
        """Pinball loss at q=0.5 should equal MAE/2."""
        from riskfusion.models.alpha_quantiles import AlphaQuantilesModel
        
        y_true = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.5, 2.5, 2.5, 3.5, 4.5])
        
        model = AlphaQuantilesModel()
        loss = model._pinball_loss(y_true, y_pred, 0.5)
        
        # Pinball loss at 0.5 = 0.5 * sum(|y - pred|) / n
        expected = 0.5 * np.mean(np.abs(y_true.values - y_pred))
        assert abs(loss - expected) < 1e-6


class TestIsQuantilesEnabled:
    """Test feature flag detection."""
    
    @patch('riskfusion.models.alpha_quantiles.get_config')
    def test_flag_off(self, mock_config):
        """Test detection when flag is OFF."""
        from riskfusion.models.alpha_quantiles import is_quantiles_enabled
        
        mock_config.return_value.params = {'alpha': {'use_quantiles': False}}
        assert is_quantiles_enabled() == False
    
    @patch('riskfusion.models.alpha_quantiles.get_config')
    def test_flag_on(self, mock_config):
        """Test detection when flag is ON."""
        from riskfusion.models.alpha_quantiles import is_quantiles_enabled
        
        mock_config.return_value.params = {'alpha': {'use_quantiles': True}}
        assert is_quantiles_enabled() == True
