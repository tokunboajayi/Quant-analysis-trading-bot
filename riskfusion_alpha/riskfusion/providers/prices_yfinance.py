import yfinance as yf
import pandas as pd
from typing import List
from riskfusion.providers.prices_base import PriceProvider
from riskfusion.utils.logging import get_logger

logger = get_logger("prices_yfinance")

class YFinanceProvider(PriceProvider):
    """
    Yahoo Finance Data Provider
    """
    def get_history(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        logger.info(f"Downloading data for {len(tickers)} tickers from {start_date} to {end_date}...")
        
        # yfinance download
        # group_by='ticker' makes it hierarchical columns if >1 ticker
        # But group_by='column' is default. 
        # Easier to handle multi-ticker download
        
        try:
            data = yf.download(
                tickers, 
                start=start_date, 
                end=end_date, 
                group_by='ticker', 
                auto_adjust=False, # We want Adj Close separate usually, or we can use auto_adjust=True to overwrite Close
                actions=False,
                threads=True, 
                progress=False
            )
        except Exception as e:
            logger.error(f"Failed to download data: {e}")
            raise

        if data.empty:
            logger.warning("No data downloaded.")
            return pd.DataFrame()

        # Reshape data: Stack to make it tall (date, ticker, O, H, L, C, V)
        # If single ticker, YF returns simple DF. If multiple, it returns MultiIndex columns.
        
        if len(tickers) == 1:
            # Single ticker case
            df = data.reset_index()
            df['ticker'] = tickers[0]
        else:
            # Multi ticker case
            # Columns are (Ticker, Field) -> need to stack level 0
            df = data.stack(level=0).reset_index()
            # Rename columns to standardized names
            # Expected from stack: Date, Ticker, Adj Close, Close, High, Low, Open, Volume
            df.rename(columns={'level_1': 'ticker', 'Ticker': 'ticker'}, inplace=True)
        
        # Standardize columns
        cols_map = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Adj Close': 'adj_close',
            'Volume': 'volume'
        }
        df.rename(columns=cols_map, inplace=True)
        
        # Ensure lower case columns
        df.columns = [c.lower() for c in df.columns]
        
        # Validation
        val_cols = ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']
        missing = [c for c in val_cols if c not in df.columns]
        if missing:
            # Maybe 'Adj Close' wasn't returned or something
            logger.warning(f"Missing columns: {missing}")
        
        # Ensure types
        df['date'] = pd.to_datetime(df['date'])
        
        # Sort
        df.sort_values(['date', 'ticker'], inplace=True)
        
        logger.info(f"Downloaded {len(df)} rows.")
        return df

if __name__ == "__main__":
    # Test
    p = YFinanceProvider()
    d = p.get_history(["SPY", "AAPL"], "2023-01-01", "2023-01-10")
    print(d.head())
