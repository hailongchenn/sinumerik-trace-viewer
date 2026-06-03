"""FFT frequency-domain plot widget."""
from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox,
)
from PySide6.QtCore import Qt, Signal

import pyqtgraph as pg


class FftPlot(QWidget):
    """A dockable FFT spectrum plot panel."""

    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)  # hidden by default

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Header bar ---
        header = QWidget()
        header.setStyleSheet(
            "background-color: #2b2b2b; border-bottom: 1px solid #444444;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 4, 4, 4)
        header_layout.setSpacing(8)

        self._title = QLabel("FFT Spectrum")
        self._title.setStyleSheet("font-size: 12px; font-weight: bold; color: #eeeeee;")

        window_label = QLabel("Window:")
        window_label.setStyleSheet("color: #999999; font-size: 11px;")

        self._window_combo = QComboBox()
        self._window_combo.addItems(["hann", "hamming", "blackman", "rectangular"])
        self._window_combo.setStyleSheet("""
            QComboBox { background: #333; color: #eee; padding: 2px 6px; border: 1px solid #555; }
            QComboBox::drop-down { border: none; }
        """)
        self._window_combo.currentTextChanged.connect(self._on_window_changed)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet(
            "QPushButton { border: none; color: #999; font-size: 16px; }"
            "QPushButton:hover { color: #fff; background: #555; }"
        )
        close_btn.clicked.connect(self.hide_panel)

        header_layout.addWidget(self._title, 1)
        header_layout.addWidget(window_label)
        header_layout.addWidget(self._window_combo)
        header_layout.addWidget(close_btn)
        layout.addWidget(header)

        # --- Plot ---
        self._plot = pg.PlotWidget()
        self._plot.showGrid(x=True, y=True, alpha=0.25)
        self._plot.setMenuEnabled(False)
        self._plot.setMouseEnabled(x=True, y=True)
        self._plot.getAxis("left").setPen(pg.mkPen("#888888"))
        self._plot.getAxis("left").setTextPen(pg.mkPen("#cccccc"))
        self._plot.getAxis("bottom").setPen(pg.mkPen("#888888"))
        self._plot.getAxis("bottom").setTextPen(pg.mkPen("#cccccc"))
        self._plot.setLabel("bottom", "Frequency", units="Hz", color="#cccccc")
        self._plot.setLabel("left", "Magnitude", units="dB", color="#cccccc")

        self._curve = pg.PlotDataItem(
            [], [], pen=pg.mkPen("#55ff55", width=1.5), stepMode="center",
        )
        self._plot.addItem(self._curve)

        layout.addWidget(self._plot, stretch=1)

        # Internal state for re-computation on window change
        self._freqs = None
        self._mag_db = None
        self._request_callback = None  # called when window changes

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_fft_data(
        self,
        channel_name: str,
        freqs: np.ndarray,
        mag_db: np.ndarray,
        window: str,
        t1: float,
        t2: float,
    ):
        """Display FFT spectrum data."""
        self._freqs = freqs
        self._mag_db = mag_db

        # Update title
        region_text = f"{min(t1, t2):.4f}s – {max(t1, t2):.4f}s"
        self._title.setText(f"FFT: {channel_name} | {region_text} | {window}")

        # Update window combo without triggering signal
        self._window_combo.blockSignals(True)
        idx = self._window_combo.findText(window)
        if idx >= 0:
            self._window_combo.setCurrentIndex(idx)
        self._window_combo.blockSignals(False)

        # Plot
        self._curve.setData(freqs, mag_db)

        # Auto-range
        if len(freqs) > 0 and len(mag_db) > 0:
            self._plot.setXRange(0, freqs[-1], padding=0.02)
            db_min = max(np.min(mag_db), -200)
            db_max = np.max(mag_db)
            margin = (db_max - db_min) * 0.1 if db_max != db_min else 10.0
            self._plot.setYRange(db_min - margin, db_max + margin, padding=0.05)

        self.setVisible(True)

    def hide_panel(self):
        """Hide the FFT panel."""
        self.setVisible(False)
        self.closed.emit()

    def set_recompute_callback(self, callback):
        """Set callback for when window type changes. Called as callback()."""
        self._request_callback = callback

    @property
    def current_window(self) -> str:
        return self._window_combo.currentText()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_window_changed(self, _text: str):
        if self._request_callback:
            self._request_callback()
