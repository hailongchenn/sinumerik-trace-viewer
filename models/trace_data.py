"""TraceData — top-level container for parsed trace data."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import OrderedDict
import numpy as np


@dataclass
class TraceData:
    """Container for all data parsed from a trace file.

    Attributes:
        time: Shared time-axis array (numpy float64).
        signals: List of per-signal metadata dicts (as parsed from XML).
        channels: OrderedDict mapping signal key -> ChannelData.
        start_time: Capture start time string from frame header.
        stop_inc: Duration in seconds (stop increment).
    """

    time: np.ndarray = field(default_factory=lambda: np.array([]))
    signals: list[dict] = field(default_factory=list)
    channels: OrderedDict = field(default_factory=OrderedDict)
    start_time: str = ""
    stop_inc: float = 0.0
