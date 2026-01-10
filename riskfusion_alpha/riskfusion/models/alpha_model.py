import lightgbm as lgb
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("alpha_model")

class AlphaModel:
    def __init__(self, **kwargs):
        self.config = get_config()
        self.model = None
        self.params = kwargs # Store hyperparameters
        self.features = [
            'ret_1d', 'ret_5d', 'ret_20d', 
            'realized_vol_20d', 'rsi', 
            'xs_mom_20d', 'xs_vol_20d'
            # 'news_count' removed - optional feature, API may fail
        ]
        self.target = 'target_fwd_5d'

    def train(self, df: pd.DataFrame):
        """
        Train LGBM Ranker/Regressor.
        For MVP, we use Regressor on the forward return.
        """
        logger.info("Training Alpha Model...")
        
        # Filter NaNs
        train_df = df.dropna(subset=self.features + [self.target])
        
        # Time-based split for validation (last 20%)
        dates = train_df['date'].unique()
        split_idx = int(len(dates) * 0.8)
        split_date = sorted(dates)[split_idx]
        
        train_set = train_df[train_df['date'] <= split_date]
        val_set = train_df[train_df['date'] > split_date]
        
        X_train = train_set[self.features]
        y_train = train_set[self.target]
        
        X_val = val_set[self.features]
        y_val = val_set[self.target]
        
        dtrain = lgb.Dataset(X_train, label=y_train)
        dval = lgb.Dataset(X_val, label=y_val)
        
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'learning_rate': 0.05,
            'num_leaves': 31,
            'verbose': -1,
            'seed': 42,
            'deterministic': True
        }
        
        # Override
        if self.params:
            params.update(self.params)
        
        self.model = lgb.train(
            params, 
            dtrain, 
            num_boost_round=1000, 
            valid_sets=[dval],
            callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(100)]
        )
        
        self.save()

    def predict(self, df: pd.DataFrame) -> pd.Series:
        if not self.model:
            self.load()
        
        # Check features
        missing = [f for f in self.features if f not in df.columns]
        if missing:
            raise ValueError(f"Missing features: {missing}")
            
        return self.model.predict(df[self.features])

    def save(self):
        path = Path(self.config.params['paths']['models']) / "alpha_model.pkl"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        logger.info(f"Saved Alpha Model to {path}")

    def load(self):
        path = Path(self.config.params['paths']['models']) / "alpha_model.pkl"
        if not path.exists():
            raise FileNotFoundError("Model not trained yet.")
        self.model = joblib.load(path)
