"""Hover crosshair manager."""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import QObject, Signal, Qt
import pyqtgraph as pg


class CrosshairManager(QObject):
    """Manages hover crosshair (vertical + horizontal dashed lines)."""

    hoverInfo = Signal(str)

    def __init__(self, plot: pg.PlotWidget):
        super().__init__()
        self._plot = plot

        self.v_line = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen("#aaaaaa", width=1, style=Qt.DashLine),
        )
        self.h_line = pg.InfiniteLine(
            angle=0, movable=False,
            pen=pg.mkPen("#aaaaaa", width=1, style=Qt.DashLine),
        )
        plot.addItem(self.v_line, ignoreBounds=True)
        plot.addItem(self.h_line, ignoreBounds=True)
        self.v_line.hide()
        self.h_line.hide()

        self._proxy = pg.SignalProxy(
            plot.scene().sigMouseMoved, rateLimit=60, slot=self._on_hover
        )

        self._channel_times: dict = {}
        self._channel_data: dict = {}
        self._channel_meta: dict = {}
        self._channel_visible: dict = {}

    def set_channel_data(self, key: str, t_valid, y_valid, meta: dict):
        """Register channel data for hover lookups."""
        self._channel_times[key] = t_valid
        self._channel_data[key] = y_valid
        self._channel_meta[key] = meta
        self._channel_visible[key] = True

    def remove_channel(self, key: str):
        for d in (self._channel_times, self._channel_data,
                  self._channel_meta, self._channel_visible):
            d.pop(key, None)

    def clear_channels(self):
        self._channel_times.clear()
        self._channel_data.clear()
        self._channel_meta.clear()
        self._channel_visible.clear()

    def set_visible(self, key: str, visible: bool):
        self._channel_visible[key] = visible

    def _on_hover(self, evt):
        pos = evt[0]
        vb = self._plot.getViewBox()
        if not vb.sceneBoundingRect().contains(pos):
            self.v_line.hide()
            self.h_line.hide()
            self.hoverInfo.emit("")
            return

        mouse_point = vb.mapSceneToView(pos)
        x = mouse_point.x()
        y = mouse_point.y()
        self.v_line.setPos(x)
        self.h_line.setPos(y)
        self.v_line.show()
        self.h_line.show()

        info = f"Time: {x:.6f}s"
        for key in self._channel_times:
            if not self._channel_visible.get(key, True):
                continue
            t_arr = self._channel_times.get(key)
            y_arr = self._channel_data.get(key)
            if t_arr is None or len(t_arr) == 0:
                continue
            idx = np.searchsorted(t_arr, x)
            if 0 <= idx < len(t_arr):
                val = y_arr[idx]
                meta = self._channel_meta.get(key, {})
                name = meta.get("description", meta.get("name", key))
                short = name[:30] + "..." if len(name) > 30 else name
                info += f"\n  {short}: {val:.6f}"
        self.hoverInfo.emit(info)
