"""
Tests for Meta-Labeler (Step 2)
================================
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock


class TestMetaLabels:
    """Test meta-label creation."""
    
    def test_create_meta_labels_direction_match(self):
        """Test that meta-labels correctly identify direction matches."""
        from riskfusion.labeling.meta_labels import create_meta_labels
        
        # Create test data
        idx = pd.MultiIndex.from_tuples([
            ('2024-01-01', 'AAPL'),
            ('2024-01-01', 'MSFT'),
            ('2024-01-01', 'GOOGL'),
        ])
        
        features = pd.DataFrame({'dummy': [1, 2, 3]}, index=idx)
        
        # Alpha predictions: bullish, bearish, bullish
        alpha = pd.Series([0.05, -0.03, 0.02], index=idx)
        
        # Forward returns: positive, negative, negative (GOOGL is wrong)
        returns = pd.Series([0.02, -0.01, -0.02], index=idx)
        
        result = create_meta_labels(features, alpha, returns)
        
        # AAPL: bullish + positive = GOOD (1)
        # MSFT: bearish + negative = GOOD (1)
        # GOOGL: bullish + negative = BAD (0)
        assert result.loc[('2024-01-01', 'AAPL'), 'meta_label'] == 1
        assert result.loc[('2024-01-01', 'MSFT'), 'meta_label'] == 1
        assert result.loc[('2024-01-01', 'GOOGL'), 'meta_label'] == 0
    
    def test_meta_features_creation(self):
        """Test meta-specific features are created correctly."""
        from riskfusion.labeling.meta_labels import create_meta_features
        
        # Create test features
        dates = pd.date_range('2024-01-01', periods=100)
        df = pd.DataFrame({
            'ret_1d': np.random.randn(100) * 0.02,
            'ret_5d': np.random.randn(100) * 0.05,
            'ret_20d': np.random.randn(100) * 0.10,
            'realized_vol_20d': np.random.uniform(0.1, 0.4, 100),
            'rsi': np.random.uniform(20, 80, 100),
            'xs_mom_20d': np.random.randn(100),
        }, index=dates)
        
        meta_feats = create_meta_features(df)
        
        # Check expected columns exist
        assert 'momentum_consistency' in meta_feats.columns
        assert 'rsi_extreme' in meta_feats.columns
        assert 'consensus_strength' in meta_feats.columns


class TestMetaLabeler:
    """Test MetaLabeler model."""
    
    @patch('riskfusion.models.meta_labeler.get_config')
    def test_predict_returns_probabilities(self, mock_config):
        """Test that predict returns probability values."""
        from riskfusion.models.meta_labeler import MetaLabeler
        
        # Mock config
        mock_config.return_value.params = {
            'meta': {'enabled': True, 'threshold': 0.55},
            'paths': {'models': 'data/models'}
        }
        
        # Create labeler (without trained model, should return 1.0)
        labeler = MetaLabeler()
        
        # Test data
        df = pd.DataFrame({
            'ret_1d': [0.01, 0.02],
            'realized_vol_20d': [0.2, 0.3],
            'rsi': [50, 60],
        })
        
        probs = labeler.predict(df)
        
        # Should return 1.0 for all when no model
        assert len(probs) == 2
        assert all(probs == 1.0)
    
    @patch('riskfusion.models.meta_labeler.get_config')
    def test_apply_to_weights_multiplier(self, mock_config):
        """Test weight adjustment using multiplier mode."""
        from riskfusion.models.meta_labeler import MetaLabeler
        
        mock_config.return_value.params = {
            'meta': {'enabled': True, 'threshold': 0.55, 'apply_as_multiplier': True},
            'paths': {'models': 'data/models'}
        }
        
        labeler = MetaLabeler()
        
        weights = pd.DataFrame({
            'weight': [0.10, 0.08, 0.06]
        }, index=['AAPL', 'MSFT', 'GOOGL'])
        
        meta_probs = pd.Series([0.8, 0.5, 0.9], index=['AAPL', 'MSFT', 'GOOGL'])
        
        result = labeler.apply_to_weights(weights, meta_probs)
        
        # Check weights are scaled by meta_prob
        assert abs(result.loc['AAPL', 'weight'] - 0.10 * 0.8) < 1e-6
        assert abs(result.loc['MSFT', 'weight'] - 0.08 * 0.5) < 1e-6
        assert abs(result.loc['GOOGL', 'weight'] - 0.06 * 0.9) < 1e-6
    
    @patch('riskfusion.models.meta_labeler.get_config')
    def test_apply_to_weights_filter(self, mock_config):
        """Test weight adjustment using filter mode."""
        from riskfusion.models.meta_labeler import MetaLabeler
        
        mock_config.return_value.params = {
            'meta': {'enabled': True, 'threshold': 0.55, 'apply_as_multiplier': False},
            'paths': {'models': 'data/models'}
        }
        
        labeler = MetaLabeler()
        
        weights = pd.DataFrame({
            'weight': [0.10, 0.08, 0.06]
        }, index=['AAPL', 'MSFT', 'GOOGL'])
        
        # MSFT below threshold
        meta_probs = pd.Series([0.8, 0.4, 0.9], index=['AAPL', 'MSFT', 'GOOGL'])
        
        result = labeler.apply_to_weights(weights, meta_probs)
        
        # AAPL and GOOGL should be unchanged, MSFT zeroed
        assert result.loc['AAPL', 'weight'] == 0.10
        assert result.loc['MSFT', 'weight'] == 0.0  # Filtered
        assert result.loc['GOOGL', 'weight'] == 0.06


class TestIsMetaEnabled:
    """Test feature flag detection."""
    
    @patch('riskfusion.models.meta_labeler.get_config')
    def test_flag_off(self, mock_config):
        from riskfusion.models.meta_labeler import is_meta_enabled
        mock_config.return_value.params = {'meta': {'enabled': False}}
        assert is_meta_enabled() == False
    
    @patch('riskfusion.models.meta_labeler.get_config')
    def test_flag_on(self, mock_config):
        from riskfusion.models.meta_labeler import is_meta_enabled
        mock_config.return_value.params = {'meta': {'enabled': True}}
        assert is_meta_enabled() == True
