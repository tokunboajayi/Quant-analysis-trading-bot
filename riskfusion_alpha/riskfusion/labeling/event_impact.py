import pandas as pd
import numpy as np
from riskfusion.features.store import FeatureStore
from riskfusion.utils.logging import get_logger

logger = get_logger("event_labeling")

class EventLabeler:
    """
    Labels events based on Real Market Impact.
    Logic:
    - Events from News and Filings.
    - Measure Forward Return (1D, 5D) vs SPY.
    - If |Return - SPY| > Threshold, Label = 1 (High Impact).
    """
    def __init__(self):
        self.store = FeatureStore()
        # Thresholds from Master Prompt
        self.THRESH_1D = 0.02 # 2%
        self.THRESH_5D = 0.05 # 5%
    
    def _load_data(self):
        prices = self.store.load_raw_prices()
        news = self.store.load_raw_news()
        filings = self.store.load_raw_filings()
        
        # Combine events
        events = pd.concat([news, filings], ignore_index=True)
        if events.empty:
            logger.warning("No events to label.")
            return None, None
            
        if prices.empty:
            logger.warning("No prices for labeling.")
            return None, None
            
        return events, prices

    def label_events(self) -> pd.DataFrame:
        events, prices = self._load_data()
        if events is None:
            return pd.DataFrame()
            
        logger.info(f"Labeling {len(events)} labels...")
        
        # 1. Prepare Market Data (SPY)
        market = prices[prices['ticker'] == 'SPY'].copy()
        market = market.set_index('date').sort_index()
        market['ret_1d'] = market['close'].pct_change(1).shift(-1) # Forward 1D
        market['ret_5d'] = market['close'].pct_change(5).shift(-5) # Forward 5D
        
        # 2. Prepare Ticker Data
        # LEAKAGE RULE: Events after market close (16:00 ET) are assigned to next trading day.
        # We assume timestamps are in ET or UTC consistent with market hours. 
        # (Assuming UTC for now, 16:00 ET is 21:00 UTC approx. Let's assume input is local NY time or handle conservatively).
        # PROMPT RULE: "Events after market close are only eligible starting next trading day."
        
        # Simple heuristic: If hour >= 16, shift to next day.
        # Note: This is a simplification. Real engine uses Trading Calendars.
        
        events['timestamp'] = pd.to_datetime(events['timestamp'])
        
        # Logic: Effective Date
        # If hour >= 16: Date = timestamp.date() + 1 day
        # Else: Date = timestamp.date()
        
        # Vectorized shift
        events['effective_date'] = events['timestamp'].dt.normalize()
        # Find rows where hour >= 16
        after_close = events['timestamp'].dt.hour >= 16
        events.loc[after_close, 'effective_date'] += pd.Timedelta(days=1)
        
        # We merge on 'effective_date' which aligns with Price Date
        
        # Merge prices to get Ticker Returns
        # prices needs fwd returns first
        # FORMULA: r_asset = close(t+1)/close(t) - 1
        # This is exactly pct_change(1).shift(-1)
        prices['ret_1d'] = prices.groupby('ticker')['close'].pct_change(1).shift(-1)
        prices['ret_5d'] = prices.groupby('ticker')['close'].pct_change(5).shift(-5)
        
        merged = events.merge(prices[['date', 'ticker', 'ret_1d', 'ret_5d']], 
                              left_on=['effective_date', 'ticker'], 
                              right_on=['date', 'ticker'], 
                              how='inner')
        
        # Join SPY Returns on effective_date
        merged = merged.merge(market[['ret_1d', 'ret_5d']], 
                              left_on='effective_date', 
                              right_index=True, 
                              suffixes=('', '_mkt'))
        
        # 3. Calculate Abnormal Returns
        # Impact = |r_asset - r_spy|
        merged['ar_1d'] = (merged['ret_1d'] - merged['ret_1d_mkt']).abs()
        merged['ar_5d'] = (merged['ret_5d'] - merged['ret_5d_mkt']).abs()
        
        # 4. Label
        merged['label_1d'] = (merged['ar_1d'] >= self.THRESH_1D).astype(int)
        merged['label_5d'] = (merged['ar_5d'] >= self.THRESH_5D).astype(int)
        
        # Aggregate Label (High Impact if EITHER 1D or 5D is high impact? Or separate models?)
        # Prompt implies "High Risk". Let's use 1D for immediate reaction.
        merged['high_impact'] = merged['label_1d'] | merged['label_5d']
        
        logger.info(f"Labeled {len(merged)} events. Impact Rate: {merged['high_impact'].mean():.2%}")
        
        # Return columns for training
        out_cols = ['event_id', 'timestamp', 'ticker', 'title', 'description', 
                   'high_impact', 'label_1d', 'label_5d', 'ar_1d', 'ar_5d']
        return merged[out_cols]

    def save_labels(self, df):
        if df.empty:
            return
        path = self.store.processed_path / "labeled_events.parquet"
        from riskfusion.utils.hashing import save_parquet
        save_parquet(df, path)
        logger.info(f"Saved labeled events to {path}")

if __name__ == "__main__":
    from riskfusion.utils.logging import setup_logging
    setup_logging()
    lab = EventLabeler()
    df = lab.label_events()
    lab.save_labels(df)
