import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from riskfusion.research.validation_suite import ValidationSuite

@patch("riskfusion.research.validation_suite.AlphaModel")
def test_permutation_test(mock_model_class):
    # Setup
    mock_model = mock_model_class.return_value
    # Predict returns random
    mock_model.predict.side_effect = lambda df: np.random.randn(len(df))
    
    df = pd.DataFrame({
        'date': ['2020-01-01']*10,
        'ticker': [f't{i}' for i in range(10)],
        'f1': np.random.randn(10),
        'target_fwd_5d': np.random.randn(10)
    })
    
    res = ValidationSuite.permutation_test(df, n_permutes=2)
    
    assert len(res) == 3 # 1 true + 2 permuted
    assert res.iloc[0]['type'] == 'true'
    assert res.iloc[1]['type'] == 'permuted'
