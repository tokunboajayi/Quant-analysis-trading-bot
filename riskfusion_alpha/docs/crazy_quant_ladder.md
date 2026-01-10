# Crazy Quant Ladder

## Overview

7-step sequential upgrade path for RiskFusion Alpha with advanced quant ML modules.
Each step is behind a feature flag (OFF by default).

## Steps

| Step | Module | Flag | Status |
|------|--------|------|--------|
| 1 | [Distributional Alpha](step1_distributional_alpha.md) | `alpha.use_quantiles` | ✅ Implemented |
| 2 | [Meta-Labeler](step2_meta_labeler.md) | `meta.enabled` | ✅ Implemented |
| 3 | [CVXPY Optimizer](step3_cvxpy_optimizer.md) | `optimizer.method: cvxpy` | ✅ Implemented |
| 4 | [Graph/Cluster Caps](step4_graph_cluster.md) | `graph.enabled` | ✅ Implemented |
| 5 | [Multi-Task Event Risk](step5_event_multitask.md) | `event.multitask` | ✅ Implemented |
| 6 | [Regime Switching](step6_regime_switching.md) | `regime.enabled` | ✅ Implemented |
| 7 | [Online Learning](step7_online_learning.md) | `online_learning.enabled` | ✅ Implemented |

## How to Enable

Edit `configs/default.yaml` and set the desired flag to `true`.

## How to Compare (Ablation)

```bash
# Compare baseline vs Step 1
python -m riskfusion.cli ablation --steps 0,1 --start 2024-01-01 --end 2024-12-31

# Compare baseline vs Steps 1+2
python -m riskfusion.cli ablation --steps 0,1,2 --start 2024-01-01 --end 2024-12-31
```

## Rollback

Set all flags to `false` to return to baseline behavior.

## Gate Requirements

Each step must pass these gates before being "promoted":
- IC not degraded > 10%
- Max Drawdown not worse > 5%
- Turnover not increased > 20%
- No leakage detected
- Tests passing
