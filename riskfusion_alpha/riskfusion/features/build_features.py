import pandas as pd
import numpy as np
from riskfusion.features.store import FeatureStore
from riskfusion.features.technical import compute_returns, compute_volatility, compute_rsi, compute_macd, compute_zscores
from riskfusion.utils.logging import get_logger

logger = get_logger("build_features")

def build_features(start_date=None):
    store = FeatureStore()
    
    logger.info("Loading raw prices...")
    prices = store.load_raw_prices()
    
    if prices.empty:
        logger.error("No prices found.")
        return

    # Process per ticker
    logger.info("Computing technical features...")
    
    # We group by ticker and apply transformations
    # For efficiency with pandas, we can use group apply or pre-sort and use rolling
    # prices is already sorted by date,ticker. Let's sort by ticker,date for rolling ops.
    prices = prices.sort_values(['ticker', 'date'])
    
    processed_dfs = []
    
    for ticker, group in prices.groupby('ticker'):
        group = group.copy()
        
        # 1. Technicals
        rets = compute_returns(group)
        vols = compute_volatility(group)
        rsi = compute_rsi(group)
        macd = compute_macd(group)
        zscore = compute_zscores(group, window=20)
        
        # Concat features
        feats = pd.concat([group, rets, vols, macd, zscore], axis=1)
        feats['rsi'] = rsi
        
        # 2. Targets (Shifted Returns)
        # Target: Forward 5D return
        feats['target_fwd_5d'] = feats['close'].pct_change(5).shift(-5)
        # Target: Forward 1D return (for Tail/Risk)
        feats['target_fwd_1d'] = feats['close'].pct_change(1).shift(-1)
        
        processed_dfs.append(feats)

    full_df = pd.concat(processed_dfs)
    
    # 3. Cross-sectional Features (Requires full universe per date)
    # e.g. Rank of Momentum
    logger.info("Computing cross-sectional features...")
    
    # Reset index to operate on columns
    full_df = full_df.reset_index(drop=True)
    
    # Example: Z-Score of 20D Return across universe per day
    # Group by date
    def xs_zscore(x):
        return (x - x.mean()) / x.std()
        
    full_df['xs_mom_20d'] = full_df.groupby('date')['ret_20d'].transform(xs_zscore)
    full_df['xs_vol_20d'] = full_df.groupby('date')['realized_vol_20d'].transform(xs_zscore)
    
    # 4. Merge Event Features
    from riskfusion.features.event_features import aggregate_events
    # from riskfusion.features.sentiment import build_sentiment_features
    
    logger.info("Merging event features...")
    
    # A. Counts
    event_df = aggregate_events(prices)
    if not event_df.empty:
        # full_df has 'date' and 'ticker' columns. event_df has index (date, ticker)
        full_df = full_df.set_index(['date', 'ticker']).join(event_df, how='left').fillna(0).reset_index()
    else:
        full_df['news_count'] = 0
        full_df['filings_count'] = 0

    # B. Sentiment (REMOVED in favor of Impact ML)
    # logger.info("Merging sentiment features...")
    # ...

    # 5. Handle NaNs (drop rows where we can't compute features)
    # But be careful not to drop everything if data is short.
    # We usually drop the first N rows per ticker (warmup)
    
    # Save
    store.save_features(full_df)
    logger.info(f"Built features for {len(full_df)} rows.")

if __name__ == "__main__":
    from riskfusion.utils.logging import setup_logging
    setup_logging()
    build_features()
