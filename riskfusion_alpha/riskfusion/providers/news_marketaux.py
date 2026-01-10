import requests
import pandas as pd
from typing import List, Optional
import os
from datetime import datetime
from riskfusion.utils.logging import get_logger

logger = get_logger("news_marketaux")

class MarketAuxProvider:
    """
    MarketAux News API Provider
    """
    BASE_URL = "https://api.marketaux.com/v1/news/all"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MARKETAUX_API_KEY")
        if not self.api_key:
            logger.warning("MARKETAUX_API_KEY not found. News ingestion will be skipped or mocked.")

    def get_headlines(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch news for tickers.
        Note: MarketAux free tier has rate limits and limitations on history depth.
        We will iterate carefully.
        """
        if not self.api_key:
            logger.warning("No API Key. Returning empty DataFrame.")
            return pd.DataFrame()

        # Join tickers (limit per request usually 3)
        symbols = ",".join(tickers[:3]) # simple truncation for safety in this demo
        
        params = {
            "api_token": self.api_key,
            "symbols": symbols,
            "published_after": start_date + "T00:00:00",
            "published_before": end_date + "T23:59:59",
            "language": "en",
            "limit": 3 # limit for testing
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = data.get("data", [])
            records = []
            for art in articles:
                records.append({
                    "event_id": art.get("uuid"),
                    "timestamp": art.get("published_at"),
                    "title": art.get("title"),
                    "description": art.get("description"),
                    "url": art.get("url"),
                    "source": art.get("source"),
                    "tickers": ",".join([e["symbol"] for e in art.get("entities", [])]),
                    "provider": "marketaux"
                })
            
            df = pd.DataFrame(records)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Normalize cols
            return df

        except Exception as e:
            logger.error(f"MarketAux request failed: {e}")
            return pd.DataFrame()
