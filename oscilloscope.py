#!/usr/bin/env python3
"""
Industrial Oscilloscope - SINUMERIK Trace File Viewer
Reads Siemens SINUMERIK Solution Line Trace XML files and displays waveforms.
Single plot: all channels overlaid with shared Y-axis auto-scaled to visible data.
"""

import sys
import xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
from collections import OrderedDict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QSplitter,
    QHeaderView, QAbstractItemView, QCheckBox, QFileDialog,
    QToolBar, QStatusBar,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QAction, QKeySequence

import pyqtgraph as pg

pg.setConfigOptions(antialias=True, useOpenGL=False)


# ---------------------------------------------------------------------------
# Color utilities
# ---------------------------------------------------------------------------
def parse_color(color_str: str) -> str:
    """Parse SINUMERIK color string (e.g., '00ff0000') to #RRGGBB."""
    color_str = color_str.strip()
    if len(color_str) == 8:
        return f"#{color_str[2:4]}{color_str[4:6]}{color_str[6:8]}"
    elif len(color_str) == 6:
        return f"#{color_str}"
    return color_str


def color_to_tuple(color_str: str) -> tuple:
    """Return (r, g, b, a) tuple for pyqtgraph."""
    hex_color = parse_color(color_str)
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, 255)


# ---------------------------------------------------------------------------
# XML Parser
# ---------------------------------------------------------------------------
class TraceData:
    def __init__(self):
        self.signals = []
        self.time = None
        self.channels = OrderedDict()
        self.start_time = ""
        self.stop_inc = 0.0


class XmlTraceParser:
    def parse(self, filepath: str) -> TraceData:
        tree = ET.parse(filepath)
        root = tree.getroot()

        td = TraceData()

        display_setup = root.find("traceDisplaySetup")
        if display_setup is None:
            display_setup = root.find("traceDisplaySetup_V20")

        signal_meta = {}
        if display_setup is not None:
            signals_elem = display_setup.find("signals")
            if signals_elem is not None:
                for sig in signals_elem.findall("signal"):
                    key = sig.get("key")
                    signal_meta[key] = {
                        "key": key,
                        "name": sig.get("name", ""),
                        "description": sig.get("description", ""),
                        "color": sig.get("color", "FFFFFF"),
                        "dataType": sig.get("dataType", "float"),
                        "unitsType": sig.get("unitsType", ""),
                        "waveformKey": sig.get("waveformKey", ""),
                        "axisDisplay": sig.get("axisDisplay", "leftSide"),
                        "displayRes": int(sig.get("displayRes", "5")),
                    }

        trace_data = root.find("traceData")
        if trace_data is None:
            raise ValueError("No <traceData> found in XML")

        data_frame = trace_data.find("dataFrame")
        if data_frame is None:
            raise ValueError("No <dataFrame> found in XML")

        frame_header = data_frame.find("frameHeader")
        if frame_header is not None:
            td.start_time = frame_header.get("startTime", "")
            td.stop_inc = float(frame_header.get("stopInc", "0"))

        data_signals = {}
        for ds in data_frame.findall("dataSignal"):
            fid = ds.get("id")
            key = ds.get("key")
            data_signals[fid] = {
                "id": fid,
                "key": key,
                "name": ds.get("name", ""),
                "description": ds.get("description", ""),
                "interval": float(ds.get("interval", "0.002")),
                "datapointCount": int(ds.get("datapointCount", "0")),
                "dataType": ds.get("dataType", "float"),
                "unitsType": ds.get("unitsType", ""),
            }
            if key in signal_meta:
                data_signals[fid].update({
                    "color": signal_meta[key].get("color", "FFFFFF"),
                    "displayRes": signal_meta[key].get("displayRes", 5),
                    "axisDisplay": signal_meta[key].get("axisDisplay", "leftSide"),
                })
            else:
                data_signals[fid]["color"] = "FFFFFF"
                data_signals[fid]["displayRes"] = 5
                data_signals[fid]["axisDisplay"] = "leftSide"

        recs = data_frame.findall("rec")
        n = len(recs)

        time_vals = np.zeros(n, dtype=np.float64)
        field_values = {fid: np.full(n, np.nan, dtype=np.float64)
                        for fid in data_signals}

        for i, rec in enumerate(recs):
            t = float(rec.get("time", "0"))
            time_vals[i] = t
            for fid in data_signals:
                val_str = rec.get(fid)
                if val_str is not None:
                    try:
                        field_values[fid][i] = float(val_str)
                    except ValueError:
                        pass

        td.time = time_vals
        for fid, meta in data_signals.items():
            key = meta["key"]
            td.channels[key] = {
                "data": field_values[fid],
                "meta": meta,
            }
            td.signals.append(meta)

        return td


# ---------------------------------------------------------------------------
# Oscilloscope Plot Widget — single plot, merged Y-axis
# ---------------------------------------------------------------------------
class OscilloscopePlot(QWidget):
    cursorMoved = Signal()
    hoverValue = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setMenuEnabled(False)
        self.plot.setMouseEnabled(x=True, y=True)

        self.plot.getAxis("left").setPen(pg.mkPen("#888888"))
        self.plot.getAxis("left").setTextPen(pg.mkPen("#cccccc"))
        self.plot.getAxis("bottom").setPen(pg.mkPen("#888888"))
        self.plot.getAxis("bottom").setTextPen(pg.mkPen("#cccccc"))
        self.plot.setLabel("bottom", "Time", units="s", color="#cccccc")

        self.cursor1 = pg.InfiniteLine(
            angle=90, movable=True, pen=pg.mkPen("#ff5555", width=2),
            label="T1", labelOpts={"position": 0.02, "color": "#ff5555",
                                    "fill": (80, 0, 0, 180), "movable": True}
        )
        self.cursor2 = pg.InfiniteLine(
            angle=90, movable=True, pen=pg.mkPen("#55ffff", width=2),
            label="T2", labelOpts={"position": 0.98, "color": "#55ffff",
                                    "fill": (0, 80, 80, 180), "movable": True}
        )
        self.plot.addItem(self.cursor1)
        self.plot.addItem(self.cursor2)
        self.cursor1.sigPositionChanged.connect(self._on_cursor_moved)
        self.cursor2.sigPositionChanged.connect(self._on_cursor_moved)

        self.v_line = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen("#aaaaaa", width=1, style=Qt.DashLine)
        )
        self.h_line = pg.InfiniteLine(
            angle=0, movable=False,
            pen=pg.mkPen("#aaaaaa", width=1, style=Qt.DashLine)
        )
        self.plot.addItem(self.v_line, ignoreBounds=True)
        self.plot.addItem(self.h_line, ignoreBounds=True)
        self.v_line.hide()
        self.h_line.hide()

        layout.addWidget(self.plot)

        self.curves = {}
        self.channel_visible = {}
        self.channel_times = {}
        self.channel_data = {}
        self._trace_data = None

        self.proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self._on_hover_moved
        )

    def set_trace_data(self, td: TraceData):
        for curve in self.curves.values():
            self.plot.removeItem(curve)
        self.curves.clear()
        self.channel_visible.clear()
        self.channel_times.clear()
        self.channel_data.clear()

        self._trace_data = td

        if td.time is None or len(td.time) == 0:
            return

        t = td.time
        t_min, t_max = t[0], t[-1]

        for key, ch in td.channels.items():
            meta = ch["meta"]
            color_tuple = color_to_tuple(meta.get("color", "FFFFFF"))
            pen = pg.mkPen(color=color_tuple, width=1.5)

            # Extract valid (non-NaN) points for this channel
            data = ch["data"]
            valid_mask = ~np.isnan(data)
            t_valid = t[valid_mask]
            y_valid = data[valid_mask]

            curve = pg.PlotDataItem(t_valid, y_valid, pen=pen, connect="finite")
            self.plot.addItem(curve)
            self.curves[key] = curve
            self.channel_visible[key] = True
            self.channel_times[key] = t_valid
            self.channel_data[key] = y_valid

        self.plot.setXRange(t_min, t_max, padding=0.02)
        self._update_y_range()

        span = t_max - t_min
        self.cursor1.setValue(t_min + span * 0.1)
        self.cursor2.setValue(t_min + span * 0.9)

    def _on_cursor_moved(self):
        self.cursorMoved.emit()

    def _on_hover_moved(self, evt):
        pos = evt[0]
        if self.plot.vb.sceneBoundingRect().contains(pos):
            mouse_point = self.plot.vb.mapSceneToView(pos)
            x = mouse_point.x()
            y = mouse_point.y()
            self.v_line.setPos(x)
            self.h_line.setPos(y)
            self.v_line.show()
            self.h_line.show()

            info = f"Time: {x:.6f}s"
            if self._trace_data is not None:
                for key in self._trace_data.channels:
                    if not self.channel_visible.get(key, True):
                        continue
                    t_arr = self.channel_times.get(key)
                    y_arr = self.channel_data.get(key)
                    if t_arr is None or len(t_arr) == 0:
                        continue
                    idx = np.searchsorted(t_arr, x)
                    if 0 <= idx < len(t_arr):
                        val = y_arr[idx]
                        meta = self._trace_data.channels[key]["meta"]
                        name = meta.get("description", meta.get("name", key))
                        short_name = name[:30] + "..." if len(name) > 30 else name
                        info += f"\n  {short_name}: {val:.6f}"
            self.hoverValue.emit(info)
        else:
            self.v_line.hide()
            self.h_line.hide()
            self.hoverValue.emit("")

    def set_channel_visible(self, key: str, visible: bool):
        if key in self.curves:
            self.curves[key].setVisible(visible)
            self.channel_visible[key] = visible
            self._update_y_range()

    def set_channel_axis(self, key: str, axis: str):
        pass

    def get_cursor_values(self):
        if self._trace_data is None or self._trace_data.time is None:
            return None, None
        return self.cursor1.value(), self.cursor2.value()

    def get_measurements(self):
        if self._trace_data is None:
            return {}
        t1, t2 = self.get_cursor_values()
        if t1 is None:
            return {}

        t_min = min(t1, t2)
        t_max = max(t1, t2)

        results = {}

        for key in self._trace_data.channels:
            t_arr = self.channel_times.get(key)
            y_arr = self.channel_data.get(key)
            meta = self._trace_data.channels[key]["meta"]
            name = meta.get("description", meta.get("name", key))
            units = meta.get("unitsType", "")
            visible = self.channel_visible.get(key, True)
            if t_arr is None or len(t_arr) == 0:
                results[key] = {
                    "name": name, "units": units, "visible": visible,
                    "t1": t1, "t2": t2, "delta": abs(t2 - t1),
                    "rms": None, "avg": None, "std": None, "pp": None,
                    "min": None, "max": None,
                }
                continue
            mask = (t_arr >= t_min) & (t_arr <= t_max)
            valid = y_arr[mask]
            if len(valid) == 0:
                results[key] = {
                    "name": name, "units": units, "visible": visible,
                    "t1": t1, "t2": t2, "delta": abs(t2 - t1),
                    "rms": None, "avg": None, "std": None, "pp": None,
                    "min": None, "max": None,
                }
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

    def _update_y_range(self):
        if self._trace_data is None:
            return
        y_min = float('inf')
        y_max = float('-inf')
        has_visible = False
        for key in self._trace_data.channels:
            if not self.channel_visible.get(key, True):
                continue
            y_arr = self.channel_data.get(key)
            if y_arr is not None and len(y_arr) > 0:
                has_visible = True
                y_min = min(y_min, np.min(y_arr))
                y_max = max(y_max, np.max(y_arr))
        if has_visible:
            margin = (y_max - y_min) * 0.1 if y_max != y_min else 1.0
            self.plot.setYRange(y_min - margin, y_max + margin, padding=0.05)


# ---------------------------------------------------------------------------
# Measurement Table — includes visibility checkboxes
# ---------------------------------------------------------------------------
class MeasurementTable(QTableWidget):
    visibilityChanged = Signal(str, bool)

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
            "Average", "Std. Dev.", "Peak-Peak", "Min", "Max"
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

        self._channel_keys = []
        self._channel_meta = {}

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

            values = [
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
            ]
            for col, text in values:
                item = self.item(row, col)
                if item is None:
                    item = QTableWidgetItem()
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.setItem(row, col, item)
                item.setText(text)
                item.setForeground(dim_color)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Industrial Oscilloscope - SINUMERIK Trace Viewer")
        self.setMinimumSize(1280, 800)
        self.resize(1500, 950)

        self.trace_data = None
        self.parser = XmlTraceParser()

        self._build_ui()
        self._apply_dark_theme()

        default_xml = Path(__file__).parent / "Tav23362_2140_frenata_15_4_26_EmgTest.xml"
        if default_xml.exists():
            self.load_file(str(default_xml))

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_label = QLabel("Industrial Oscilloscope - Ready")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 6px; "
            "background-color: #2b2b2b; color: #eeeeee; border-bottom: 1px solid #444444;"
        )
        main_layout.addWidget(self.title_label)

        self.hover_label = QLabel("Hover over plot to see values")
        self.hover_label.setStyleSheet(
            "font-size: 11px; padding: 3px 10px; background-color: #1a1a1a; color: #aaaaaa; border-bottom: 1px solid #333333;"
        )
        main_layout.addWidget(self.hover_label)

        self.plot_widget = OscilloscopePlot()
        self.plot_widget.cursorMoved.connect(self._update_measurements)
        self.plot_widget.hoverValue.connect(self._on_hover)

        self.measurement_table = MeasurementTable()
        self.measurement_table.visibilityChanged.connect(self._on_channel_visibility)

        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.addWidget(self.plot_widget)
        v_splitter.addWidget(self.measurement_table)
        v_splitter.setStretchFactor(0, 3)
        v_splitter.setStretchFactor(1, 1)
        main_layout.addWidget(v_splitter, stretch=1)

        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        open_act = QAction("Open XML", self)
        open_act.setShortcut(QKeySequence.Open)
        open_act.triggered.connect(self._open_file)
        toolbar.addAction(open_act)

        reset_zoom_act = QAction("Reset Zoom", self)
        reset_zoom_act.triggered.connect(self._reset_zoom)
        toolbar.addAction(reset_zoom_act)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QToolBar { background-color: #2b2b2b; border: none; padding: 4px; }
            QToolButton { color: #eeeeee; padding: 4px 8px; }
            QStatusBar { background-color: #2b2b2b; color: #eeeeee; }
            QMenuBar { background-color: #2b2b2b; color: #eeeeee; }
            QMenu { background-color: #2b2b2b; color: #eeeeee; }
            QMenu::item:selected { background-color: #3a6ea5; }
            QMessageBox { background-color: #2b2b2b; }
            QScrollArea { border: none; }
        """)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Trace XML", str(Path(__file__).parent),
            "XML Files (*.xml);;All Files (*.*)"
        )
        if path:
            self.load_file(path)

    def load_file(self, filepath: str):
        try:
            self.trace_data = self.parser.parse(filepath)
            self.plot_widget.set_trace_data(self.trace_data)
            self.measurement_table.set_channels(self.trace_data.signals, self.trace_data.channels)
            self._update_measurements()

            title = f"Scope plot of {Path(filepath).stem}"
            if self.trace_data.start_time:
                title += f"  |  Capture: {self.trace_data.start_time}"
            self.title_label.setText(title)
            self.status_bar.showMessage(
                f"Loaded {len(self.trace_data.signals)} channels, {len(self.trace_data.time)} time points, "
                f"duration={self.trace_data.stop_inc:.3f}s"
            )
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to parse XML:\n{e}")

    def _on_channel_visibility(self, key: str, visible: bool):
        self.plot_widget.set_channel_visible(key, visible)
        self._update_measurements()

    def _update_measurements(self):
        measurements = self.plot_widget.get_measurements()
        self.measurement_table.update_measurements(measurements)

    def _on_hover(self, text: str):
        self.hover_label.setText(text.replace("\n", "  |  "))

    def _reset_zoom(self):
        if self.trace_data is not None and self.trace_data.time is not None:
            t = self.trace_data.time
            self.plot_widget.plot.setXRange(t[0], t[-1], padding=0.02)
            self.plot_widget._update_y_range()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    from PySide6.QtGui import QPalette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.WindowText, QColor(238, 238, 238))
    dark_palette.setColor(QPalette.Base, QColor(43, 43, 43))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(43, 43, 43))
    dark_palette.setColor(QPalette.ToolTipText, QColor(238, 238, 238))
    dark_palette.setColor(QPalette.Text, QColor(238, 238, 238))
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, QColor(238, 238, 238))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(238, 238, 238))
    app.setPalette(dark_palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
