# Step 6: Regime Switching (Mixture of Experts)

## Overview

Detects market regimes and switches strategy parameters accordingly.
Defensive in stressed markets, aggressive in calm markets.

## Feature Flag

```yaml
# configs/default.yaml
regime:
  enabled: false  # Set to true to enable
  states: ["calm", "volatile", "stressed"]
  vol_threshold_volatile: 0.20
  vol_threshold_stressed: 0.35
```

## Regime Detection

Based on:
- **SPY Volatility**: Annualized realized vol
- **Correlation Spikes**: Average cross-asset correlation
- **Vol-of-Vol**: Volatility instability
- **Sector Dispersion**: Cross-sectional return spread

| Regime | Condition |
|--------|-----------|
| CALM | Vol < 20%, stable |
| VOLATILE | 20% < Vol < 35% |
| STRESSED | Vol > 35% OR correlation spike + vol instability |

## Parameter Switching

| Parameter | CALM | VOLATILE | STRESSED |
|-----------|------|----------|----------|
| Target Vol | 12% | 8% | 5% |
| Gross Exposure | 100% | 70% | 40% |
| Risk Aversion (λ) | 1.0 | 2.0 | 4.0 |
| Event Overlay α | 0.5 | 0.7 | 0.9 |
| Max Position | 10% | 7% | 5% |

## Files Added

| File | Purpose |
|------|---------|
| `riskfusion/models/regime_model.py` | Regime detection |
| `riskfusion/portfolio/strategy_selector.py` | Parameter switching |
| `tests/test_regime.py` | Unit tests |

## How to Enable

```yaml
# configs/default.yaml
regime:
  enabled: true
```

## Expected Metrics Impact

| Metric | Expected Change |
|--------|-----------------|
| Stressed-Period Drawdown | Reduced |
| Calm-Period Returns | Maintained/Improved |
| Fold Stability | Improved |

## Rollback

Set `regime.enabled: false` to disable.

## Gates

- Reduced drawdowns in stressed regimes
- Fold stability across regime transitions
