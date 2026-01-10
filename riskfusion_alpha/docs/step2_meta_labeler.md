# Step 2: Meta-Labeler (Trade Filter)

## Overview

Adds a meta-model that predicts whether to act on an alpha signal.
Improves precision by filtering out low-confidence trades.

## Feature Flag

```yaml
# configs/default.yaml
meta:
  enabled: false  # Set to true to enable
  threshold: 0.55
  apply_as_multiplier: true  # or false for hard filter
```

## What It Does

1. **Creates Meta-Labels**:
   - Labels historical alpha predictions as "good" or "bad"
   - Good = alpha direction matched return direction

2. **Trains Meta-Classifier**:
   - LightGBM binary classifier
   - Predicts P(good_trade | features)
   - Uses both base features + meta-specific features

3. **Filters Trades**:
   - **Multiplier mode**: `weight = weight × meta_prob`
   - **Filter mode**: Drop trades where `meta_prob < threshold`

## Files Added

| File | Purpose |
|------|---------|
| `riskfusion/labeling/meta_labels.py` | Meta-label creation logic |
| `riskfusion/models/meta_labeler.py` | Meta-Labeler model |
| `tests/test_meta_labeler.py` | Unit tests |

## Meta-Specific Features

- **vol_regime**: Volatility quintile (high vol = uncertain)
- **momentum_consistency**: Do 1d/5d/20d returns agree?
- **rsi_extreme**: Is RSI overbought/oversold?
- **consensus_strength**: How extreme is the alpha signal?

## How to Enable

```yaml
# configs/default.yaml
meta:
  enabled: true
  threshold: 0.55
  apply_as_multiplier: true
```

## Expected Metrics Impact

| Metric | Expected Change |
|--------|-----------------|
| AUC | > 0.55 (target) |
| Turnover | Reduced (fewer trades) |
| Drawdown | Reduced (fewer bad trades) |

## Rollback

Set `meta.enabled: false` to disable.

## Gates

- AUC > 0.55
- Turnover <= baseline + 10%
- Worst-fold drawdown improved or stable
