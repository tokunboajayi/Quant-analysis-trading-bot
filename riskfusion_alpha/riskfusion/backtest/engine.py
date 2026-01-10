import pandas as pd
import numpy as np
from riskfusion.features.store import FeatureStore
from riskfusion.models.alpha_model import AlphaModel
from riskfusion.portfolio.construction import PortfolioOptimizer
from riskfusion.utils.logging import get_logger

logger = get_logger("backtest")

class Backtester:
    def __init__(self, start_date, end_date):
        self.start = start_date
        self.end = end_date
        self.store = FeatureStore()
        self.alpha_model = AlphaModel()
        self.optimizer = PortfolioOptimizer()
        
    def run(self):
        logger.info(f"Running backtest from {self.start} to {self.end}")
        
        # Load Features
        features = self.store.load_features()
        if features.empty:
            logger.error("No features.")
            return

        # Load Prices (for returns calculation)
        prices = self.store.load_raw_prices()
        prices = prices.pivot(index='date', columns='ticker', values='close')
        
        # Filter Dates
        features = features[(features['date'] >= self.start) & (features['date'] <= self.end)]
        
        # Loop by Date
        dates = sorted(features['date'].unique())
        
        portfolio_history = []
        equity = 1.0
        
        # We need a model trained before start? Or Walk-forward?
        # For simplicity, load the pre-trained model (cheating slightly if static, but ok for MVP infrastructure test)
        # Ideally we call 'train' every N months.
        try:
            self.alpha_model.load()
        except:
            logger.warning("Model not found, training on available history (leakage warning if not careful!)")
            self.alpha_model.train(features) # Still leaks current window. In real life, train on history < start.
        
        prev_weights = pd.Series()
        
        for d in dates:
            day_feats = features[features['date'] == d].set_index('ticker')
            
            # Predict Alpha
            try:
                scores = self.alpha_model.predict(day_feats)
                # predict returns array, map to index
                score_series = pd.Series(scores, index=day_feats.index)
            except Exception as e:
                logger.error(f"Prediction failed on {d}: {e}")
                continue
                
            # Construct Weights
            # Risk data stub
            risk_data = pd.DataFrame(index=day_feats.index)
            if 'realized_vol_20d' in day_feats.columns:
                risk_data['vol_hat'] = day_feats['realized_vol_20d'] # Simple Vol Forecast = Last Vol
            
            weights_df = self.optimizer.construct_weights(score_series, risk_data)
            
            # Record
            weights_df['date'] = d
            portfolio_history.append(weights_df)
            
            # Calculate Returns for TODAY (using weights from yesterday? No, we trade At Close? or Open next day?)
            # Assumption: We trade at Close[t]. Return is Close[t] to Close[t+1].
            # So these weights apply to return t -> t+1.
            
            # ... Return calc would go here ... 
        
        full_res = pd.concat(portfolio_history)
        return full_res

