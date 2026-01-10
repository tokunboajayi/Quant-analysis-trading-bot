from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Optional

class PriceProvider(ABC):
    """
    Abstract Interface for Price Data Providers.
    """
    
    @abstractmethod
    def get_history(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date YYYY-MM-DD
            end_date: End date YYYY-MM-DD
            
        Returns:
            DataFrame with columns: [date, ticker, open, high, low, close, volume]
            and optionally [adj_close]
            indexed by (date, ticker) or just integer index, but must contain 'date' and 'ticker'.
        """
        pass
