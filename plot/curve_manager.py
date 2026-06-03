"""Curve manager — handles per-channel PlotDataItem CRUD and Y-range."""
from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from utils import color_to_tuple


class CurveManager:
    """Manages pg.PlotDataItem curves on a PlotWidget."""

    def __init__(self, plot: pg.PlotWidget):
        self._plot = plot
        self._curves: dict[str, pg.PlotDataItem] = {}
        self._visible: dict[str, bool] = {}
        self._y_data: dict[str, np.ndarray] = {}  # valid (non-NaN) arrays

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_curve(self, key: str, time: np.ndarray, data: np.ndarray,
                  color: str, meta: dict) -> pg.PlotDataItem:
        """Create and add a PlotDataItem for one channel."""
        # Remove existing curve if re-adding
        self.remove_curve(key)

        color_tuple = color_to_tuple(color)
        pen = pg.mkPen(color=color_tuple, width=1.5)

        valid_mask = ~np.isnan(data)
        t_valid = time[valid_mask]
        y_valid = data[valid_mask]

        curve = pg.PlotDataItem(t_valid, y_valid, pen=pen, connect="finite")
        self._plot.addItem(curve)
        self._curves[key] = curve
        self._visible[key] = True
        self._y_data[key] = y_valid
        return curve

    def remove_curve(self, key: str):
        """Remove a curve from the plot."""
        curve = self._curves.pop(key, None)
        if curve is not None:
            self._plot.removeItem(curve)
        self._visible.pop(key, None)
        self._y_data.pop(key, None)

    def clear(self):
        for curve in list(self._curves.values()):
            self._plot.removeItem(curve)
        self._curves.clear()
        self._visible.clear()
        self._y_data.clear()

    def set_visible(self, key: str, visible: bool):
        if key in self._curves:
            self._curves[key].setVisible(visible)
            self._visible[key] = visible

    def is_visible(self, key: str) -> bool:
        return self._visible.get(key, True)

    @property
    def curve_keys(self) -> list[str]:
        return list(self._curves.keys())

    # ------------------------------------------------------------------
    # Y-range computation
    # ------------------------------------------------------------------

    def compute_y_range(self) -> tuple[float, float] | None:
        """Compute (y_min, y_max) covering all visible curves. Returns None if none visible."""
        y_min = float("inf")
        y_max = float("-inf")
        has_visible = False

        for key, y_arr in self._y_data.items():
            if not self._visible.get(key, True) or len(y_arr) == 0:
                continue
            has_visible = True
            y_min = min(y_min, float(np.min(y_arr)))
            y_max = max(y_max, float(np.max(y_arr)))

        if not has_visible:
            return None
        margin = (y_max - y_min) * 0.1 if y_max != y_min else 1.0
        return (y_min - margin, y_max + margin)
