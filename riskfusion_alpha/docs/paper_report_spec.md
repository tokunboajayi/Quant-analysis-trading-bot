# Automated Paper Report Specification

## Overview
The `report_paper` command generates a publication-ready Markdown report (and plots) from a backtest run.

## Usage
```bash
python -m riskfusion.cli report_paper --run_id <RUN_ID> --snapshot_id <SNAP_ID>
```

## Inputs
- **Run ID**: Identifier for the backtest/walkforward result.
- **Snapshot ID**: Data version used.
- **Backtest Results**: Expected to be in `data/outputs/predictions.parquet` or similar (currently loading mock or CLI provided df).

## Outputs
Location: `data/outputs/reports/<RUN_ID>/`
- `report.md`: Full text report.
- `figures/*.png`:
  - Equity Curve
  - Drawdown
  - Rolling Volatility

## Report Sections
1.  **Abstract**: Summary of run.
2.  **Data**: Universe, Missingness, Survivorship.
3.  **Feature Engineering**: Definitions.
4.  **Models**: Type, Hyperparams.
5.  **Portfolio**: Optimization settings.
6.  **Protocol**: Execution lag, costs.
7.  **Results**: Metrics table + Plots.
8.  **Ablation**: Component analysis.
9.  **Risk**: Compliance checks.
10. **Limitations**: Free data caveats.
11. **Appendix**: Reproducibility hashes.

## Extension
To add PDF support, install `weasyprint` and add a conversion step in `riskfusion/reporting/paper.py`.
