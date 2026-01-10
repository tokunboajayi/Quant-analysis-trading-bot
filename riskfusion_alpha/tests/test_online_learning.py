"""
Tests for Online Learning (Step 7)
===================================
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json
import tempfile
from pathlib import Path


class TestOnlineLearningManager:
    """Test online learning manager."""
    
    @patch('riskfusion.research.online_learning.get_config')
    def test_should_retrain_on_drift(self, mock_config):
        """Test that high PSI drift triggers retrain."""
        from riskfusion.research.online_learning import OnlineLearningManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config.return_value.params = {
                'online_learning': {
                    'drift_psi_threshold': 0.25,
                    'var_breach_threshold': 0.10,
                    'min_retrain_interval_days': 7
                },
                'paths': {'outputs': tmpdir}
            }
            
            manager = OnlineLearningManager()
            
            # High PSI
            drift_metrics = {'feature_1': 0.30, 'feature_2': 0.10}
            should, reason = manager.should_retrain(drift_metrics, var_breach_rate=0.05)
            
            assert should == True
            assert 'DRIFT_PSI_EXCEEDED' in reason
    
    @patch('riskfusion.research.online_learning.get_config')
    def test_should_not_retrain_within_interval(self, mock_config):
        """Test that retraining is blocked within minimum interval."""
        from riskfusion.research.online_learning import OnlineLearningManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config.return_value.params = {
                'online_learning': {
                    'drift_psi_threshold': 0.25,
                    'var_breach_threshold': 0.10,
                    'min_retrain_interval_days': 7
                },
                'paths': {'outputs': tmpdir}
            }
            
            manager = OnlineLearningManager()
            
            # Simulate recent retrain
            manager.state['last_retrain_date'] = (datetime.now() - timedelta(days=2)).isoformat()
            
            # Even with high drift, should be blocked
            drift_metrics = {'feature_1': 0.50}
            should, reason = manager.should_retrain(drift_metrics, var_breach_rate=0.05)
            
            assert should == False
            assert 'MIN_INTERVAL_NOT_MET' in reason
    
    @patch('riskfusion.research.online_learning.get_config')
    def test_no_retrain_when_stable(self, mock_config):
        """Test that no retrain when metrics are stable."""
        from riskfusion.research.online_learning import OnlineLearningManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config.return_value.params = {
                'online_learning': {
                    'drift_psi_threshold': 0.25,
                    'var_breach_threshold': 0.10,
                    'min_retrain_interval_days': 7
                },
                'paths': {'outputs': tmpdir}
            }
            
            manager = OnlineLearningManager()
            
            # Low PSI, low VaR breach
            drift_metrics = {'feature_1': 0.05, 'feature_2': 0.08}
            should, reason = manager.should_retrain(drift_metrics, var_breach_rate=0.04)
            
            assert should == False
            assert reason == 'NO_TRIGGER'


class TestAntiRetrainLoop:
    """Test anti-loop protection."""
    
    def test_blocks_excessive_retrains(self):
        """Test that excessive retrains are blocked."""
        from riskfusion.research.online_learning import AntiRetrainLoop
        
        loop = AntiRetrainLoop(max_retrains_per_period=3, period_days=14)
        
        # First 3 should be allowed
        assert loop.can_retrain() == True
        loop.record_retrain()
        
        assert loop.can_retrain() == True
        loop.record_retrain()
        
        assert loop.can_retrain() == True
        loop.record_retrain()
        
        # 4th should be blocked
        assert loop.can_retrain() == False


class TestIsOnlineLearningEnabled:
    """Test feature flag detection."""
    
    @patch('riskfusion.research.online_learning.get_config')
    def test_flag_off(self, mock_config):
        from riskfusion.research.online_learning import is_online_learning_enabled
        mock_config.return_value.params = {'online_learning': {'enabled': False}}
        assert is_online_learning_enabled() == False
    
    @patch('riskfusion.research.online_learning.get_config')
    def test_flag_on(self, mock_config):
        from riskfusion.research.online_learning import is_online_learning_enabled
        mock_config.return_value.params = {'online_learning': {'enabled': True}}
        assert is_online_learning_enabled() == True
