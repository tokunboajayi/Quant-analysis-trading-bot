"""
Tests for Multi-Task Event Risk (Step 5)
=========================================
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock


class TestMultiTaskEventRisk:
    """Test multi-task event risk model."""
    
    @patch('riskfusion.models.event_risk_multitask.get_config')
    def test_predict_returns_all_columns(self, mock_config):
        """Test that predict returns all required columns."""
        from riskfusion.models.event_risk_multitask import MultiTaskEventRiskModel
        
        mock_config.return_value.params = {
            'paths': {'models': 'data/models'},
            'event': {'multitask': True}
        }
        
        model = MultiTaskEventRiskModel()
        
        # Test events (no trained model, should return defaults)
        events = pd.DataFrame({
            'title': ['Stock rises on earnings', 'Company announces layoffs'],
            'description': ['Beat expectations', 'Restructuring plan']
        })
        
        result = model.predict(events)
        
        assert 'event_risk_prob' in result.columns
        assert 'event_neg_prob' in result.columns
        assert 'event_mag_bucket' in result.columns
        assert 'event_combined_risk' in result.columns
    
    def test_create_multitask_labels(self):
        """Test label creation for multi-task training."""
        from riskfusion.models.event_risk_multitask import create_multitask_labels
        
        events = pd.DataFrame({
            'title': ['Event A', 'Event B', 'Event C', 'Event D'],
            'description': ['Desc A', 'Desc B', 'Desc C', 'Desc D']
        }, index=[0, 1, 2, 3])
        
        # Returns: small neg, large pos, medium neg, small pos
        returns = pd.Series([-0.01, 0.08, -0.03, 0.005], index=[0, 1, 2, 3])
        
        result = create_multitask_labels(events, returns)
        
        # Event A: small negative
        assert result.loc[0, 'high_impact'] == 0
        assert result.loc[0, 'negative'] == 1
        assert result.loc[0, 'magnitude_bucket'] == 0
        
        # Event B: large positive
        assert result.loc[1, 'high_impact'] == 1
        assert result.loc[1, 'negative'] == 0
        assert result.loc[1, 'magnitude_bucket'] == 2
        
        # Event C: medium negative
        assert result.loc[2, 'high_impact'] == 1
        assert result.loc[2, 'negative'] == 1
        assert result.loc[2, 'magnitude_bucket'] == 1


class TestMultiTaskOverlay:
    """Test overlay behavior with multi-task outputs."""
    
    def test_combined_risk_calculation(self):
        """Test that combined risk = P(impact) * P(negative)."""
        # Simulate predictions
        predictions = pd.DataFrame({
            'event_risk_prob': [0.8, 0.3, 0.9],
            'event_neg_prob': [0.7, 0.5, 0.2],
        })
        
        expected_combined = predictions['event_risk_prob'] * predictions['event_neg_prob']
        
        # Event 0: High risk, likely negative -> high combined
        assert abs(expected_combined.iloc[0] - 0.56) < 0.01
        
        # Event 1: Low risk -> low combined
        assert abs(expected_combined.iloc[1] - 0.15) < 0.01
        
        # Event 2: High risk but likely positive -> low combined
        assert abs(expected_combined.iloc[2] - 0.18) < 0.01


class TestIsMultitaskEnabled:
    """Test feature flag detection."""
    
    @patch('riskfusion.models.event_risk_multitask.get_config')
    def test_flag_off(self, mock_config):
        from riskfusion.models.event_risk_multitask import is_multitask_enabled
        mock_config.return_value.params = {'event': {'multitask': False}}
        assert is_multitask_enabled() == False
    
    @patch('riskfusion.models.event_risk_multitask.get_config')
    def test_flag_on(self, mock_config):
        from riskfusion.models.event_risk_multitask import is_multitask_enabled
        mock_config.return_value.params = {'event': {'multitask': True}}
        assert is_multitask_enabled() == True
