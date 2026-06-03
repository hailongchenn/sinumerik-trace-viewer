"""Color parsing utilities for SINUMERIK trace XML."""


def parse_color(color_str: str) -> str:
    """Parse a SINUMERIK color string to a standard hex color.

    Handles 8-char format ('00ff0000') and 6-char format ('ff0000').
    Returns '#RRGGBB'.
    """
    color_str = color_str.strip()
    if len(color_str) == 8:
        # SINUMERIK uses AARRGGBB — drop the alpha channel (first 2 hex chars)
        return f"#{color_str[2:4]}{color_str[4:6]}{color_str[6:8]}"
    elif len(color_str) == 6:
        return f"#{color_str}"
    return color_str


def color_to_tuple(color_str: str) -> tuple:
    """Convert a color string to an (r, g, b, a) tuple for pyqtgraph."""
    hex_color = parse_color(color_str)
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, 255)
