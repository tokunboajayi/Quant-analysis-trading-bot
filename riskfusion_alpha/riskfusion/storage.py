"""
Persistence Layer for RiskFusion
================================
Stores runs, trades, and signals in a local SQLite database.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("storage")

class RiskFusionDB:
    def __init__(self):
        config = get_config()
        # Ensure data dir exists
        db_path = Path(config.params.get('paths', {}).get('data', 'data')) / "riskfusion.db"
        self.db_path = str(db_path)
        self._init_db()
        
    def _init_db(self):
        """Initialize tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 1. Runs
        c.execute('''CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            date TEXT,
            timestamp TEXT,
            status TEXT,
            mode TEXT,
            metrics_json TEXT
        )''')
        
        # 2. Trades
        c.execute('''CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            ticker TEXT,
            side TEXT,
            qty REAL,
            notional REAL,
            avg_price REAL,
            order_id TEXT,
            timestamp TEXT,
            FOREIGN KEY(run_id) REFERENCES runs(run_id)
        )''')
        
        # 3. Portfolio Snapshots (Weights)
        c.execute('''CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            run_id TEXT,
            ticker TEXT,
            weight REAL,
            alpha_score REAL,
            vol_hat REAL,
            event_risk REAL,
            PRIMARY KEY (run_id, ticker),
            FOREIGN KEY(run_id) REFERENCES runs(run_id)
        )''')

        # 4. General Reports (Markdown output)
        c.execute('''CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            report_type TEXT, -- 'monitoring', 'ablation', etc
            filename TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY(run_id) REFERENCES runs(run_id)
        )''')

        # 5. Ablation Metrics
        c.execute('''CREATE TABLE IF NOT EXISTS ablation_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT, -- or timestamp if no run_id
            step INTEGER,
            metric_name TEXT,
            metric_value REAL,
            timestamp TEXT
        )''')
        
        conn.commit()
        conn.close()
        
    def log_run(self, run_id: str, date: str, status: str, mode: str, metrics: dict):
        """Log a pipeline run."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO runs 
                         (run_id, date, timestamp, status, mode, metrics_json)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (run_id, date, datetime.utcnow().isoformat(), status, mode, json.dumps(metrics)))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log run: {e}")

    def log_trades(self, run_id: str, trades: list):
        """
        Log executed trades. 
        trades: list of dicts/objects from OMS
        """
        if not trades:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            data = []
            for t in trades:
                # Handle both Alpaca Order objects and dicts
                if hasattr(t, 'symbol'): # Alpaca object
                     data.append((
                        run_id, t.symbol, t.side, 
                        float(t.qty) if t.qty else 0, 
                        float(t.notional) if t.notional else 0,
                        float(t.filled_avg_price) if t.filled_avg_price else 0,
                        str(t.id),
                        str(t.created_at)
                    ))
                else: # Dict fallback
                    data.append((
                        run_id, t.get('symbol'), t.get('side'),
                        t.get('qty', 0), t.get('notional', 0),
                        t.get('price', 0),
                        t.get('id', ''),
                        datetime.utcnow().isoformat()
                    ))
            
            c.executemany('''INSERT INTO trades 
                             (run_id, ticker, side, qty, notional, avg_price, order_id, timestamp)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', data)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log trades: {e}")

    def log_snapshot(self, run_id: str, weights_df, risk_df=None, alpha_series=None):
        """
        Log the final portfolio snapshot with component signals.
        weights_df: DataFrame with 'weight' column
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Merge data for complete persistent record
            # We iterate weights indices
            data = []
            for ticker, row in weights_df.iterrows():
                w = float(row['weight'])
                if w == 0: continue # Skip zero weights to save space? Or keep for tracking? Let's skip zeros.
                
                a_score = 0.0
                if alpha_series is not None and ticker in alpha_series.index:
                    a_score = float(alpha_series[ticker])
                    
                v_hat = 0.0
                e_risk = 0.0
                if risk_df is not None and ticker in risk_df.index:
                    v_hat = float(risk_df.loc[ticker].get('vol_hat', 0))
                    e_risk = float(risk_df.loc[ticker].get('event_risk', 0))
                
                data.append((run_id, ticker, w, a_score, v_hat, e_risk))
                
            c.executemany('''INSERT INTO portfolio_snapshots
                             (run_id, ticker, weight, alpha_score, vol_hat, event_risk)
                             VALUES (?, ?, ?, ?, ?, ?)''', data)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log snapshot: {e}")
            
    def log_report(self, run_id: str, report_type: str, filename: str, content: str):
        """Store a markdown report."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT INTO reports (run_id, report_type, filename, content, timestamp)
                         VALUES (?, ?, ?, ?, ?)''',
                      (run_id, report_type, filename, content, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log report: {e}")

    def log_ablation_metrics(self, run_id: str, df_metrics):
        """
        Store ablation metrics from DataFrame.
        Expected df cols: step, metric1, metric2...
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            data = []
            timestamp = datetime.utcnow().isoformat()
            
            # Iterate rows
            for _, row in df_metrics.iterrows():
                step = int(row['step'])
                # Iterate columns for metrics
                for col in df_metrics.columns:
                    if col == 'step': continue
                    val = row[col]
                    if pd.isna(val): continue
                    
                    data.append((run_id, step, col, float(val), timestamp))
            
            c.executemany('''INSERT INTO ablation_metrics 
                             (run_id, step, metric_name, metric_value, timestamp)
                             VALUES (?, ?, ?, ?, ?)''', data)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log ablation: {e}")

    def get_runs(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.execute("SELECT * FROM runs ORDER BY timestamp DESC LIMIT ?", (limit,))
        res = [dict(r) for r in c.fetchall()]
        conn.close()
        return res

    def get_trades(self, limit=50):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,))
        res = [dict(r) for r in c.fetchall()]
        conn.close()
        return res
