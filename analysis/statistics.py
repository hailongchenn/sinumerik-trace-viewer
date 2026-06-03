"""Pure stateless statistics functions for waveform measurements."""
import numpy as np


def compute_statistics(
    time: np.ndarray, data: np.ndarray, t1: float, t2: float
) -> dict:
    """Compute RMS, avg, std, peak-peak, min, max for a time window.

    Args:
        time: Time array (full, may include NaN positions).
        data: Signal data array (full, may include NaN).
        t1, t2: Cursor positions defining the analysis window.

    Returns:
        Dict with keys: rms, avg, std, pp, min, max.
        Values are None if no valid data in the window.
    """
    t_min, t_max = (t1, t2) if t1 <= t2 else (t2, t1)
    valid_mask = ~np.isnan(data)
    t_valid = time[valid_mask]
    y_valid = data[valid_mask]

    if len(t_valid) == 0 or len(y_valid) == 0:
        return _empty_result()

    in_window = (t_valid >= t_min) & (t_valid <= t_max)
    y_win = y_valid[in_window]

    if len(y_win) == 0:
        return _empty_result()

    return {
        "rms": float(np.sqrt(np.mean(y_win ** 2))),
        "avg": float(np.mean(y_win)),
        "std": float(np.std(y_win)),
        "pp": float(np.max(y_win) - np.min(y_win)),
        "min": float(np.min(y_win)),
        "max": float(np.max(y_win)),
    }


def _empty_result() -> dict:
    return {"rms": None, "avg": None, "std": None, "pp": None, "min": None, "max": None}
