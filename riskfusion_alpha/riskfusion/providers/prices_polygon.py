import os
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger
from riskfusion.providers.prices_base import PriceProvider

logger = get_logger("polygon_prices")

class PolygonPriceProvider(PriceProvider):
    def __init__(self):
        self.config = get_config()
        self.api_key = os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment.")
        
        self.base_url = "https://api.polygon.io"
        
        # Rate Limiting: 5 requests / minute for free tier
        # We'll use a simple sleep method. 
        # Ideally, we should use a token bucket or similar if we were serious.
        # But for "Professional Data Layer" implies we might have a paid key? 
        # The prompt didn't specify Tier. We assume basic hygiene.
        self.last_req_time = 0
        self.min_interval = 12.0 # 60s / 5 req = 12s per req (Very slow!)
        # Verify if paid key? 
        # Let's assume user has a basic key but we want to be safe.
        # Actually, user provided a key, maybe it's paid.
        # Let's start with a less aggressive limit: 5 req/sec (standard paid).
        # We can implement an adaptive backoff.
        
    def _rate_limit(self):
        """Simple sleep to prevent 429"""
        # For now, let's just respect 429s if they happen (see _get)
        pass

    def _get(self, endpoint: str, params: Dict = {}) -> Dict:
        params['apiKey'] = self.api_key
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(3):
            resp = requests.get(url, params=params)
            
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                logger.warning("Polygon Rate Limit Hit. Sleeping 60s...")
                time.sleep(61)
                continue
            else:
                resp.raise_for_status()
        raise Exception("Max Retries Exceeded for Polygon")

    def download_prices(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """
        Download daily bars (OHLCV) for a list of tickers.
        Polygon Aggregates Endpoint: /v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}
        """
        all_data = []
        
        for ticker in tickers:
            logger.info(f"Downloading {ticker} from Polygon...")
            
            # Format: YYYY-MM-DD
            endpoint = f"/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
            params = {
                "adjusted": "true",
                "sort": "asc",
                "limit": 50000
            }
            
            try:
                data = self._get(endpoint, params)
                
                if 'results' not in data:
                    logger.warning(f"No results for {ticker}")
                    continue
                    
                df = pd.DataFrame(data['results'])
                # Polygon cols: v, vw, o, c, h, l, t, n
                # Map to standard: Open, High, Low, Close, Volume
                df = df.rename(columns={
                    'o': 'Open',
                    'h': 'High',
                    'l': 'Low',
                    'c': 'Close',
                    'v': 'Volume',
                    't': 'Date'
                })
                
                # Convert timestamp (ms) to datetime
                df['Date'] = pd.to_datetime(df['Date'], unit='ms')
                df['Ticker'] = ticker
                
                # Filter relevant columns
                df = df[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
                all_data.append(df)
                
            except Exception as e:
                logger.error(f"Failed to download {ticker}: {e}")
                
        if not all_data:
            return pd.DataFrame()
            
        final_df = pd.concat(all_data, ignore_index=True)
        return final_df

    def get_history(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Alias for download_prices to satisfy base class contract."""
        return self.download_prices(tickers, start_date, end_date)
