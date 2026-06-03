"""FFT (Fast Fourier Transform) analysis for time-domain signals."""
from __future__ import annotations

import numpy as np

# Available window functions
_WINDOWS = {
    "hann": np.hanning,
    "hamming": np.hamming,
    "blackman": np.blackman,
    "rectangular": lambda n: np.ones(n),
}


def available_windows() -> list[str]:
    """Return list of available window function names."""
    return list(_WINDOWS.keys())


def compute_fft(
    time: np.ndarray,
    data: np.ndarray,
    t1: float,
    t2: float,
    window: str = "hann",
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """Compute single-sided FFT magnitude spectrum of data between t1 and t2.

    Args:
        time: Full time array.
        data: Full data array (may contain NaN).
        t1, t2: Cursor positions defining the analysis window.
        window: Window function name — 'hann', 'hamming', 'blackman', or 'rectangular'.

    Returns:
        (freqs, mag_linear, mag_db) arrays, or None if no valid data in window.
        freqs: Frequency bins in Hz (length = N//2 + 1).
        mag_linear: Normalized linear magnitude.
        mag_db: Magnitude in dB (20*log10), floor at -200 dB.
    """
    t_min, t_max = (t1, t2) if t1 <= t2 else (t2, t1)

    # Extract valid (non-NaN) data points
    valid = ~np.isnan(data)
    t_valid = time[valid]
    y_valid = data[valid]

    if len(t_valid) < 4:
        return None

    # Select points in window
    in_window = (t_valid >= t_min) & (t_valid <= t_max)
    t_win = t_valid[in_window]
    y_win = y_valid[in_window]

    if len(t_win) < 4:
        return None

    # Estimate uniform sample interval
    if len(t_win) > 1:
        dt = float(np.median(np.diff(t_win)))
    else:
        return None

    if dt <= 0:
        return None

    # Apply window function
    win_func = _WINDOWS.get(window, np.hanning)
    w = win_func(len(y_win))
    y_windowed = y_win * w

    # Real FFT (single-sided)
    n = len(y_windowed)
    fft_result = np.fft.rfft(y_windowed)
    freqs = np.fft.rfftfreq(n, d=dt)

    # Magnitude (normalized by window gain)
    win_gain = np.mean(w) if np.mean(w) > 0 else 1.0
    mag = np.abs(fft_result) / (n * win_gain)
    mag[1:] *= 2  # Double-side correction (except DC)

    # dB conversion with floor
    mag_db = 20 * np.log10(np.maximum(mag, 1e-10))

    return freqs, mag, mag_db
