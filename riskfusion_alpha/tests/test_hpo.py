import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from riskfusion.research.hpo import run_hpo, objective

@patch("riskfusion.research.hpo.FeatureStore")
@patch("riskfusion.research.hpo.AlphaModel")
def test_hpo_flow(mock_model_cls, mock_store_cls):
    # Setup Mock Data
    df = pd.DataFrame({
        'ticker': ['AAPL']*50 + ['GOOG']*50,
        'date': pd.to_datetime(['2021-01-01']*100), # Simple date
        'feat1': np.random.randn(100),
        'target_fwd_5d': np.random.randn(100)
    })
    # Dates need to be sortable and split
    dates = pd.date_range('2020-01-01', periods=100)
    df = pd.DataFrame({
        'ticker': ['AAPL']*100,
        'date': dates,
        'feat1': np.random.randn(100),
        'target_fwd_5d': np.random.randn(100),
        'close': np.random.randn(100) # needed?
    })
    
    # Mock Store
    mock_store = mock_store_cls.return_value
    mock_store.load_features.return_value = df
    
    # Mock Model
    mock_model = mock_model_cls.return_value
    mock_model.predict.return_value = np.random.randn(20) # validation split is 20%
    
    # Run HPO (1 trial for speed)
    best_params = run_hpo(n_trials=1)
    
    assert isinstance(best_params, dict)
    assert 'learning_rate' in best_params
    
    # Check calls
    mock_store.load_features.assert_called()
    mock_model.train.assert_called()
    mock_model.predict.assert_called()
