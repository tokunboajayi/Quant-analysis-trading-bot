import pandas as pd
import numpy as np

def compute_returns(df: pd.DataFrame, horizons=[1, 5, 20, 60, 252]) -> pd.DataFrame:
    """
    Compute percentage returns for various horizons.
    Input df must have 'close' and be indexed by date (or grouped by ticker).
    """
    out = pd.DataFrame(index=df.index)
    for h in horizons:
        out[f'ret_{h}d'] = df['close'].pct_change(h)
    return out

def compute_volatility(df: pd.DataFrame, windows=[5, 20, 60]) -> pd.DataFrame:
    """
    Compute rolling realized volatility (annualized).
    """
    out = pd.DataFrame(index=df.index)
    ret_1d = df['close'].pct_change(1)
    
    for w in windows:
        # Vol = std dev of returns * sqrt(252)
        out[f'realized_vol_{w}d'] = ret_1d.rolling(window=w).std() * np.sqrt(252)
    
    return out

def compute_rsi(df: pd.DataFrame, window=14) -> pd.Series:
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({'macd': macd, 'macd_signal': sig, 'macd_hist': macd - sig}, index=df.index)

def compute_zscores(df: pd.DataFrame, window=60) -> pd.DataFrame:
    """
    Z-Score of price deviation from moving average? Or z-score of returns?
    Let's do Z-Score of price vs 20D MA (Mean Reversion signal)
    """
    ma = df['close'].rolling(window=window).mean()
    std = df['close'].rolling(window=window).std()
    z = (df['close'] - ma) / std
    return pd.DataFrame({f'zscore_{window}d': z}, index=df.index)
