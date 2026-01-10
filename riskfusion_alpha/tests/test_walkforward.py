import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from riskfusion.research.walkforward import WalkForwardRunner

@patch("riskfusion.research.walkforward.AlphaModel")
@patch("riskfusion.research.walkforward.ExperimentTracker")
def test_walkforward_run(mock_tracker_class, mock_model_class):
    # Setup Mocks
    mock_model = mock_model_class.return_value
    # Mock predict to return correct length array
    def predict_side_effect(df_in):
        return np.random.random(len(df_in))
    mock_model.predict.side_effect = predict_side_effect
    
    mock_tracker = mock_tracker_class.return_value
    
    # Create dummy data
    # We need enough dates
    dates = pd.date_range("2020-01-01", periods=100)
    df = pd.DataFrame({
        'date': dates,
        'ticker': ['A'] * 100,
        'f1': np.random.randn(100),
        'target_fwd_5d': np.random.randn(100)
    })
    
    # Init Runner
    # Train 50, Test 10, Step 10
    runner = WalkForwardRunner(df, initial_train_days=50, test_size_days=10, step_size_days=10)
    
    # Run
    res = runner.run()
    
    # Assertions
    # Total dates = 100.
    # Fold 0: Train [0:50], Test [50:60]
    # Fold 1: Train [0:60], Test [60:70]
    # Fold 2: Train [0:70], Test [70:80]
    # Fold 3: Train [0:80], Test [80:90]
    # Fold 4: Train [0:90], Test [90:100]
    # Total 5 folds
    
    assert len(res) >= 4
    assert 'ic' in res.columns
    assert mock_model.train.call_count >= 4
    assert mock_tracker.log_metrics.called
