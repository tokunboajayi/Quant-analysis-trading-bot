import pytest
import pandas as pd
import numpy as np
from riskfusion.monitoring.drift import check_feature_drift, calculate_psi

def test_calculate_psi_no_drift():
    # Identical distributions -> PSI ~ 0
    a = np.random.normal(0, 1, 1000)
    b = np.random.normal(0, 1, 1000)
    psi = calculate_psi(a, b)
    assert psi < 0.1

def test_calculate_psi_drift():
    # Shifted -> High PSI
    a = np.random.normal(0, 1, 1000)
    b = np.random.normal(1, 1, 1000) # shifted mean
    psi = calculate_psi(a, b)
    assert psi > 0.1

def test_check_feature_drift():
    df_train = pd.DataFrame({'f1': np.random.normal(0, 1, 100)})
    df_curr = pd.DataFrame({'f1': np.random.normal(2, 1, 100)}) # drifting
    
    report = check_feature_drift(df_train, df_curr, ['f1'])
    assert 'f1' in report
    assert report['f1'] > 0.2
