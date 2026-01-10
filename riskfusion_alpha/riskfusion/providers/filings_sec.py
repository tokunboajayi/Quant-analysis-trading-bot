from typing import List
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from riskfusion.utils.logging import get_logger
import time

logger = get_logger("filings_sec")

class SECFilingsProvider:
    """
    SEC provider using standard RSS Atom feeds or requests to search pages.
    Includes 8-K (Events), 10-Q (Quarterly), 10-K (Annual).
    
    Actually, to target specific tickers, using the SEC JSON API is better:
    https://data.sec.gov/submissions/CIK{cik}.json
    But that requires CIK mapping.
    """
    
    USER_AGENT = "RiskFusionAlpha/1.0 (bot@riskfusion.ai)" # Required by SEC
    
    def __init__(self):
        self.headers = {"User-Agent": self.USER_AGENT}
        self.cik_map = {} # Cache ticker -> CIK

    def _get_cik(self, ticker: str) -> str:
        # MVP: Lazy usage of a free lookup or hardcoded for a few
        # Real pro way: Download company_tickers.json from SEC
        if not self.cik_map:
            try:
                url = "https://www.sec.gov/files/company_tickers.json"
                r = requests.get(url, headers=self.headers)
                if r.status_code == 200:
                    data = r.json()
                    for idx, val in data.items():
                        self.cik_map[val['ticker']] = str(val['cik_str']).zfill(10)
            except Exception as e:
                logger.warning(f"Failed to load CIK map: {e}")
        
        return self.cik_map.get(ticker.upper())

    def get_filings(self, tickers: List[str], start_date: str) -> pd.DataFrame:
        """
        Get filings for tickers from start_date (approx).
        """
        # Load CIKs
        if not self.cik_map:
            self._get_cik("SPY") # Trigger load
            
        all_filings = []
        
        for ticker in tickers:
            cik = self._get_cik(ticker)
            if not cik:
                continue
                
            # Fetch submissions JSON
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            try:
                r = requests.get(url, headers=self.headers)
                if r.status_code != 200:
                    time.sleep(0.1)
                    continue
                    
                data = r.json()
                filings = data.get("filings", {}).get("recent", {})
                
                # Arrays: accessionNumber, filingDate, reportDate, acceptanceDateTime, form, etc.
                if filings:
                    # Convert to DF
                    df_f = pd.DataFrame(filings)
                    df_f['ticker'] = ticker
                    df_f['cik'] = cik
                    
                    # Filter by date
                    df_f['filingDate'] = pd.to_datetime(df_f['filingDate'])
                    mask = df_f['filingDate'] >= pd.to_datetime(start_date)
                    df_f = df_f[mask]
                    
                    # Keep relevant forms
                    target_forms = ['8-K', '10-Q', '10-K', 'SC 13G', 'SC 13D']
                    df_f = df_f[df_f['form'].isin(target_forms)]
                    
                    if not df_f.empty:
                        all_filings.append(df_f)
                
                time.sleep(0.11) # rate limit (10 req/sec allowed)
                
            except Exception as e:
                logger.error(f"Error fetching SEC data for {ticker}: {e}")
        
        if not all_filings:
            return pd.DataFrame()
            
        final_df = pd.concat(all_filings, ignore_index=True)
        # Rename for consistency
        cols_map = {
            'filingDate': 'timestamp',
            'accessionNumber': 'event_id',
            'form': 'title' # Use form type as title proxy for now
        }
        final_df.rename(columns=cols_map, inplace=True)
        final_df['provider'] = 'sec_edgar'
        final_df['description'] = final_df['primaryDocument'] # Proxy
        
        final_df = final_df[['event_id', 'timestamp', 'ticker', 'title', 'description', 'provider']]
        return final_df
