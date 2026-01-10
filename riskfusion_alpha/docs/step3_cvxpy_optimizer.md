# Step 3: CVXPY Portfolio Optimizer

## Overview

Replaces heuristic portfolio weighting with convex optimization using CVXPY.
Incorporates risk aversion, transaction costs, and constraints.

## Feature Flag

```yaml
# configs/default.yaml
optimizer:
  method: "heuristic"  # Set to "cvxpy" to enable
  risk_aversion: 1.0
  cost_bps: 5
  turnover_cap: 0.30
```

## What It Does

1. **Convex Objective**:
   ```
   maximize: α'w - λ·w'Σw - cost·||w - w_prev||₁
   ```
   - α'w: Expected alpha (maximize)
   - w'Σw: Portfolio variance (minimize)
   - ||w - w_prev||₁: Transaction cost (minimize)

2. **Constraints**:
   - Long-only: w ≥ 0
   - Max weight: w ≤ max_weight
   - Gross exposure: Σw ≤ 1
   - Turnover cap: ||w - w_prev||₁ ≤ turnover_cap

3. **Covariance Estimation**:
   - Ledoit-Wolf shrinkage (default)
   - Sample covariance (option)
   - Diagonal (fastest)

## Files Added

| File | Purpose |
|------|---------|
| `riskfusion/portfolio/optimizer_cvxpy.py` | CVXPY optimizer |
| `riskfusion/portfolio/covariance.py` | Covariance estimation |
| `tests/test_optimizer_cvxpy.py` | Unit tests |

## Dependencies

```bash
pip install cvxpy ecos
```

## How to Enable

```yaml
# configs/default.yaml
optimizer:
  method: "cvxpy"
  risk_aversion: 1.0
  cost_bps: 5
  turnover_cap: 0.30
```

## Expected Metrics Impact

| Metric | Expected Change |
|--------|-----------------|
| Risk-adjusted Return | Improved |
| Turnover | Controlled by cap |
| Transaction Cost | Reduced |

## Rollback

Set `optimizer.method: "heuristic"` to disable.

## Gates

- Feasible solution rate = 100%
- Turnover cap respected
- Volatility tracking improved
