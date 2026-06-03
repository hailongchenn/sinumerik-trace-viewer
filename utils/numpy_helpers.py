"""NumPy helper functions for nan-aware signal processing."""
import numpy as np


def extract_valid(time: np.ndarray, data: np.ndarray):
    """Return (t_valid, y_valid) arrays with NaN values removed."""
    valid_mask = ~np.isnan(data)
    return time[valid_mask], data[valid_mask]


def mask_range(time: np.ndarray, t1: float, t2: float) -> np.ndarray:
    """Return a boolean mask for time values between t1 and t2 (inclusive)."""
    t_min, t_max = (t1, t2) if t1 <= t2 else (t2, t1)
    return (time >= t_min) & (time <= t_max)


def safe_range(data: np.ndarray):
    """Return (min, max) of array, ignoring NaN. Returns (0, 0) for all-NaN."""
    valid = data[~np.isnan(data)]
    if len(valid) == 0:
        return 0.0, 0.0
    return float(np.min(valid)), float(np.max(valid))
