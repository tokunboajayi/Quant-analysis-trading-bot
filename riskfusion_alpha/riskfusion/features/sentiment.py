import pandas as pd
from textblob import TextBlob
from riskfusion.utils.logging import get_logger

logger = get_logger("sentiment_features")

def calculate_sentiment(text: str) -> float:
    """Return polarity score (-1 to 1)."""
    if not isinstance(text, str):
        return 0.0
    return TextBlob(text).sentiment.polarity

def build_sentiment_features(events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Augment events DataFrame with sentiment scores.
    Expected columns: ['date', 'ticker', 'title', 'description']
    Returns DataFrame with ['sentiment_score', 'sentiment_7d_avg']
    """
    if events_df.empty:
        logger.warning("Empty events dataframe.")
        return pd.DataFrame()
        
    logger.info("Calculating sentiment scores...")
    
    # Combine title and description
    events_df['full_text'] = events_df['title'].fillna('') + " " + events_df['description'].fillna('')
    
    # Apply TextBlob (Slow for millions of rows, okay for MVP)
    events_df['sentiment_score'] = events_df['full_text'].apply(calculate_sentiment)
    
    # Aggregate by Ticker + Date
    # We want daily sentiment per ticker
    daily_sent = events_df.groupby(['date', 'ticker'])['sentiment_score'].mean().reset_index()
    
    # Calculate rolling averages
    # Need to re-index to ensure continuous days or use rolling on time index
    daily_sent = daily_sent.set_index('date').sort_index()
    
    # Group by ticker again to roll
    result_frames = []
    for ticker, group in daily_sent.groupby('ticker'):
        group = group.sort_index()
        # 7-day moving average of sentiment
        group['sentiment_7d_avg'] = group['sentiment_score'].rolling('7D').mean()
        
        # Sentiment Shock: Today vs 30D Avg
        group['sentiment_30d_avg'] = group['sentiment_score'].rolling('30D').mean()
        group['sentiment_shock'] = group['sentiment_score'] - group['sentiment_30d_avg']
        
        result_frames.append(group)
        
    if not result_frames:
        return pd.DataFrame()
        
    final_df = pd.concat(result_frames).reset_index()
    final_df = final_df[['date', 'ticker', 'sentiment_score', 'sentiment_7d_avg', 'sentiment_shock']]
    
    logger.info(f"Generated sentiment features for {len(final_df)} ticker-days.")
    return final_df
