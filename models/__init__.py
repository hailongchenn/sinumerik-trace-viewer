"""Data models for the Industrial Oscilloscope."""

from .trace_data import TraceData
from .channel import ChannelData, ChannelMetadata

__all__ = ["TraceData", "ChannelData", "ChannelMetadata"]
