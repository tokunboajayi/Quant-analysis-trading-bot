"""
Normalization utilities for telemetry gauges
=============================================
"""
import numpy as np
from typing import List, Optional


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp value to range."""
    return max(min_val, min(max_val, value))


def robust_normalize(
    value: float,
    history: Optional[List[float]] = None,
    p_low: float = 10,
    p_high: float = 90,
    default_min: float = 0.0,
    default_max: float = 1.0
) -> float:
    """
    Robust normalization using percentiles of historical data.
    Falls back to min/max if insufficient history.
    """
    if history is None or len(history) < 10:
        # Fallback to simple normalization
        return clamp((value - default_min) / (default_max - default_min + 1e-8))
    
    arr = np.array(history)
    low = np.percentile(arr, p_low)
    high = np.percentile(arr, p_high)
    
    if high - low < 1e-8:
        return 0.5
    
    return clamp((value - low) / (high - low))


def linear_scale(value: float, in_min: float, in_max: float, 
                 out_min: float = 0.0, out_max: float = 1.0) -> float:
    """Linear scale from input range to output range."""
    if in_max - in_min < 1e-8:
        return out_min
    
    scaled = (value - in_min) / (in_max - in_min)
    return clamp(out_min + scaled * (out_max - out_min), out_min, out_max)


def sigmoid_normalize(value: float, center: float = 0.0, scale: float = 1.0) -> float:
    """Sigmoid normalization centered at 'center'."""
    return 1 / (1 + np.exp(-(value - center) / scale))
