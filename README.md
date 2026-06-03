# Industrial Oscilloscope — SINUMERIK Trace Viewer

A desktop GUI application that reads **Siemens SINUMERIK Solution Line Trace XML** files and displays waveform data. Built with PySide6 + pyqtgraph.

## Screenshot (UI Layout)

```
┌──────────────────────────────────────────────┐
│  Industrial Oscilloscope — SINUMERIK Viewer   │  ← Title bar
├──────────────────────────────────────────────┤
│  Hover over plot to see values                │  ← Hover info bar
├──────────────────────────────────────────────┤
│                                              │
│  ┌──────────────────────────────────────────┐│
│  │  Waveform plot (all channels overlaid)    ││  ← Single shared plot
│  │  • T1 / T2 draggable cursors              ││    with auto-scaled Y-axis
│  │  • Mouse hover crosshair                  ││
│  │                                           ││
│  └──────────────────────────────────────────┘│
│  ─────────────────── drag to resize ───────── │  ← Vertical splitter
│  ┌──────────────────────────────────────────┐│
│  │ ☑ │ Channel Name  │ Unit │ T1 │ … │ Max  ││  ← Measurement table
│  │ ☐ │ Hidden Ch.    │  —   │ —  │ … │  —   ││    with colored checkboxes
│  └──────────────────────────────────────────┘│
└──────────────────────────────────────────────┘
```

## Features

- Parses SINUMERIK **Solution Line Trace** XML format (both V1 and V20)
- All channels overlaid on a **single shared plot** with auto-scaled Y-axis
- Two **draggable vertical cursors** (T1 red, T2 cyan) for interval measurement
- **Mouse hover crosshair** showing real-time values of every visible channel
- **Per-channel statistics** between cursors: RMS, Average, Std Dev, Peak-Peak, Min, Max
- **Colored visibility checkboxes** directly in the measurement table
- Resizable plot/table layout via **drag handle**
- **Dark theme** (Fusion style + custom palette + stylesheet)
- Auto-loads `Tav23362_2140_frenata_15_4_26_EmgTest.xml` on startup if present

## Requirements

- Python 3.8+
- PySide6
- pyqtgraph
- numpy

## Install & Run

```bash
# Clone
git clone https://github.com/hailongchenn/sinumerik-trace-viewer.git
cd sinumerik-trace-viewer

# Install dependencies
pip install PySide6 pyqtgraph numpy

# Run
python oscilloscope.py
```

On Windows, double-click `run_oscilloscope.bat` or run it from the terminal.

## Usage

| Action | How |
|--------|-----|
| Open XML | Toolbar **Open XML** button or `Ctrl+O` |
| Reset Zoom | Toolbar **Reset Zoom** button |
| Move cursor | Drag T1 (red) or T2 (cyan) on the plot |
| Toggle channel | Click the checkbox in the measurement table |
| Resize table | Drag the divider between plot and table |
| Hover values | Move mouse over the waveform |

## XML Format

The application expects SINUMERIK trace XML:

```xml
<traceDataRoot>
  <traceDisplaySetup>     <!-- or traceDisplaySetup_V20 -->
    <signals>
      <signal key="..." name="..." description="..." color="00ff0000" .../>
    </signals>
  </traceDisplaySetup>
  <traceData>
    <dataFrame>
      <frameHeader startTime="..." stopInc="..."/>
      <dataSignal id="..." key="..." interval="..." datapointCount="..."/>
      <rec time="..." id1="value1" id2="value2" .../>
    </dataFrame>
  </traceData>
</traceDataRoot>
```

## License

MIT
