#!/usr/bin/env python3
"""
Industrial Oscilloscope - SINUMERIK Trace File Viewer
Reads Siemens SINUMERIK Solution Line Trace XML files and displays waveforms.
Single plot: all channels overlaid with shared Y-axis auto-scaled to visible data.
"""

import sys
import numpy as np
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QSplitter, QFileDialog, QStatusBar,
)
from PySide6.QtCore import Qt

import pyqtgraph as pg

from models import TraceData
from parsers import SinumerikXmlParser as XmlTraceParser
from plot import OscilloscopePlot, FftPlot
from ui import MeasurementTable, setup_toolbar, create_dark_palette, MAIN_STYLESHEET
from analysis import compute_fft

pg.setConfigOptions(antialias=True, useOpenGL=False)


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
        self._last_fft_channel = None  # for toolbar FFT button

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

        # FFT panel (hidden by default)
        self.fft_plot = FftPlot()
        self.fft_plot.set_recompute_callback(self._on_fft_recompute)

        # Main vertical splitter: time plot + FFT panel
        self._top_splitter = QSplitter(Qt.Vertical)
        self._top_splitter.addWidget(self.plot_widget)
        self._top_splitter.addWidget(self.fft_plot)
        self._top_splitter.setStretchFactor(0, 4)
        self._top_splitter.setStretchFactor(1, 0)

        self.measurement_table = MeasurementTable()
        self.measurement_table.visibilityChanged.connect(self._on_channel_visibility)
        self.measurement_table.fftRequested.connect(self._on_fft_requested)

        # Outer vertical splitter: (time+fft) + measurement table
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.addWidget(self._top_splitter)
        v_splitter.addWidget(self.measurement_table)
        v_splitter.setStretchFactor(0, 3)
        v_splitter.setStretchFactor(1, 1)
        main_layout.addWidget(v_splitter, stretch=1)

        toolbar = setup_toolbar(self)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _apply_dark_theme(self):
        self.setStyleSheet(MAIN_STYLESHEET)

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
            self.fft_plot.hide_panel()

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

    # ------------------------------------------------------------------
    # FFT
    # ------------------------------------------------------------------

    def _on_fft_requested(self, key: str):
        """Handle right-click → Compute FFT from measurement table."""
        self._last_fft_channel = key
        self._compute_and_show_fft(key)

    def _on_fft_toolbar(self):
        """Handle toolbar FFT button — use last-clicked or first channel."""
        if self.trace_data is None:
            return
        key = self._last_fft_channel
        if key is None and self.trace_data.channels:
            key = next(iter(self.trace_data.channels))
            self._last_fft_channel = key
        if key:
            self._compute_and_show_fft(key)

    def _on_fft_recompute(self):
        """Recompute FFT when window type changes."""
        if self._last_fft_channel:
            self._compute_and_show_fft(self._last_fft_channel)

    def _compute_and_show_fft(self, key: str):
        """Run FFT on the selected channel and show the panel."""
        if self.trace_data is None or key not in self.trace_data.channels:
            return

        t1, t2 = self.plot_widget.get_cursor_values()
        if t1 is None:
            return

        ch = self.trace_data.channels[key]
        time = self.trace_data.time
        data = ch["data"]
        meta = ch["meta"]
        name = meta.get("description", meta.get("name", key))
        window = self.fft_plot.current_window

        result = compute_fft(time, data, t1, t2, window=window)
        if result is None:
            self.status_bar.showMessage(
                f"FFT: not enough valid data points in cursor region for {name}"
            )
            return

        freqs, mag, mag_db = result
        self.fft_plot.set_fft_data(name, freqs, mag_db, window, t1, t2)

        # Allocate ~25% of the top splitter to FFT
        if self._top_splitter.count() >= 2:
            total = self._top_splitter.height()
            if total > 0:
                self._top_splitter.setSizes([int(total * 0.65), int(total * 0.35)])

        self.status_bar.showMessage(
            f"FFT: {name} | {min(t1, t2):.4f}s–{max(t1, t2):.4f}s | "
            f"peak={freqs[np.argmax(mag)]:.1f} Hz (window: {window})"
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(create_dark_palette())

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
