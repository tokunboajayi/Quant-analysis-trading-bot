# Step 4: Graph/Cluster Risk Caps

## Overview

Controls hidden correlation concentration by clustering the universe
and capping exposure per cluster.

## Feature Flag

```yaml
# configs/default.yaml
graph:
  enabled: false  # Set to true to enable
  correlation_window: 60
  max_cluster_exposure: 0.25
  clustering_method: "hierarchical"  # or "spectral"
```

## What It Does

1. **Computes Correlation Matrix**:
   - Rolling 60-day correlations between all assets

2. **Clusters Assets**:
   - Hierarchical clustering (default)
   - Groups correlated assets together

3. **Caps Cluster Exposure**:
   - Limits total weight per cluster to `max_cluster_exposure`
   - Scales down weights in overexposed clusters

4. **Produces Features**:
   - `cluster_id`: Which cluster each ticker belongs to
   - `centrality`: How connected each ticker is
   - `avg_correlation`: Average correlation with others

## Files Added

| File | Purpose |
|------|---------|
| `riskfusion/features/graph_features.py` | Clustering and centrality |
| `riskfusion/portfolio/cluster_caps.py` | Exposure cap enforcement |
| `tests/test_graph_cluster.py` | Unit tests |

## How to Enable

```yaml
# configs/default.yaml
graph:
  enabled: true
  max_cluster_exposure: 0.25
```

## Expected Metrics Impact

| Metric | Expected Change |
|--------|-----------------|
| Concentration Index | Reduced |
| Stress-period Drawdown | Reduced |
| Diversification | Improved |

## Rollback

Set `graph.enabled: false` to disable.

## Gates

- Cluster concentration index improved
- Worst stress-period drawdown reduced
