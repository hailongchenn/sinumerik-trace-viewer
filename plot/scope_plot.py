"""OscilloscopePlot — single shared plot with overlaid channels."""
from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal

import pyqtgraph as pg

from models import TraceData
from plot.cursors import CursorManager
from plot.crosshair import CrosshairManager
from plot.curve_manager import CurveManager


class OscilloscopePlot(QWidget):
    """Main oscilloscope plot widget — all channels overlaid on one pg.PlotWidget."""

    cursorMoved = Signal()
    hoverValue = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Plot widget ---
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setMenuEnabled(False)
        self.plot.setMouseEnabled(x=True, y=True)
        self.plot.getAxis("left").setPen(pg.mkPen("#888888"))
        self.plot.getAxis("left").setTextPen(pg.mkPen("#cccccc"))
        self.plot.getAxis("bottom").setPen(pg.mkPen("#888888"))
        self.plot.getAxis("bottom").setTextPen(pg.mkPen("#cccccc"))
        self.plot.setLabel("bottom", "Time", units="s", color="#cccccc")
        layout.addWidget(self.plot)

        # --- Managers ---
        self._cursors = CursorManager(self.plot)
        self._cursors.positionChanged.connect(lambda: self.cursorMoved.emit())

        self._crosshair = CrosshairManager(self.plot)
        self._crosshair.hoverInfo.connect(self.hoverValue.emit)

        self._curves = CurveManager(self.plot)

        self._trace_data: TraceData | None = None

    # ------------------------------------------------------------------
    # Public API (same signatures as before for main_window compatibility)
    # ------------------------------------------------------------------

    def set_trace_data(self, td: TraceData):
        self._curves.clear()
        self._crosshair.clear_channels()
        self._trace_data = td

        if td.time is None or len(td.time) == 0:
            return

        t = td.time
        t_min, t_max = float(t[0]), float(t[-1])

        for key, ch in td.channels.items():
            meta = ch["meta"]
            color = meta.get("color", "FFFFFF")
            self._curves.add_curve(key, t, ch["data"], color, meta)
            t_valid, y_valid = self._curves._y_data.get(key, np.array([])), ch["data"]
            valid = ch["data"][~np.isnan(ch["data"])]
            self._crosshair.set_channel_data(
                key, t[~np.isnan(ch["data"])], valid, meta
            )

        self.plot.setXRange(t_min, t_max, padding=0.02)
        self._update_y_range()
        self._cursors.reset_to_default(t_min, t_max)

    def set_channel_visible(self, key: str, visible: bool):
        self._curves.set_visible(key, visible)
        self._crosshair.set_visible(key, visible)
        self._update_y_range()

    def get_cursor_values(self):
        if self._trace_data is None or self._trace_data.time is None:
            return None, None
        return self._cursors.get_values()

    def get_measurements(self) -> dict:
        if self._trace_data is None:
            return {}

        t1, t2 = self.get_cursor_values()
        if t1 is None:
            return {}

        t_min, t_max = (t1, t2) if t1 <= t2 else (t2, t1)
        results = {}

        for key in self._trace_data.channels:
            curve_keys = self._curves.curve_keys
            if key not in curve_keys:
                continue

            # Get valid (non-NaN) time & data from curve manager
            y_arr = self._curves._y_data.get(key)
            ch = self._trace_data.channels[key]
            data_full = ch["data"]
            time_full = self._trace_data.time
            valid_mask = ~np.isnan(data_full)
            t_arr = time_full[valid_mask]
            y_arr = data_full[valid_mask]

            meta = ch["meta"]
            name = meta.get("description", meta.get("name", key))
            units = meta.get("unitsType", "")
            visible = self._curves.is_visible(key)

            if len(t_arr) == 0:
                results[key] = self._empty_measurement(name, units, t1, t2, visible)
                continue

            mask = (t_arr >= t_min) & (t_arr <= t_max)
            valid = y_arr[mask]
            if len(valid) == 0:
                results[key] = self._empty_measurement(name, units, t1, t2, visible)
                continue

            results[key] = {
                "name": name,
                "units": units,
                "visible": visible,
                "t1": t1,
                "t2": t2,
                "delta": abs(t2 - t1),
                "rms": float(np.sqrt(np.mean(valid ** 2))),
                "avg": float(np.mean(valid)),
                "std": float(np.std(valid)),
                "pp": float(np.max(valid) - np.min(valid)),
                "min": float(np.min(valid)),
                "max": float(np.max(valid)),
            }
        return results

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _update_y_range(self):
        y_range = self._curves.compute_y_range()
        if y_range is not None:
            self.plot.setYRange(y_range[0], y_range[1], padding=0.05)

    @staticmethod
    def _empty_measurement(name, units, t1, t2, visible):
        return {
            "name": name, "units": units, "visible": visible,
            "t1": t1, "t2": t2, "delta": abs(t2 - t1),
            "rms": None, "avg": None, "std": None, "pp": None,
            "min": None, "max": None,
        }
