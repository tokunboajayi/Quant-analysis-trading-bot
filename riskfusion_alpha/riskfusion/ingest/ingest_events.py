from riskfusion.config import get_config
from riskfusion.providers.news_marketaux import MarketAuxProvider
from riskfusion.providers.filings_sec import SECFilingsProvider
from riskfusion.utils.hashing import save_parquet
from riskfusion.utils.logging import get_logger, setup_logging
import pandas as pd

logger = get_logger("ingest_events")

def ingest_all_events(start_date: str = None, end_date: str = None):
    config = get_config()
    tickers = config.universe
    
    if not start_date:
        start_date = config.data['start_date']
    if not end_date:
        from datetime import datetime
        end_date = datetime.today().strftime('%Y-%m-%d')

    # 1. News
    logger.info("Ingesting News...")
    news_prov = MarketAuxProvider()
    news_df = news_prov.get_headlines(tickers, start_date, end_date)
    if not news_df.empty:
        path = f"{config.params['paths']['raw']}/news.parquet"
        save_parquet(news_df, path)
        logger.info(f"Saved {len(news_df)} news items.")
    else:
        logger.info("No news found.")

    # 2. Filings
    logger.info("Ingesting SEC Filings...")
    sec_prov = SECFilingsProvider()
    filings_df = sec_prov.get_filings(tickers, start_date)
    if not filings_df.empty:
        path = f"{config.params['paths']['raw']}/filings.parquet"
        save_parquet(filings_df, path)
        logger.info(f"Saved {len(filings_df)} filings.")
    else:
        logger.info("No filings found.")

if __name__ == "__main__":
    setup_logging()
    ingest_all_events()
