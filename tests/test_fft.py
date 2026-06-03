"""Tests for FFT computation."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.fft import compute_fft, available_windows


def test_available_windows():
    """Verify all expected window functions are available."""
    windows = available_windows()
    assert "hann" in windows
    assert "hamming" in windows
    assert "blackman" in windows
    assert "rectangular" in windows
    print("OK: All window functions available")


def test_fft_50hz_sine():
    """FFT of a 50 Hz sine wave should peak at exactly 50 Hz."""
    fs = 1000.0  # Sample rate
    t = np.arange(0, 1.0, 1.0 / fs)
    y = np.sin(2 * np.pi * 50.0 * t)  # 50 Hz sine, amplitude 1

    result = compute_fft(t, y, 0.0, 1.0, window="hann")
    assert result is not None, "FFT should not return None"
    freqs, mag, mag_db = result

    # Find peak frequency
    peak_idx = np.argmax(mag)
    peak_freq = freqs[peak_idx]

    # Should be very close to 50 Hz (within bin resolution)
    assert abs(peak_freq - 50.0) < 2.0, f"Expected peak at 50 Hz, got {peak_freq:.2f} Hz"
    print(f"OK: 50 Hz sine → peak at {peak_freq:.2f} Hz, mag_db={mag_db[peak_idx]:.1f} dB")


def test_fft_two_sines():
    """FFT of two sines (50 Hz + 120 Hz)."""
    fs = 2000.0
    t = np.arange(0, 1.0, 1.0 / fs)  # 1 second for better resolution
    y = np.sin(2 * np.pi * 50.0 * t) + 0.5 * np.sin(2 * np.pi * 120.0 * t)

    result = compute_fft(t, y, 0.0, 1.0, window="hann")
    assert result is not None
    freqs, mag, _ = result

    # Find peaks in distinct frequency bands (skip DC, skip nearby bins)
    # Look for peaks above threshold, separated by >10 Hz
    threshold = 0.1
    above = mag > threshold
    peaks = []
    i = 1  # skip DC
    while i < len(freqs) - 1:
        if above[i] and mag[i] > mag[i-1] and mag[i] > mag[i+1]:
            peaks.append(freqs[i])
            i += 10  # skip nearby bins
        i += 1
    peaks = sorted(peaks[:2])  # top 2 distinct peaks

    assert abs(peaks[0] - 50.0) < 3.0, f"Expected 50 Hz, got {peaks[0]:.1f}"
    assert abs(peaks[1] - 120.0) < 3.0, f"Expected 120 Hz, got {peaks[1]:.1f}"
    print(f"OK: Two sines → peaks at {peaks[0]:.1f} Hz and {peaks[1]:.1f} Hz")


def test_fft_empty_window():
    """FFT with cursor region outside data should return None."""
    t = np.array([0.0, 1.0, 2.0])
    y = np.array([1.0, 2.0, 3.0])
    result = compute_fft(t, y, 100.0, 200.0)
    assert result is None
    print("OK: Empty window returns None")


def test_fft_nan_handling():
    """NaN values should be excluded before FFT."""
    fs = 1000.0
    t = np.arange(0, 0.2, 1.0 / fs)
    y = np.sin(2 * np.pi * 50.0 * t).copy()
    y[50] = np.nan  # Inject NaN

    result = compute_fft(t, y, 0.0, 0.2, window="hann")
    assert result is not None, "Should handle NaN gracefully"
    freqs, mag, _ = result
    peak_idx = np.argmax(mag)
    assert abs(freqs[peak_idx] - 50.0) < 5.0
    print("OK: NaN handling works correctly")


if __name__ == "__main__":
    test_available_windows()
    test_fft_50hz_sine()
    test_fft_two_sines()
    test_fft_empty_window()
    test_fft_nan_handling()
    print("\nAll FFT tests passed!")
