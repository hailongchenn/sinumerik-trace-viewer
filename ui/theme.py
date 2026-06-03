"""Dark Fusion theme for the Industrial Oscilloscope."""
from PySide6.QtGui import QPalette, QColor


def create_dark_palette() -> QPalette:
    """Return a dark QPalette for the Fusion style."""
    p = QPalette()
    p.setColor(QPalette.Window, QColor(30, 30, 30))
    p.setColor(QPalette.WindowText, QColor(238, 238, 238))
    p.setColor(QPalette.Base, QColor(43, 43, 43))
    p.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    p.setColor(QPalette.ToolTipBase, QColor(43, 43, 43))
    p.setColor(QPalette.ToolTipText, QColor(238, 238, 238))
    p.setColor(QPalette.Text, QColor(238, 238, 238))
    p.setColor(QPalette.Button, QColor(53, 53, 53))
    p.setColor(QPalette.ButtonText, QColor(238, 238, 238))
    p.setColor(QPalette.BrightText, QColor(255, 0, 0))
    p.setColor(QPalette.Highlight, QColor(42, 130, 218))
    p.setColor(QPalette.HighlightedText, QColor(238, 238, 238))
    return p


MAIN_STYLESHEET = """
    QMainWindow { background-color: #1e1e1e; }
    QToolBar { background-color: #2b2b2b; border: none; padding: 4px; }
    QToolButton { color: #eeeeee; padding: 4px 8px; }
    QStatusBar { background-color: #2b2b2b; color: #eeeeee; }
    QMenuBar { background-color: #2b2b2b; color: #eeeeee; }
    QMenu { background-color: #2b2b2b; color: #eeeeee; }
    QMenu::item:selected { background-color: #3a6ea5; }
    QMessageBox { background-color: #2b2b2b; }
    QScrollArea { border: none; }
"""
