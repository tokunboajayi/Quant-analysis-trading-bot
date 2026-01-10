# Step 7: Online Learning + Drift-Aware Retraining

## Overview

Safely retrains models when signals justify it, with anti-loop protection.

## Feature Flag

```yaml
# configs/default.yaml
online_learning:
  enabled: false  # Set to true to enable
  drift_psi_threshold: 0.25
  var_breach_threshold: 0.10
  min_retrain_interval_days: 7
```

## Retrain Triggers

| Trigger | Condition |
|---------|-----------|
| Feature Drift | PSI > 0.25 |
| VaR Breach | Breach rate > 10% |
| IC Degradation | IC < 50% of baseline |

## Safety Mechanisms

1. **Minimum Interval**: No retrain within 7 days of last retrain
2. **Holdout Validation**: Candidate must pass on recent holdout
3. **Anti-Loop Protection**: Max 3 retrains per 14-day period
4. **Full Audit Trail**: All decisions logged

## Retrain Flow

```
Drift Detected → Check Interval → Check Anti-Loop
                       ↓
              Train Candidate Model
                       ↓
              Evaluate on Holdout
                       ↓
           IC > 0.02? → PROMOTE
                       ↓
                 Log Decision
```

## Files Added

| File | Purpose |
|------|---------|
| `riskfusion/research/online_learning.py` | Online learning manager |
| `tests/test_online_learning.py` | Unit tests |

## How to Enable

```yaml
# configs/default.yaml
online_learning:
  enabled: true
```

## Outputs

- `data/outputs/online_learning_state.json`: Persisted state
- `data/outputs/retrain_log.jsonl`: Decision audit log

## Expected Metrics Impact

| Metric | Expected Change |
|--------|-----------------|
| Model Freshness | Improved |
| Drift Recovery Time | Faster |
| Stability | Maintained (via gates) |

## Rollback

Set `online_learning.enabled: false` to disable.

## Gates

- Retrain frequency stable (not exceeding limits)
- Post-retrain IC maintained
- No catastrophic degradation
