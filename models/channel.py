"""Channel data models."""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class ChannelMetadata:
    """Metadata for a single channel/signal.

    Attributes:
        key: Unique signal key string.
        name: Short name.
        description: Human-readable description.
        color: Hex color string (#RRGGBB).
        data_type: Data type (float, int, etc.).
        units: Engineering units (mm, A, V, etc.).
        display_resolution: Number of decimal places.
        axis_side: 'leftSide' or 'rightSide'.
    """

    key: str = ""
    name: str = ""
    description: str = ""
    color: str = "#FFFFFF"
    data_type: str = "float"
    units: str = ""
    display_resolution: int = 5
    axis_side: str = "leftSide"


@dataclass
class ChannelData:
    """Data for a single channel.

    Attributes:
        data: Raw sample array (may contain NaN for missing values).
        meta: ChannelMetadata instance.
    """

    data: np.ndarray = field(default_factory=lambda: np.array([]))
    meta: ChannelMetadata = field(default_factory=ChannelMetadata)
