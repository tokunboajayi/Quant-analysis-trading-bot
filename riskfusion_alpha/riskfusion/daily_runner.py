import pandas as pd
import uuid
import os
import shutil
from dotenv import load_dotenv
load_dotenv()  # Load .env file for API keys
from datetime import datetime, timedelta
from riskfusion.config import get_config
from riskfusion.ingest.ingest_prices import ingest_prices
from riskfusion.ingest.ingest_events import ingest_all_events
from riskfusion.features.build_features import build_features
from riskfusion.features.store import FeatureStore
from riskfusion.models.alpha_model import AlphaModel
from riskfusion.models.vol_model import VolModel
from riskfusion.portfolio.construction import PortfolioOptimizer
from riskfusion.utils.logging import get_logger, setup_logging
from riskfusion.utils.hashing import save_parquet
from riskfusion.utils.validation import DataValidator, ValidationError
from riskfusion.monitoring.drift import check_feature_drift
from riskfusion.monitoring.report import generate_monitoring_report
from riskfusion.storage import RiskFusionDB
from pathlib import Path

logger = get_logger("daily_runner")

def run_daily_pipeline(date_str: str = None):
    # Setup
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]
    config = get_config()
    audit_path = Path(config.params['paths']['audit']) / run_id
    audit_path.mkdir(parents=True, exist_ok=True)
    
    # Configure logging to file
    setup_logging(log_file=str(audit_path / "run.log"), json_format=True)
    
    if not date_str:
        date_str = datetime.today().strftime("%Y-%m-%d")
        
    logger.info(f"--- STARTING DAILY RUN FOR {date_str} (ID: {run_id}) ---")

    # DB Persistence
    db = RiskFusionDB()
    db.log_run(run_id, date_str, "STARTED", os.environ.get("EXECUTION_MODE", "SIMULATION"), {})
    
    try:
        # 1. Ingest
        start_fetch = (pd.to_datetime(date_str) - timedelta(days=5)).strftime("%Y-%m-%d")
        logger.info("Step 1: Ingesting...")
        ingest_prices(start_fetch, date_str)
        ingest_all_events(start_fetch, date_str)
        
        # 2. Features
        logger.info("Step 2: Building features...")
        build_features()
        
        store = FeatureStore()
        latest_features = store.load_features()
        
        # VALIDATE FEATURES
        # Identify model features from AlphaModel (instantiate to get list)
        am_temp = AlphaModel()
        DataValidator.validate_features(latest_features, am_temp.features)
        
        # 3. Model & Drift
        target_date = pd.to_datetime(date_str)
        day_feats = latest_features[latest_features['date'] == target_date]
        
        if day_feats.empty:
            logger.warning(f"No features for {date_str}. Using latest available.")
            target_date = latest_features['date'].max()
            day_feats = latest_features[latest_features['date'] == target_date]

        day_feats = day_feats.set_index('ticker')

        # DRIFT CHECK (Compare to random sample of past)
        # Simple sample: last 30 days excluding today
        past_df = latest_features[latest_features['date'] < target_date].sample(frac=0.1)
        drift_metrics = check_feature_drift(past_df, day_feats.reset_index(), am_temp.features)
        
        # 4. Predict
        alpha_model = AlphaModel()
        try:
            alpha_model.load()
        except FileNotFoundError:
            logger.warning("Training new model...")
            alpha_model.train(latest_features)

        alpha_scores = alpha_model.predict(day_feats)
        alpha_series = pd.Series(alpha_scores, index=day_feats.index)
        
        vol_model = VolModel()
        vol_hat = vol_model.predict(day_feats)
        
        # 5. Optimize
        optimizer = PortfolioOptimizer()
        risk_data = pd.DataFrame({'vol_hat': vol_hat}, index=day_feats.index)
        
        # --- EVENT RISK UPDATE (Impact ML) ---
        # Predict High Impact Prob using EventRiskModel
        from riskfusion.models.event_risk import EventRiskModel
        
        # Reuse existing 'store' from line 49
        # Get LAST available news (today's)
        news_df = store.load_raw_news()
        if not news_df.empty:
            # Filter for recent news (today/yesterday) that impacts tomorrow's trade
            # In live, we run at night for tomorrow open.
            today_news = news_df[news_df['timestamp'].dt.normalize() == target_date].copy()
            if not today_news.empty:
                logger.info(f"Predicting Event Risk for {len(today_news)} headlines...")
                ev_model = EventRiskModel()
                # If model not trained, this returns zeros.
                # In Grand Run, maybe we should train on historical data first? 
                # For now, we assume pre-trained or it will return safe 0s.
                probs = ev_model.predict(today_news)
                today_news['event_risk'] = probs
                
                # Aggregate max risk per ticker
                ticker_risk = today_news.groupby('ticker')['event_risk'].max()
                
                # Merge into risk_data
                risk_data = risk_data.join(ticker_risk, how='left').fillna(0.0)
            else:
                risk_data['event_risk'] = 0.0
        else:
             risk_data['event_risk'] = 0.0

        weights = optimizer.construct_weights(alpha_series, risk_data)
        
        # VALIDATE WEIGHTS
        DataValidator.validate_weights(weights)

        # Log Portfolio Snapshot to DB
        db.log_snapshot(run_id, weights, risk_data, alpha_series)

        # 6. Execution (Live or Simulated)
        # PAPER and LIVE both submit orders to Alpaca (PAPER uses paper-api endpoint)
        mode = os.environ.get("EXECUTION_MODE", "SIMULATION")
        
        if mode in ("LIVE", "PAPER"):
            logger.warning(f">>> {mode} EXECUTION ENABLED <<<")
            from riskfusion.execution.oms import OMS
            oms = OMS()
            # DEBUG: Print weights stats
            logger.info(f"DEBUG: weights shape = {weights.shape}")
            logger.info(f"DEBUG: weights dtypes = {weights.dtypes.to_dict()}")
            logger.info(f"DEBUG: weights NaNs = {weights['weight'].isna().sum()}")
            logger.info(f"DEBUG: weights sample:\\n{weights.head(10)}")
            # Execute
            result = oms.execute_rebalance(weights)
            logger.info(f"Execution Result: {result}")
            
            # Log Trades to DB
            if 'details' in result:
                db.log_trades(run_id, result['details'])
        else:
            logger.info(f"Simulated Rebalance: \n{weights}")
        
        # 6. Output
        logger.info("Step 6: Writing outputs...")
        output_path = Path(config.params['paths']['outputs'])
        
        w_filename = f"daily_weights_{target_date.strftime('%Y%m%d')}.csv"
        weights.to_csv(output_path / w_filename)
        weights.to_csv(audit_path / "weights.csv")
        
        generate_monitoring_report(date_str, "SUCCESS", drift_metrics, weights, run_id)
        
        # Log Success
        db.log_run(run_id, date_str, "SUCCESS", mode, drift_metrics)
        logger.info(f"SUCCESS. Run ID {run_id}")
        
    except Exception as e:
        logger.error(f"Run FAILED: {e}", exc_info=True)
        # Log Failure
        db.log_run(run_id, date_str, "FAILED", os.environ.get("EXECUTION_MODE", "SIMULATION"), {'error': str(e)})
        generate_monitoring_report(date_str, f"FAILED: {str(e)}", {}, pd.DataFrame(), run_id)
        
        # Fallback Logic
        if os.getenv("ALLOW_FALLBACK_WEIGHTS") == "1":
            logger.warning("Attempting fallback to yesterday's weights...")
            # Look for yesterday's file
            yest = (pd.to_datetime(target_date) - timedelta(days=1)).strftime('%Y%m%d')
            yest_file = Path(config.params['paths']['outputs']) / f"daily_weights_{yest}.csv"
            if yest_file.exists():
                fallback_file = Path(config.params['paths']['outputs']) / f"daily_weights_{target_date.strftime('%Y%m%d')}_FALLBACK.csv"
                shutil.copy(yest_file, fallback_file)
                logger.info(f"Fallback successful: {fallback_file}")
            else:
                logger.error("No fallback file found.")
        raise e

if __name__ == "__main__":
    run_daily_pipeline()
