# Step 5: Multi-Task Event Risk

## Overview

Upgrades event risk from single binary output to multi-task predictions:
- P(high impact)
- P(negative direction)  
- Magnitude bucket (small/medium/large)

## Feature Flag

```yaml
# configs/default.yaml
event:
  multitask: false  # Set to true to enable
  predict_direction: true
  predict_magnitude: true
```

## What It Does

1. **Three Prediction Tasks**:
   - **Impact**: P(|return| > 2%)
   - **Direction**: P(return < 0)
   - **Magnitude**: 0=small, 1=medium (2-5%), 2=large (>5%)

2. **Combined Risk Score**:
   ```
   combined_risk = P(high_impact) × P(negative)
   ```
   - Only cuts exposure for impactful + negative events
   - Preserves exposure for positive catalysts

3. **Enhanced Overlay**:
   - Uses combined_risk for smarter position cuts
   - Records `EVENT_OVERLAY_*` reason codes

## Files Added

| File | Purpose |
|------|---------|
| `riskfusion/models/event_risk_multitask.py` | Multi-task model |
| `tests/test_event_multitask.py` | Unit tests |

## How to Enable

```yaml
# configs/default.yaml
event:
  multitask: true
```

## Expected Metrics Impact

| Metric | Expected Change |
|--------|-----------------|
| False Positive Rate | Reduced (fewer cuts on positive news) |
| Worst Daily Drawdowns | Reduced |
| Negative Event Precision | Improved |

## Rollback

Set `event.multitask: false` to use original binary model.

## Gates

- Precision on negative high-impact events > 50%
- Reduction in worst daily drawdowns
