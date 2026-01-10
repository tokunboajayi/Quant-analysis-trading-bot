import pandas as pd
from riskfusion.config import get_config
from riskfusion.utils.hashing import load_parquet
from pathlib import Path

def aggregate_events(prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Load raw news/filings and aggregate to (ticker, date).
    """
    config = get_config()
    raw_path = Path(config.params['paths']['raw'])
    
    # Load News
    news_df = pd.DataFrame()
    if (raw_path / "news.parquet").exists():
        news_df = load_parquet(raw_path / "news.parquet")
    
    # Load Filings
    filings_df = pd.DataFrame()
    if (raw_path / "filings.parquet").exists():
        filings_df = load_parquet(raw_path / "filings.parquet")
        
    # If no events, return empty features
    if news_df.empty and filings_df.empty:
        return pd.DataFrame()

    # Normalize dates
    if not news_df.empty:
        news_df['date'] = pd.to_datetime(news_df['timestamp']).dt.normalize()
    if not filings_df.empty:
        filings_df['date'] = pd.to_datetime(filings_df['timestamp']).dt.normalize()

    # Aggregate by Ticker/Date
    # We need to map news tickers (comma sep) to rows.
    # Note: MarketAux returns "AAPL,MSFT". We need to explode.
    
    event_feats = []
    
    # Process News
    if not news_df.empty:
        # Explode tickers
        news_exploded = news_df.assign(ticker=news_df['tickers'].str.split(',')).explode('ticker')
        # Group
        news_daily = news_exploded.groupby(['date', 'ticker']).agg({
            'event_id': 'count',
            # 'sentiment': 'mean' # if we had sentiment
        }).rename(columns={'event_id': 'news_count'})
        event_feats.append(news_daily)

    # Process Filings
    if not filings_df.empty:
        filings_daily = filings_df.groupby(['date', 'ticker']).agg({
            'event_id': 'count'
        }).rename(columns={'event_id': 'filings_count'})
        event_feats.append(filings_daily)

    if not event_feats:
        return pd.DataFrame()

    # Merge all event features
    full_events = pd.concat(event_feats, axis=1).fillna(0)
    
    return full_events
