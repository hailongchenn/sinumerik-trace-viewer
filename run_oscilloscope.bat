@echo off
chcp 65001 >nul
echo Starting Industrial Oscilloscope...
echo.
python "%~dp0oscilloscope.py"
if errorlevel 1 (
    echo.
    echo Failed to start. Make sure Python, PySide6 and pyqtgraph are installed:
    echo   pip install PySide6 pyqtgraph numpy
    pause
)
