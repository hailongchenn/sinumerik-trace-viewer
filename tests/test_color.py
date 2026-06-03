"""Tests for color utilities."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import parse_color, color_to_tuple


def test_parse_color_8char():
    """SINUMERIK 8-char colors: AARRGGBB → #RRGGBB."""
    assert parse_color("00ff0000") == "#ff0000"
    assert parse_color("0000ff00") == "#00ff00"
    assert parse_color("000000ff") == "#0000ff"


def test_parse_color_6char():
    """6-char colors pass through as #RRGGBB."""
    assert parse_color("ff0000") == "#ff0000"
    assert parse_color("ffffff") == "#ffffff"


def test_color_to_tuple():
    """Convert color string to (r, g, b, a) tuple."""
    result = color_to_tuple("00ff0000")
    assert result == (255, 0, 0, 255), f"Expected (255,0,0,255), got {result}"

    result = color_to_tuple("0000ff00")
    assert result == (0, 255, 0, 255)


if __name__ == "__main__":
    test_parse_color_8char()
    test_parse_color_6char()
    test_color_to_tuple()
    print("All color tests passed!")
