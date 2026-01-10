"""
RiskFusion Alpha - Full System Diagnostic
==========================================
"""
from dotenv import load_dotenv
load_dotenv()

import os
import sys

def check_env_vars():
    print("=" * 50)
    print("1. ENVIRONMENT VARIABLES")
    print("=" * 50)
    vars_to_check = [
        "POLYGON_API_KEY",
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
        "ALPACA_BASE_URL",
        "MARKETAUX_API_KEY",
        "EXECUTION_MODE"
    ]
    for v in vars_to_check:
        val = os.environ.get(v)
        if val:
            # Mask sensitive parts
            masked = val[:8] + "..." if len(val) > 8 else val
            print(f"  ✅ {v}: {masked}")
        else:
            print(f"  ❌ {v}: NOT SET")

def check_alpaca():
    print("\n" + "=" * 50)
    print("2. ALPACA CONNECTIVITY")
    print("=" * 50)
    try:
        from riskfusion.execution.alpaca_connector import AlpacaConnector
        ac = AlpacaConnector()
        account = ac.get_account()
        print(f"  ✅ Account Status: {account.get('status')}")
        print(f"  ✅ Equity: ${float(account.get('equity', 0)):,.2f}")
        print(f"  ✅ Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
        
        # Check positions
        positions = ac.get_positions()
        print(f"  ✅ Open Positions: {len(positions)}")
        if positions:
            for p in positions[:5]:
                print(f"      - {p['symbol']}: {p['qty']} shares @ ${float(p['avg_entry_price']):.2f}")
    except Exception as e:
        print(f"  ❌ Alpaca Error: {e}")

def check_data():
    print("\n" + "=" * 50)
    print("3. DATA LAYER")
    print("=" * 50)
    try:
        from riskfusion.features.store import FeatureStore
        store = FeatureStore()
        
        prices = store.load_raw_prices()
        print(f"  ✅ Prices: {len(prices)} rows, {prices['ticker'].nunique()} tickers")
        
        features = store.load_features()
        print(f"  ✅ Features: {len(features)} rows, {len(features.columns)} columns")
        
        news = store.load_raw_news()
        print(f"  {'✅' if len(news) > 0 else '⚠️'} News: {len(news)} events")
    except Exception as e:
        print(f"  ❌ Data Error: {e}")

def check_models():
    print("\n" + "=" * 50)
    print("4. MODELS")
    print("=" * 50)
    try:
        from riskfusion.models.alpha_model import AlphaModel
        from riskfusion.models.vol_model import VolModel
        from riskfusion.models.event_risk import EventRiskModel
        from pathlib import Path
        
        model_path = Path("models/alpha_lgbm.pkl")
        print(f"  {'✅' if model_path.exists() else '⚠️'} Alpha Model: {'Trained' if model_path.exists() else 'Not Trained'}")
        
        vol_path = Path("models/vol_model.pkl")
        print(f"  {'✅' if vol_path.exists() else '⚠️'} Vol Model: {'Trained' if vol_path.exists() else 'Not Trained'}")
        
        event_path = Path("models/event_risk_model.pkl")
        print(f"  {'✅' if event_path.exists() else '⚠️'} Event Risk Model: {'Trained' if event_path.exists() else 'Not Trained'}")
    except Exception as e:
        print(f"  ❌ Model Error: {e}")

def check_outputs():
    print("\n" + "=" * 50)
    print("5. OUTPUTS")
    print("=" * 50)
    from pathlib import Path
    import glob
    
    output_dir = Path("data/outputs")
    weights_files = list(output_dir.glob("daily_weights_*.csv"))
    reports = list(output_dir.glob("monitoring_report_*.md"))
    
    print(f"  ✅ Weight Files: {len(weights_files)}")
    for f in weights_files[-3:]:
        print(f"      - {f.name}")
    
    print(f"  ✅ Reports: {len(reports)}")

def main():
    print("\n🔬 RISKFUSION ALPHA - FULL SYSTEM DIAGNOSTIC\n")
    check_env_vars()
    check_alpaca()
    check_data()
    check_models()
    check_outputs()
    print("\n" + "=" * 50)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()
