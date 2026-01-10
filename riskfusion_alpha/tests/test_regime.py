"""
Tests for Regime Model and Strategy Selector (Step 6)
======================================================
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock


class TestRegimeModel:
    """Test regime detection."""
    
    @patch('riskfusion.models.regime_model.get_config')
    def test_detect_calm_regime(self, mock_config):
        """Test detection of CALM regime (low vol)."""
        from riskfusion.models.regime_model import RegimeModel
        
        mock_config.return_value.params = {
            'regime': {'vol_threshold_volatile': 0.20, 'vol_threshold_stressed': 0.35}
        }
        
        model = RegimeModel()
        
        # Create low-volatility prices
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=60)
        prices = pd.DataFrame({
            'SPY': 100 + np.cumsum(np.random.randn(60) * 0.002),  # Very low vol
            'QQQ': 200 + np.cumsum(np.random.randn(60) * 0.003),
        }, index=dates)
        
        regime, info = model.detect_regime(prices)
        
        assert regime == model.CALM
        assert info['regime'] == 'CALM'
    
    @patch('riskfusion.models.regime_model.get_config')
    def test_detect_volatile_regime(self, mock_config):
        """Test detection of VOLATILE regime."""
        from riskfusion.models.regime_model import RegimeModel
        
        mock_config.return_value.params = {
            'regime': {'vol_threshold_volatile': 0.20, 'vol_threshold_stressed': 0.35}
        }
        
        model = RegimeModel()
        
        # Create high-volatility prices with explicit high daily moves
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=60)
        # 3% daily moves = ~47% annualized vol
        daily_returns = np.random.randn(60) * 0.03
        prices = pd.DataFrame({
            'SPY': 100 * np.exp(np.cumsum(daily_returns)),
            'QQQ': 200 * np.exp(np.cumsum(daily_returns * 1.2)),
        }, index=dates)
        
        regime, info = model.detect_regime(prices)
        
        # With 3% daily moves, should be VOLATILE or STRESSED
        assert regime in [model.VOLATILE, model.STRESSED]
        assert info['realized_vol'] > 0.20  # Should exceed volatile threshold


class TestStrategySelector:
    """Test strategy parameter selection."""
    
    @patch('riskfusion.portfolio.strategy_selector.is_regime_enabled')
    @patch('riskfusion.portfolio.strategy_selector.get_config')
    def test_params_change_with_regime(self, mock_config, mock_enabled):
        """Test that parameters change based on regime."""
        from riskfusion.portfolio.strategy_selector import StrategySelector
        from riskfusion.models.regime_model import RegimeModel
        
        mock_enabled.return_value = True
        mock_config.return_value.params = {
            'portfolio': {'target_vol_ann': 0.10, 'max_weight': 0.10},
            'optimizer': {'risk_aversion': 1.0},
            'regime': {'vol_threshold_volatile': 0.20, 'vol_threshold_stressed': 0.35}
        }
        
        selector = StrategySelector()
        
        # CALM params
        calm_params = selector.REGIME_PARAMS[RegimeModel.CALM]
        assert calm_params['gross_exposure'] == 1.0
        assert calm_params['risk_aversion'] == 1.0
        
        # STRESSED params
        stressed_params = selector.REGIME_PARAMS[RegimeModel.STRESSED]
        assert stressed_params['gross_exposure'] == 0.4
        assert stressed_params['risk_aversion'] == 4.0
    
    @patch('riskfusion.portfolio.strategy_selector.is_regime_enabled')
    @patch('riskfusion.portfolio.strategy_selector.get_config')
    def test_apply_to_weights_scales(self, mock_config, mock_enabled):
        """Test that weights are scaled by gross exposure."""
        from riskfusion.portfolio.strategy_selector import StrategySelector
        
        mock_enabled.return_value = True
        mock_config.return_value.params = {}
        
        selector = StrategySelector()
        
        weights = pd.DataFrame({
            'weight': [0.10, 0.08, 0.06]
        }, index=['A', 'B', 'C'])
        
        # Apply stressed regime params (40% gross)
        params = {'gross_exposure': 0.4, 'max_position': 0.05}
        result = selector.apply_to_weights(weights, params)
        
        # Weights should be scaled down
        assert result['weight'].sum() < weights['weight'].sum()


class TestIsRegimeEnabled:
    """Test feature flag detection."""
    
    @patch('riskfusion.models.regime_model.get_config')
    def test_flag_off(self, mock_config):
        from riskfusion.models.regime_model import is_regime_enabled
        mock_config.return_value.params = {'regime': {'enabled': False}}
        assert is_regime_enabled() == False
    
    @patch('riskfusion.models.regime_model.get_config')
    def test_flag_on(self, mock_config):
        from riskfusion.models.regime_model import is_regime_enabled
        mock_config.return_value.params = {'regime': {'enabled': True}}
        assert is_regime_enabled() == True
