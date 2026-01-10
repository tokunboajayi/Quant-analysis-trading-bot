import pandas as pd
from datetime import datetime, timedelta
from riskfusion.config import get_config
from riskfusion.providers.prices_yfinance import YFinanceProvider
from riskfusion.utils.hashing import save_parquet
from riskfusion.utils.logging import get_logger, setup_logging

logger = get_logger("ingest_prices")

def ingest_prices(start_date: str = None, end_date: str = None):
    config = get_config()
    
    # Defaults
    if not start_date:
        start_date = config.data.get("start_date", "2015-01-01")
    if not end_date:
        end_date = datetime.today().strftime('%Y-%m-%d')
        
    tickers = config.universe
    
    logger.info(f"Starting price ingestion for {len(tickers)} tickers from {start_date} to {end_date}")
    
    # Instantiate provider
    config_params = config.params
    provider_name = config_params.get("price_provider", "yfinance")
    logger.info(f"Ingesting prices using provider: {provider_name}")
    
    if provider_name == "polygon":
        from riskfusion.providers.prices_polygon import PolygonPriceProvider
        provider = PolygonPriceProvider()
    else:
        from riskfusion.providers.prices_yfinance import YFinanceProvider
        provider = YFinanceProvider()
    
    try:
        if provider_name == "polygon":
             # Polygon class uses download_prices name for now
             df = provider.download_prices(tickers, start_date, end_date)
        else:
             df = provider.get_history(tickers, start_date, end_date)
        
        if df.empty:
            logger.warning("No price data fetched!")
            return

        # Save to Raw
        raw_path = f"{config.params['paths']['raw']}/prices.parquet"
        logger.info(f"Saving to {raw_path}")
        
        # We save as a single large parquet for now (simple MVP)
        # In production, we'd partition by date or ticker. 
        # Using partition_cols=['ticker'] is good for per-ticker reads.
        save_parquet(df, raw_path, partition_cols=['ticker'])
        
        # Also save a 'latest' snapshot without partitions for easier loading of full universe?
        # Actually partition by ticker is fine. 
        
        logger.info("Price ingestion complete.")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    setup_logging()
    ingest_prices()
