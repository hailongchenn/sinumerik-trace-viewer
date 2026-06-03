"""Toolbar setup for the main window."""
from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction, QKeySequence


def setup_toolbar(parent) -> QToolBar:
    """Create and return the main toolbar."""
    toolbar = QToolBar("Main Toolbar")
    parent.addToolBar(toolbar)

    open_act = QAction("Open XML", parent)
    open_act.setShortcut(QKeySequence.Open)
    open_act.triggered.connect(parent._open_file)
    toolbar.addAction(open_act)

    reset_zoom_act = QAction("Reset Zoom", parent)
    reset_zoom_act.triggered.connect(parent._reset_zoom)
    toolbar.addAction(reset_zoom_act)

    toolbar.addSeparator()

    fft_act = QAction("FFT", parent)
    fft_act.setToolTip("Compute FFT of cursor region for last-clicked channel")
    fft_act.triggered.connect(parent._on_fft_toolbar)
    toolbar.addAction(fft_act)

    return toolbar
