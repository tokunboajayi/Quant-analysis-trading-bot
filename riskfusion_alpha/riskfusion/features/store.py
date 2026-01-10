import pandas as pd
from pathlib import Path
from riskfusion.config import get_config
from riskfusion.utils.hashing import save_parquet, load_parquet
from riskfusion.utils.logging import get_logger

logger = get_logger("feature_store")

class FeatureStore:
    def __init__(self):
        self.config = get_config()
        self.processed_path = Path(self.config.params['paths']['processed'])
    
    def load_raw_prices(self) -> pd.DataFrame:
        path = Path(self.config.params['paths']['raw']) / "prices.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Prices not found at {path}")
        return load_parquet(path)

    def load_features(self, name: str = "features_latest") -> pd.DataFrame:
        path = self.processed_path / f"{name}.parquet"
        if not path.exists():
            return pd.DataFrame()
        return load_parquet(path)
    
    def save_features(self, df: pd.DataFrame, name: str = "features_latest"):
        path = self.processed_path / f"{name}.parquet"
        # Removed partitioning to preserve 'ticker' column in data
        save_parquet(df, path)
        logger.info(f"Saved features to {path}")

    def load_raw_news(self) -> pd.DataFrame:
        path = Path(self.config.params['paths']['raw']) / "news.parquet"
        if not path.exists():
            return pd.DataFrame()
        return load_parquet(path)

    def load_raw_filings(self) -> pd.DataFrame:
        path = Path(self.config.params['paths']['raw']) / "filings.parquet"
        if not path.exists():
            return pd.DataFrame()
        return load_parquet(path)
