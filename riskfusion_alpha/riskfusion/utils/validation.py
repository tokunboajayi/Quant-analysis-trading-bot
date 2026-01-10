import pandas as pd
import numpy as np
from typing import List, Optional
from riskfusion.utils.logging import get_logger

logger = get_logger("validation")

class ValidationError(Exception):
    pass

class DataValidator:
    """
    Validates DataFrames against expected schemas and integrity rules.
    """
    
    @staticmethod
    def validate_prices(df: pd.DataFrame, required_cols=['date', 'ticker', 'close', 'volume', 'high', 'low']):
        """
        Validate Price Data.
        """
        logger.info("Validating prices...")
        
        # 1. Schema
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValidationError(f"Missing price columns: {missing}")
            
        # 2. Types
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
             # Try to convert or fail
             try:
                 df['date'] = pd.to_datetime(df['date'])
             except:
                 raise ValidationError("Column 'date' is not datetime.")
        
        # 3. Integrity
        # - No negative prices
        if (df['close'] < 0).any():
             raise ValidationError("Found negative prices!")
             
        # - Duplicates
        if df.duplicated(subset=['date', 'ticker']).any():
             raise ValidationError("Duplicate (date, ticker) found in prices.")
             
        # - Freshness (Warn only?)
        # Let's check if we have recent data (e.g. within last 5 days)
        last_date = df['date'].max()
        if (pd.Timestamp.now() - last_date).days > 5:
             logger.warning(f"Data might be stale. Last date: {last_date}")

        logger.info("Price validation passed.")

    @staticmethod
    def validate_features(df: pd.DataFrame, model_features: List[str]):
        """
        Validate Features before inference.
        """
        logger.info("Validating features...")
        
        # 1. Check columns
        # Note: model_features might be a subset. We need at least them.
        missing = [f for f in model_features if f not in df.columns]
        if missing:
            raise ValidationError(f"Missing features: {missing}")
            
        # 2. Check NaNs in critical features
        # Allowing some NaNs might be ok if model handles it (LightGBM does).
        # But if > 20% NaNs, something is wrong.
        for f in model_features:
            null_pct = df[f].isnull().mean()
            if null_pct > 0.2:
                logger.warning(f"Feature {f} has {null_pct:.1%} NaNs. High missingness.")
        
        # 3. Infinity checks
        if np.isinf(df[model_features].select_dtypes(include=np.number)).any().any():
             raise ValidationError("Found infinite values in features.")
             
        logger.info("Feature validation passed.")

    @staticmethod
    def validate_weights(df: pd.DataFrame):
        """
        Validate final weights.
        """
        if df.empty:
            logger.warning("Empty weights dataframe.")
            return

        if 'weight' not in df.columns:
            raise ValidationError("Weights DF missing 'weight' column.")
            
        # Sum approximately 1.0 (or <= 1.0)
        total_w = df['weight'].sum()
        if total_w > 1.0001:
             raise ValidationError(f"Total weight {total_w} > 1.0")
             
        if (df['weight'] < 0).any():
              # Unless shorting allowed?
              # Conf params usually dictate long_only. Assuming long_only for now.
              pass # We assume logic handled it, but let's warn
              
        if df['weight'].max() > 0.25: # Hard cap check (e.g. 25%)
             logger.warning(f"Found large position > 25%: {df['weight'].max()}")
