# Industrial Oscilloscope — SINUMERIK Trace Viewer

A desktop GUI application that reads **Siemens SINUMERIK Solution Line Trace XML** files and displays waveform data. Built with PySide6 + pyqtgraph.

## Features

- Parses SINUMERIK **Solution Line Trace** XML format (both V1 and V20)
- All channels overlaid on a **single shared plot** with auto-scaled Y-axis
- Two **draggable vertical cursors** (T1 red, T2 cyan) for interval measurement
- **Mouse hover crosshair** showing real-time values of every visible channel
- **Per-channel statistics** between cursors: RMS, Average, Std Dev, Peak-Peak, Min, Max
- **Colored visibility checkboxes** directly in the measurement table
- Resizable plot/table layout via **drag handle**
- **Dark theme** (Fusion style + custom palette + stylesheet)
- **Extensible parser architecture** — add CSV, TDMS, or other formats
- **Modular codebase** — 7 packages, 24 files, clean separation of concerns

## Requirements

- Python 3.8+
- PySide6
- pyqtgraph
- numpy

## Install & Run

```bash
git clone https://github.com/hailongchenn/sinumerik-trace-viewer.git
cd sinumerik-trace-viewer
pip install PySide6 pyqtgraph numpy
python oscilloscope.py
```

On Windows, double-click `run_oscilloscope.bat`.

## Usage

| Action | How |
|--------|-----|
| Open XML | Toolbar **Open XML** or `Ctrl+O` |
| Reset Zoom | Toolbar **Reset Zoom** |
| Move cursor | Drag T1 (red) or T2 (cyan) on the plot |
| Toggle channel | Click the checkbox in the measurement table |
| Resize table | Drag the divider between plot and table |
| Hover values | Move mouse over the waveform |

## Project Structure

```
sinumerik-trace-viewer/
├── oscilloscope.py              # Entry point + MainWindow
├── run_oscilloscope.bat         # Windows launcher
├── models/                      # Data containers
│   ├── trace_data.py            # TraceData dataclass
│   └── channel.py               # ChannelMetadata, ChannelData
├── parsers/                     # File format parsers (extensible)
│   ├── base.py                  # BaseParser ABC
│   └── sinumerik_xml.py         # SINUMERIK XML parser
├── plot/                        # Plot layer
│   ├── scope_plot.py            # OscilloscopePlot (composes managers)
│   ├── cursors.py               # T1/T2 draggable cursors
│   ├── crosshair.py             # Hover crosshair
│   └── curve_manager.py         # Curve CRUD + Y-range
├── ui/                          # UI components
│   ├── measurement_table.py     # QTableWidget + colored checkboxes
│   ├── theme.py                 # Dark Fusion theme
│   └── toolbar.py               # Toolbar factory
├── analysis/                    # Signal processing
│   └── statistics.py            # Pure functions: RMS, avg, std, etc.
├── utils/                       # Shared utilities
│   ├── color.py                 # Color parsing
│   └── numpy_helpers.py         # NaN-safe array operations
└── tests/                       # Unit tests
    ├── test_color.py            # Color utility tests
    ├── test_statistics.py       # Statistics computation tests
    └── test_parser.py           # XML parsing tests
```

## Architecture

The project follows a layered modular architecture inspired by industrial oscilloscope software (Beckhoff TE1300, Siemens SINUMERIK Trace) and open-source projects (Joulescope UI, pyqtgraph-scope-plots):

```
┌────────────────────────────────────────────┐
│  oscilloscope.py — MainWindow (thin wiring)│
├────────────┬──────────────┬────────────────┤
│   ui/      │    plot/     │   analysis/    │
│  theme     │ scope_plot   │  statistics    │
│  toolbar   │ cursors      │  (fft - todo)  │
│  table     │ crosshair    │                │
│            │ curve_mgr    │                │
├────────────┴──────────────┴────────────────┤
│  parsers/          models/      utils/     │
│  BaseParser ABC    TraceData    color      │
│  SINUMERIK XML     Channel      numpy_help │
└────────────────────────────────────────────┘
```

- **Models**: Pure data containers with no Qt dependency
- **Parsers**: Extensible — implement `BaseParser` to support new formats
- **Plot**: OscilloscopePlot composes three single-responsibility managers
- **Analysis**: Pure stateless functions, fully unit-testable
- **UI**: Reusable components with signals for loose coupling

## Running Tests

```bash
python tests/test_color.py
python tests/test_statistics.py
python tests/test_parser.py
```

## XML Format

SINUMERIK trace XML with this structure:

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
