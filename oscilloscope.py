#!/usr/bin/env python3
"""
Industrial Oscilloscope - SINUMERIK Trace File Viewer
Reads Siemens SINUMERIK Solution Line Trace XML files and displays waveforms.
Single plot: all channels overlaid with shared Y-axis auto-scaled to visible data.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QSplitter, QFileDialog, QStatusBar,
)
from PySide6.QtCore import Qt

import pyqtgraph as pg

from models import TraceData
from parsers import SinumerikXmlParser as XmlTraceParser
from plot import OscilloscopePlot
from ui import MeasurementTable, setup_toolbar, create_dark_palette, MAIN_STYLESHEET

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
    app.setPalette(create_dark_palette())

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
