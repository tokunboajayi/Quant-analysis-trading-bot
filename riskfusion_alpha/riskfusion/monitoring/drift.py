import pandas as pd
import numpy as np
from riskfusion.utils.logging import get_logger

logger = get_logger("drift")

def calculate_psi(expected, actual, buckettype='bins', buckets=10, axis=0):
    """
    Calculate Population Stability Index (PSI).
    expected: series of baseline values
    actual: series of new values
    """
    def scale_range (input, min, max):
        input += -(np.min(input))
        input /= np.max(input) / (max - min)
        input += min
        return input

    breakpoints = np.arange(0, buckets + 1) / (buckets) * 100

    if buckettype == 'bins':
        breakpoints = scale_range(breakpoints, np.min(expected), np.max(expected))
    elif buckettype == 'quantiles':
        breakpoints = np.stack([np.percentile(expected, b) for b in breakpoints])

    expected_percents = np.histogram(expected, breakpoints)[0] / len(expected)
    actual_percents = np.histogram(actual, breakpoints)[0] / len(actual)

    def sub_psi(e_perc, a_perc):
        if a_perc == 0: a_perc = 0.0001
        if e_perc == 0: e_perc = 0.0001
        return (e_perc - a_perc) * np.log(e_perc / a_perc)

    psi_value = np.sum(sub_psi(expected_percents[i], actual_percents[i]) for i in range(0, len(expected_percents)))
    return psi_value

def check_feature_drift(train_df: pd.DataFrame, current_df: pd.DataFrame, features: list):
    """
    Check PSI for features.
    """
    drift_report = {}
    for f in features:
        if f not in train_df.columns or f not in current_df.columns:
            continue
            
        # Ensure numeric
        if not pd.api.types.is_numeric_dtype(train_df[f]):
            continue
            
        psi = calculate_psi(train_df[f].dropna().values, current_df[f].dropna().values, buckets=10)
        drift_report[f] = psi
        
        if psi > 0.2:
            logger.warning(f"Drift detected in {f}: PSI={psi:.4f}")
            
    return drift_report
