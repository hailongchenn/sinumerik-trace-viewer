"""Tests for statistics computation."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.statistics import compute_statistics


def test_basic_statistics():
    """Test statistics on a simple known signal."""
    time = np.linspace(0, 10, 1000)
    data = np.sin(2 * np.pi * 1.0 * time)  # 1 Hz sine wave, amplitude 1

    result = compute_statistics(time, data, 0.0, 10.0)

    # For a full sine wave cycle, RMS should be ~0.707 (1/√2)
    assert result["rms"] is not None
    assert abs(result["rms"] - 0.7071) < 0.01, f"Expected RMS ~0.707, got {result['rms']}"
    assert abs(result["avg"]) < 0.05, f"Expected avg ~0, got {result['avg']}"
    assert abs(result["pp"] - 2.0) < 0.01, f"Expected pp ~2.0, got {result['pp']}"
    print(f"OK: RMS={result['rms']:.4f}, avg={result['avg']:.4f}, pp={result['pp']:.4f}")


def test_empty_window():
    """Test statistics with no data in the window."""
    time = np.array([1.0, 2.0, 3.0])
    data = np.array([10.0, 20.0, 30.0])

    result = compute_statistics(time, data, 100.0, 200.0)  # Outside data range
    assert result["rms"] is None
    assert result["avg"] is None
    print("OK: Empty window returns None values")


def test_nan_handling():
    """Test that NaN values are properly excluded."""
    time = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    data = np.array([1.0, np.nan, 3.0, np.nan, 5.0])

    result = compute_statistics(time, data, 0.0, 4.0)
    assert result["avg"] == 3.0, f"Expected avg=3.0, got {result['avg']}"
    print("OK: NaN values excluded correctly")


if __name__ == "__main__":
    test_basic_statistics()
    test_empty_window()
    test_nan_handling()
    print("\nAll statistics tests passed!")
