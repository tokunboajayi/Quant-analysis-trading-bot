import pandas as pd
import numpy as np

def calculate_metrics(returns: pd.Series):
    """Calculate key performance metrics."""
    metrics = {}
    
    # CAGR
    total_ret = (1 + returns).prod() - 1
    n_years = len(returns) / 252
    metrics['cagr'] = (1 + total_ret) ** (1/n_years) - 1 if n_years > 0 else 0
    
    # Sharpe
    mean_ret = returns.mean() * 252
    vol = returns.std() * np.sqrt(252)
    metrics['sharpe'] = mean_ret / vol if vol > 0 else 0
    metrics['vol'] = vol
    
    # Drawdown
    curve = (1 + returns).cumprod()
    dd = (curve - curve.cummax()) / curve.cummax()
    metrics['max_dd'] = dd.min()
    
    return metrics
