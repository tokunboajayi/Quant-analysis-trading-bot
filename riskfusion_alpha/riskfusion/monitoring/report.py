import pandas as pd
from datetime import datetime
from pathlib import Path
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("reporting")

def generate_monitoring_report(
    date_str: str,
    validation_status: str,
    drift_metrics: dict,
    weights_df: pd.DataFrame,
    audit_id: str
):
    """
    Write a markdown report summary.
    """
    config = get_config()
    output_path = Path(config.params['paths']['outputs'])
    report_file = output_path / f"monitoring_report_{date_str}.md"
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# RiskFusion Alpha Monitoring Report - {date_str}\n\n")
        f.write(f"**Run ID**: `{audit_id}`\n")
        f.write(f"**Status**: {validation_status}\n\n")
        
        f.write("## 1. Data Validation\n")
        if validation_status == "SUCCESS":
            f.write("✅ All Schema and Integrity checks passed.\n")
        else:
            f.write(f"❌ Validation Issues: {validation_status}\n")
            
        f.write("\n## 2. Drift Analysis (PSI)\n")
        if drift_metrics:
            f.write("| Feature | PSI |\n|---|---|\n")
            for feat, psi in drift_metrics.items():
                icon = "⚠️" if psi > 0.2 else "✅"
                f.write(f"| {feat} | {icon} {psi:.4f} |\n")
        else:
            f.write("No drift analysis performed.\n")
            
        f.write("\n## 3. Portfolio Summary\n")
        if not weights_df.empty:
            # ticker is the index, not a column
            top_ticker = weights_df.index[0]
            top_weight = weights_df.iloc[0]['weight']
            f.write(f"- **Top Position**: {top_ticker} ({top_weight:.2%})\n")
            f.write(f"- **Total Positions**: {len(weights_df)}\n")
            f.write(f"- **Concentration (Top 5)**: {weights_df['weight'].head(5).sum():.2%}\n")
        else:
            f.write("No weights produced.\n")
            
    logger.info(f"Monitoring report written to {report_file}")
