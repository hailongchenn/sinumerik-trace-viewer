"""Cursor manager for T1/T2 draggable vertical cursors."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal
import pyqtgraph as pg


class CursorManager(QObject):
    """Manages two draggable InfiniteLine cursors on a PlotWidget."""

    positionChanged = Signal()  # emitted on any cursor move

    def __init__(self, plot: pg.PlotWidget):
        super().__init__()
        self._plot = plot

        self.cursor1 = pg.InfiniteLine(
            angle=90, movable=True, pen=pg.mkPen("#ff5555", width=2),
            label="T1", labelOpts={"position": 0.02, "color": "#ff5555",
                                   "fill": (80, 0, 0, 180), "movable": True},
        )
        self.cursor2 = pg.InfiniteLine(
            angle=90, movable=True, pen=pg.mkPen("#55ffff", width=2),
            label="T2", labelOpts={"position": 0.98, "color": "#55ffff",
                                   "fill": (0, 80, 80, 180), "movable": True},
        )
        plot.addItem(self.cursor1)
        plot.addItem(self.cursor2)
        self.cursor1.sigPositionChanged.connect(self._on_moved)
        self.cursor2.sigPositionChanged.connect(self._on_moved)

    def _on_moved(self):
        self.positionChanged.emit()

    def get_values(self):
        """Return (t1, t2) cursor positions, or (None, None)."""
        try:
            return self.cursor1.value(), self.cursor2.value()
        except Exception:
            return None, None

    def reset_to_default(self, t_min: float, t_max: float):
        """Position cursors at 10% and 90% of the time range."""
        span = t_max - t_min
        self.cursor1.setValue(t_min + span * 0.1)
        self.cursor2.setValue(t_min + span * 0.9)
