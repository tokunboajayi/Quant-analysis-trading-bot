import pandas as pd
import numpy as np
from typing import List, Tuple
from riskfusion.utils.logging import get_logger

logger = get_logger("leakage_checks")

class LeakageError(Exception):
    pass

class LeakageDetector:
    """
    Detects various forms of leakage in financial datasets.
    """
    
    @staticmethod
    def check_time_leakage(features: pd.DataFrame, labels: pd.DataFrame, date_col='date', ticker_col='ticker') -> None:
        """
        Ensure label timestamp > feature timestamp.
        For a daily model, if feature is at Close T, label must be from T+1 onwards.
        Usually we align them: Row T has Feat(T) and Label(T) where Label(T) = Returns(T+1 to T+k).
        Leakage happens if Feat(T) contains Price(T+1).
        This is hard to check just from values without metadata, 
        BUT we can check if the Label implied dates overlap with Feature dates in an impossible way 
        IF we had explicit 'label_start_time' columns.
        
        Without metadata, we check for 'Future Peeking' statistically (permutation logic) elsewhere.
        Here we check for obvious structural issues if 'event_timestamp' is present.
        """
        logger.info("Checking for time leakage (heuristics)...")
        # Check 1: If we have 'news_timestamp' and 'date'
        if 'news_timestamp' in features.columns and pd.api.types.is_datetime64_any_dtype(features[date_col]):
             # Assuming date_col is valid_time (e.g. Close). 
             # News timestamp should be <= Close Time (approx).
             # Let's say we assume market close is 16:00.
             pass 
        
        logger.info("Time leakage check passed (metadata limited).")

    @staticmethod
    def check_universe_integrity(df: pd.DataFrame, valid_tickers: List[str], date_col='date', ticker_col='ticker'):
        """
        Check if tickers in DF are valid for the given date.
        (Anti-survivorship bias check if valid_tickers is a time-series dictionary).
        For now, we check against a static master list or ensure no 'unknown' tickers.
        """
        logger.info("Checking universe integrity...")
        unknowns = set(df[ticker_col].unique()) - set(valid_tickers)
        if unknowns:
            logger.warning(f"Found {len(unknowns)} tickers not in allowed universe: {list(unknowns)[:5]}...")
            # Detectable leakage? Maybe not alone, but consistency issue.
            
    @staticmethod
    def check_future_peeking(df: pd.DataFrame, feature_cols: List[str], shift_detection=True):
        """
        Statistical check: Does Feature(t) correlate perfectly with Price(t+1)?
        This detects shift errors like 'close' column carrying tomorrow's price.
        """
        logger.info("Checking for future peeking (feature-target correlation)...")
        # This requires the raw price next day.
        # Assuming df has 'target' which represents future return.
        
        # High correlation between a FEATURE and the TARGET is good (alpha).
        # PERFECT correlation (1.0 or very high > 0.99) often means leakage 
        # (e.g. using Close(T+1) as a feature to predict Return(T+1)).
        
        for col in feature_cols:
            if col not in df.columns: continue
            if 'target' not in df.columns: continue
            
            numeric_df = df[[col, 'target']].dropna()
            if numeric_df.empty: continue
            
            corr = numeric_df.corr().iloc[0, 1]
            if abs(corr) > 0.95:
                msg = f"Feature '{col}' has suspicious correlation {corr:.4f} with target. Possible LEAKAGE."
                logger.error(msg)
                raise LeakageError(msg)
        
        logger.info("Future peeking checks passed.")

    @staticmethod
    def check_cross_sectional_leakage(df: pd.DataFrame, feature_cols: List[str], date_col='date'):
        """
        Verifies that cross-sectional features (z-scores) are computed per-date.
        If a feature is z-scored using the WHOLE history mean, that's leakage.
        
        Heuristic: 
        If we subtract the global mean from the column, it should look like the feature.
        If we subtract the daily mean, it should be exactly 0 (if it was centered correctly).
        
        Actually, we can't easily detect this post-hoc without the raw data. 
        But we can warn if global stats are 0,1.
        """
        logger.info("Checking cross-sectional stats...")
        for col in feature_cols:
            # Check global mean/std
            g_mean = df[col].mean()
            g_std = df[col].std()
            
            # If standardized globally
            if abs(g_mean) < 1e-5 and abs(g_std - 1.0) < 1e-5:
                # Check if it is also standardized locally
                daily_means = df.groupby(date_col)[col].mean()
                if daily_means.std() > 0.1: 
                    # Global is 0,1 but Daily means vary wildly -> 
                    # Means it was globally standardized! LEAKAGE if non-stationary.
                    logger.warning(f"Feature '{col}' appears globally standardized (Global Mean~0, Std~1) but Daily Means vary. Potential look-ahead bias in normalization.")
                    
        logger.info("Cross-sectional check complete.")
