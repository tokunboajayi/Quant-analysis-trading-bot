# Step 1: Distributional Alpha (Quantile Models)

## Overview

Replaces single-point alpha prediction with distributional (quantile) predictions for forward 5D returns.

## Feature Flag

```yaml
# configs/default.yaml
alpha:
  use_quantiles: false  # Set to true to enable
  quantiles: [0.1, 0.5, 0.9]
  quality_formula: "q50_over_abs_q10"
```

## What It Does

1. **Trains 3 LightGBM Quantile Regressors**:
   - `q10`: 10th percentile (downside estimate)
   - `q50`: Median (expected return)
   - `q90`: 90th percentile (upside potential)

2. **Enforces Monotonicity**:
   - After prediction, ensures `q10 <= q50 <= q90`
   - Fixes violations via sorting

3. **Computes Quality Score**:
   ```
   score = q50 / (|q10| + epsilon)
   ```
   Higher score = better upside/downside ratio

4. **Portfolio Ranking**:
   - When enabled, ranks stocks by `quantile_score` instead of raw alpha

## Files Added

| File | Purpose |
|------|---------|
| `riskfusion/models/alpha_quantiles.py` | Quantile model training and prediction |
| `tests/test_alpha_quantiles.py` | Unit tests for monotonicity, scoring |

## How to Enable

```yaml
# configs/default.yaml
alpha:
  use_quantiles: true
```

## How to Run

```bash
# Train with quantiles enabled
python -m riskfusion.cli train

# Backtest
python -m riskfusion.cli backtest --start 2024-01-01 --end 2024-12-31

# Compare baseline vs Step 1
python -m riskfusion.cli ablation --steps 0,1 --start 2024-01-01 --end 2024-12-31
```

## Expected Metrics Impact

| Metric | Expected Change |
|--------|-----------------|
| IC | Similar or slightly better |
| Max Drawdown | Reduced (better tail awareness) |
| Turnover | Similar |

## Rollback

Set `alpha.use_quantiles: false` to revert to baseline behavior.

## Gates

- IC ≥ baseline - 10%
- Max DD ≥ baseline + 5%
- Monotonicity violation < 1%
