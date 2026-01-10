"""
Meta Labels - Step 2 of Crazy Quant Ladder
==========================================
Labels whether prior alpha predictions were "good" (profitable).
Used to train a meta-model that filters trades.
"""
import pandas as pd
import numpy as np
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("meta_labels")


def create_meta_labels(
    features_df: pd.DataFrame,
    alpha_predictions: pd.Series,
    forward_returns: pd.Series,
    threshold: float = 0.0
) -> pd.DataFrame:
    """
    Create meta-labels indicating whether acting on alpha signal was profitable.
    
    Args:
        features_df: Features DataFrame with date/ticker index
        alpha_predictions: Alpha model predictions (higher = more bullish)
        forward_returns: Realized forward returns (e.g., 5D)
        threshold: Minimum return to consider "good" (default 0)
    
    Returns:
        DataFrame with meta_label column (1 = good trade, 0 = bad trade)
    """
    logger.info("Creating meta-labels...")
    
    # Align indices
    common_idx = features_df.index.intersection(alpha_predictions.index).intersection(forward_returns.index)
    
    alpha = alpha_predictions.loc[common_idx]
    returns = forward_returns.loc[common_idx]
    
    # Meta-label logic:
    # If alpha > 0 (bullish) AND return > threshold -> GOOD (1)
    # If alpha <= 0 (bearish/neutral) AND return <= threshold -> GOOD (1)
    # Otherwise -> BAD (0)
    
    # Simplified: Did we correctly predict direction?
    alpha_sign = np.sign(alpha)
    return_sign = np.sign(returns - threshold)
    
    # Good trade = alpha direction matches return direction
    meta_label = (alpha_sign == return_sign).astype(int)
    
    # Alternative: Only label LONG trades (if alpha > 0)
    # meta_label = ((alpha > 0) & (returns > threshold)).astype(int)
    
    result = pd.DataFrame({
        'alpha_pred': alpha,
        'fwd_return': returns,
        'meta_label': meta_label
    }, index=common_idx)
    
    # Stats
    hit_rate = meta_label.mean()
    logger.info(f"Meta-label stats: {len(result)} samples, hit rate: {hit_rate:.2%}")
    
    return result


def create_meta_features(features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create additional features specifically for meta-model.
    
    These features capture prediction uncertainty and market conditions
    that might indicate whether to trust the alpha signal.
    
    Args:
        features_df: Base features DataFrame
    
    Returns:
        DataFrame with meta-specific features
    """
    meta_features = pd.DataFrame(index=features_df.index)
    
    # 1. Volatility regime (high vol = less predictable)
    if 'realized_vol_20d' in features_df.columns:
        vol = features_df['realized_vol_20d']
        meta_features['vol_regime'] = pd.qcut(vol, q=5, labels=False, duplicates='drop')
        meta_features['vol_zscore'] = (vol - vol.rolling(60).mean()) / vol.rolling(60).std()
    
    # 2. Momentum consistency (mixed signals = uncertain)
    if all(c in features_df.columns for c in ['ret_1d', 'ret_5d', 'ret_20d']):
        signs = np.sign(features_df[['ret_1d', 'ret_5d', 'ret_20d']])
        meta_features['momentum_consistency'] = signs.sum(axis=1).abs() / 3
    
    # 3. RSI extremes (overbought/oversold = potential reversal)
    if 'rsi' in features_df.columns:
        rsi = features_df['rsi']
        meta_features['rsi_extreme'] = ((rsi > 70) | (rsi < 30)).astype(int)
    
    # 4. Cross-sectional rank (consensus vs contrarian)
    if 'xs_mom_20d' in features_df.columns:
        meta_features['consensus_strength'] = features_df['xs_mom_20d'].abs()
    
    return meta_features.fillna(0)


def is_meta_enabled() -> bool:
    """Check if meta-labeler is enabled in config."""
    config = get_config()
    return config.params.get('meta', {}).get('enabled', False)
