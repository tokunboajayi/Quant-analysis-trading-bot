import os
import sys
from riskfusion.config import get_config
from riskfusion.ingest.ingest_prices import ingest_prices
from riskfusion.features.build_features import build_features
from riskfusion.models.train import train_models
from riskfusion.daily_runner import run_daily_pipeline

def verify_system():
    print("--- STARTING VERIFICATION ---")
    
    # 1. Override Universe for Speed
    conf = get_config()
    conf.params['universe']['tickers'] = ['SPY', 'AAPL'] # Tiny universe
    conf.params['data']['start_date'] = '2023-11-01' # Short history
    
    # 2. Ingest
    print("\n[TEST] Ingesting...")
    try:
        ingest_prices("2023-11-01", "2023-11-20")
    except Exception as e:
        print(f"Ingest failed: {e}")
        # Continue if possible? No.
    
    # 3. Features
    print("\n[TEST] Building Features...")
    try:
        build_features()
    except Exception as e:
        print(f"Features failed: {e}")

    # 4. Train
    print("\n[TEST] Training...")
    try:
        train_models()
    except Exception as e:
        print(f"Train failed: {e}")

    # 5. Daily Run
    print("\n[TEST] Daily Run...")
    try:
        run_daily_pipeline("2023-11-20")
    except Exception as e:
        print(f"Daily Run failed: {e}")

    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    verify_system()
