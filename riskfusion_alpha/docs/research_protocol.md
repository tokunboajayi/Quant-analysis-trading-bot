# Research Protocol

## 1. Goal
Ensure all research artifacts are reproducible, production-faithful, and free of look-ahead bias.

## 2. Leakage Prevention
- **Time Leakage**: Feature $t$ cannot use Price $t+1$. 
- **Universe Leakage**: Do not use "survivors only". Use ETF constituents or Point-in-Time universe lists.
- **Future PeekingCheck**: Run `val_suite.check_future_peeking` to detect correlation > 0.99.

## 3. Data Snapshotting
All research MUST run on immutable snapshots.
```bash
python -m riskfusion.cli snapshot create --desc "Baseline Features"
python -m riskfusion.cli snapshot list
```
Snapshot ID format: `YYYYMMDD_HHMMSS_<hash>`

## 4. Walk-Forward Evaluation
We use a sliding window approach for backtesting.
- **Train Window**: 3 Years (Initial)
- **Test Window**: 3 Months (Quarterly)
- **Step**: 1 Month

Run via:
```bash
python -m riskfusion.cli walkforward --start_days 750 --test_days 63
```

## 5. Experiment Tracking
Log all experiments locally to `data/experiments/`.
Use `riskfusion.research.experiment.ExperimentTracker`.

## 6. Backtest Checks
Before creating a candidate:
1.  Run Permutation Test (`validate_research command`): IC should drop to 0.
2.  Check for "Impossible Trades" (buying delisted stocks).
