"""Measurement table with per-channel visibility checkboxes and FFT context menu."""
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QCheckBox, QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QAction

from utils import parse_color


class MeasurementTable(QTableWidget):
    """Bottom table showing per-channel statistics with colored visibility toggles."""

    visibilityChanged = Signal(str, bool)
    fftRequested = Signal(str)

    COL_VISIBLE = 0
    COL_CHANNEL = 1
    COL_UNIT = 2
    COL_T1 = 3
    COL_T2 = 4
    COL_DELTA = 5
    COL_RMS = 6
    COL_AVG = 7
    COL_STD = 8
    COL_PP = 9
    COL_MIN = 10
    COL_MAX = 11

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(12)
        self.setHorizontalHeaderLabels([
            "", "Channel", "Unit", "T1", "T2", "Delta", "RMS",
            "Average", "Std. Dev.", "Peak-Peak", "Min", "Max",
        ])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.setColumnWidth(0, 32)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultSectionSize(90)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setVisible(False)
        self.setStyleSheet("""
            QTableWidget { background-color: #1e1e1e; color: #eeeeee; gridline-color: #444444;
                           border: none; alternate-background-color: #252525; }
            QHeaderView::section { background-color: #333333; color: #eeeeee; padding: 4px;
                                   border: 1px solid #444444; font-weight: bold; }
            QTableWidget::item { padding: 2px 6px; }
        """)
        self.setAlternatingRowColors(True)

        self._channel_keys: list[str] = []
        self._channel_meta: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_channels(self, signals: list, channels_data: dict):
        """Create persistent rows for all channels with colored visibility checkboxes."""
        self._channel_keys = []
        self._channel_meta = {}
        self.setRowCount(0)

        for sig in signals:
            key = sig.get("key", "")
            name = sig.get("description", sig.get("name", key))
            color = parse_color(sig.get("color", "FFFFFF"))
            self._channel_keys.append(key)
            self._channel_meta[key] = {"name": name, "color": color}

        self.setRowCount(len(self._channel_keys))

        for row, key in enumerate(self._channel_keys):
            meta = self._channel_meta[key]
            color = meta["color"]

            # Colored visibility checkbox
            cb = QCheckBox()
            cb.setChecked(True)
            cb.setStyleSheet(f"QCheckBox {{ margin-left: 6px; }}")
            cb.stateChanged.connect(
                lambda state, k=key: self.visibilityChanged.emit(k, bool(state))
            )
            self.setCellWidget(row, self.COL_VISIBLE, cb)

            # Channel name — colored
            name_item = QTableWidgetItem(meta["name"])
            name_item.setForeground(QColor(color))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, self.COL_CHANNEL, name_item)

            # Placeholder "—" for measurement columns
            for col in range(self.COL_UNIT, self.COL_MAX + 1):
                item = QTableWidgetItem("—")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item.setForeground(QColor("#666666"))
                self.setItem(row, col, item)

        self.resizeColumnToContents(self.COL_CHANNEL)

    def update_measurements(self, measurements: dict):
        """Update measurement values for existing rows. Rows not in measurements stay '—'."""
        for row, key in enumerate(self._channel_keys):
            m = measurements.get(key)
            # Update name item color based on visibility
            name_item = self.item(row, self.COL_CHANNEL)
            if name_item:
                color = QColor(self._channel_meta[key]["color"])
                if m and not m.get("visible", True):
                    color.setAlpha(80)
                name_item.setForeground(color)

            if m is None:
                continue

            fmt = lambda v: f"{v:.6f}" if v is not None else "—"
            dim_color = QColor("#666666") if not m.get("visible", True) else QColor("#eeeeee")

            for col, value in [
                (self.COL_UNIT,  m.get("units", "")),
                (self.COL_T1,    fmt(m.get("t1"))),
                (self.COL_T2,    fmt(m.get("t2"))),
                (self.COL_DELTA, fmt(m.get("delta"))),
                (self.COL_RMS,   fmt(m.get("rms"))),
                (self.COL_AVG,   fmt(m.get("avg"))),
                (self.COL_STD,   fmt(m.get("std"))),
                (self.COL_PP,    fmt(m.get("pp"))),
                (self.COL_MIN,   fmt(m.get("min"))),
                (self.COL_MAX,   fmt(m.get("max"))),
            ]:
                item = self.item(row, col)
                if item is None:
                    item = QTableWidgetItem()
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.setItem(row, col, item)
                item.setText(value)
                item.setForeground(dim_color)

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def contextMenuEvent(self, event):
        """Right-click on a channel name row → show FFT / visibility options."""
        item = self.itemAt(event.pos())
        if item is None:
            return

        row = item.row()
        if row < 0 or row >= len(self._channel_keys):
            return

        key = self._channel_keys[row]
        meta = self._channel_meta.get(key, {})
        channel_name = meta.get("name", key)

        menu = QMenu(self)

        fft_action = QAction(f"Compute FFT — {channel_name}", self)
        fft_action.triggered.connect(lambda: self.fftRequested.emit(key))
        menu.addAction(fft_action)

        menu.exec(event.globalPos())
