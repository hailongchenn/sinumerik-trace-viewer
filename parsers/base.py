"""Abstract base class for trace file parsers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from models import TraceData


class BaseParser(ABC):
    """Interface for parsers that produce TraceData from files."""

    @abstractmethod
    def parse(self, filepath: str) -> TraceData:
        """Parse a file and return a TraceData instance."""

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return the list of file extensions this parser handles (e.g. ['.xml'])."""
