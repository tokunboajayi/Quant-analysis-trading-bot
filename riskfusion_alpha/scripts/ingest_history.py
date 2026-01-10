
import os
import glob
import pandas as pd
from datetime import datetime
from riskfusion.storage import RiskFusionDB
from pathlib import Path
import re

# Files provided by user
FILES = [
    r"c:\Users\olato\OneDrive\Documents\finance ai\riskfusion_alpha\data\outputs\ablation_metrics_20260109_232514.csv",
    r"c:\Users\olato\OneDrive\Documents\finance ai\riskfusion_alpha\data\outputs\ablation_metrics_20260109_233338.csv",
    r"c:\Users\olato\OneDrive\Documents\finance ai\riskfusion_alpha\data\outputs\ablation_report_20260109_230758.md",
    r"c:\Users\olato\OneDrive\Documents\finance ai\riskfusion_alpha\data\outputs\ablation_report_20260109_232514.md",
    r"c:\Users\olato\OneDrive\Documents\finance ai\riskfusion_alpha\data\outputs\ablation_report_20260109_233338.md",
    r"c:\Users\olato\OneDrive\Documents\finance ai\riskfusion_alpha\data\outputs\daily_weights_20260108.csv",
    r"c:\Users\olato\OneDrive\Documents\finance ai\riskfusion_alpha\data\outputs\daily_weights_20260109.csv",
    r"c:\Users\olato\OneDrive\Documents\finance ai\riskfusion_alpha\data\outputs\monitoring_report_2026-01-09.md",
    r"c:\Users\olato\OneDrive\Documents\finance ai\riskfusion_alpha\data\outputs\monitoring_report_2026-01-10.md"
]

def extract_run_id(filename, content=None):
    # Try to find date/time in filename
    # Format 1: 20260109_232514
    match = re.search(r"(\d{8}_\d{6})", filename)
    if match:
        return match.group(1)
    
    # Format 2: 2026-01-09 (Date only) -> Create synthetic run ID
    match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    if match:
        return f"{match.group(1).replace('-', '')}_000000_HIST"
        
    # Format 3: 20260108 (Date only)
    match = re.search(r"(\d{8})", filename)
    if match:
        return f"{match.group(1)}_000000_HIST"

    # Try content (Markdown Run ID)
    if content:
        match = re.search(r"\*\*Run ID\*\*: `(.*?)`", content)
        if match:
            return match.group(1)
            
    return "UNKNOWN_RUN"

def ingest():
    db = RiskFusionDB()
    print("Starting ingestion...")
    
    for fpath in FILES:
        if not os.path.exists(fpath):
            print(f"Skipping missing: {fpath}")
            continue
            
        fname = os.path.basename(fpath)
        print(f"Processing {fname}...")
        
        # 1. Ablation Metrics (CSV)
        if "ablation_metrics" in fname and fname.endswith(".csv"):
            run_id = extract_run_id(fname)
            df = pd.read_csv(fpath)
            db.log_ablation_metrics(run_id, df)
            print(f"  -> Logged ablation metrics for {run_id}")
            
        # 2. Daily Weights (CSV)
        elif "daily_weights" in fname and fname.endswith(".csv"):
            run_id = extract_run_id(fname)
            df = pd.read_csv(fpath)
            # Dedup!
            df = df.drop_duplicates(subset=['ticker'])
            if 'weight' not in df.columns:
                 print("  -> Invalid weights file (no weight col)")
                 continue
            # Ensure index is numeric 0..N, store expects row['ticker']? 
            # storage.log_snapshot uses iterrows and expects 'ticker' in index or col? 
            # Let's check storage.py logic.
            # log_snapshot iterates: `for ticker, row in weights_df.iterrows():` 
            # It expects `ticker` in INDEX if it iterates (index, row). 
            # Wait, `for ticker, row in weights_df.iterrows()`: ticker is the Index. 
            # So weights_df must be indexed by ticker!
            
            if 'ticker' in df.columns:
                df = df.set_index('ticker')
            
            db.log_snapshot(run_id, df)
            print(f"  -> Logged snapshot for {run_id}")

        # 3. Reports (MD)
        elif fname.endswith(".md"):
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            run_id = extract_run_id(fname, content)
            
            rtype = "general"
            if "monitoring_report" in fname: rtype = "monitoring"
            elif "ablation_report" in fname: rtype = "ablation"
            
            db.log_report(run_id, rtype, fname, content)
            print(f"  -> Logged report {rtype} for {run_id}")
            
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest()
