# Leakage Prevention Playbook

## Taxonomy of Leakage

### 1. Time Leakage
**Definition**: Using information from $T+1$ to predict $T+1$.
**Examples**: 
- Normalizing features with full-history mean/std.
- Using "Next Day Open" as "Today's Close".
- Using News Timestamp > Market Close.
**Fix**:
- Use `LeakageDetector.check_time_leakage`.
- Strict cutoffs for event data.

### 2. Universe Leakage (Survivorship Bias)
**Definition**: Backtesting only on stocks that exist *today*.
**Impact**: Massively inflated returns (ignoring bankruptcies).
**Fix**:
- Use historical index constituents.
- If data unavailable, use strict liquidity filters and acknowledge bias.

### 3. Look-Ahead Bias (Peeking)
**Definition**: Subtle indexing errors where row $i$ accesses row $i+1$.
**Detection**:
- `ValidationSuite.permutation_test`: If permuted labels still give non-zero IC, there is structural leakage.

## Checklist before PR
- [ ] Ran `validate_research`?
- [ ] Created Snapshot?
- [ ] Checked for Global Z-Scoring?
