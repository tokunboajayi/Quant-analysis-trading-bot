import pytest
import pandas as pd
import numpy as np
from riskfusion.utils.validation import DataValidator, ValidationError

def test_validate_prices_success():
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
        'ticker': ['AAPL', 'AAPL'],
        'close': [150.0, 152.0],
        'volume': [1000, 1200],
        'high': [155, 155],
        'low': [149, 150]
    })
    # Should not raise
    DataValidator.validate_prices(df)

def test_validate_prices_negative():
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01']),
        'ticker': ['AAPL'],
        'close': [-10.0], # Error
        'volume': [1000],
        'high': [155],
        'low': [149]
    })
    with pytest.raises(ValidationError):
        DataValidator.validate_prices(df)

def test_validate_features_missing():
    df = pd.DataFrame({'f1': [1,2,3]})
    with pytest.raises(ValidationError):
        DataValidator.validate_features(df, model_features=['f1', 'f2'])

def test_validate_weights_sum():
    df = pd.DataFrame({'weight': [0.6, 0.6], 'ticker': ['A', 'B']})
    with pytest.raises(ValidationError):
        DataValidator.validate_weights(df)
