# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Industrial Oscilloscope — a desktop GUI application that reads Siemens SINUMERIK Solution Line Trace XML files and displays waveform data. Built with PySide6 and pyqtgraph.

## Running the Application

```bash
# Install dependencies
pip install PySide6 pyqtgraph numpy

# Run
python oscilloscope.py
```

On Windows, `run_oscilloscope.bat` is also available (sets UTF-8 codepage via `chcp 65001`, then launches the script). The application loads `Tav23362_2140_frenata_15_4_26_EmgTest.xml` automatically on startup if it exists alongside `oscilloscope.py`.

There is no test suite, build system, or linting configuration in this repo.

## Architecture

The entire application lives in `oscilloscope.py` (~600 lines) and is organized into these layers:

### Data Layer
- **`TraceData`** — plain data container. Holds `time` (numpy array), `signals` (list of per-signal metadata dicts), and `channels` (OrderedDict mapping signal key → `{data, meta}`).
- **`XmlTraceParser`** — parses SINUMERIK trace XML. Reads signal definitions from `<traceDisplaySetup>` (or `<traceDisplaySetup_V20>`), then reads sample data from `<traceData>/<dataFrame>/<rec>` elements. Missing data points are stored as `np.nan`.
- **`parse_color()`** — converts SINUMERIK 8-char color strings (`00ff0000`) to standard hex (`#ff0000`). Also handles 6-char strings.
- **`color_to_tuple()`** — converts a color string to an `(r, g, b, a)` tuple for pyqtgraph.

### Plot Layer — Single Shared Plot
All channels are overlaid on a **single `pg.PlotWidget`** with one shared Y-axis that auto-scales to the union of all visible channels.

- **`OscilloscopePlot`** (`QWidget`) — hosts the single plot widget.
  - Contains two cursors (`pg.InfiniteLine`): T1 (red, `#ff5555`) and T2 (cyan, `#55ffff`), both draggable.
  - Hover crosshair: a vertical + horizontal dashed line (`#aaaaaa`) shown at the mouse position. Implemented via `pg.SignalProxy` on `scene().sigMouseMoved`.
  - `set_trace_data()`: clears old curves, creates one `pg.PlotDataItem` per channel (using only non-NaN points), sets initial X range and cursor positions. `channel_times` and `channel_data` store the per-channel valid (non-NaN) arrays for fast hover lookups and measurements.
  - `set_channel_visible()`: toggles a curve's visibility and recalculates the Y range.
  - `get_measurements()`: computes RMS, average, std dev, peak-peak, min, max for **every** channel between the two cursor positions, regardless of visibility. Returns a dict keyed by channel key, each value includes a `visible` boolean flag.
  - `_update_y_range()`: rescales the Y-axis to encompass all visible channel data with 10% margin.
  - Signals: `cursorMoved()`, `hoverValue(str)`.

### UI Layer
- **`MeasurementTable`** — bottom `QTableWidget` (12 columns). Serves dual purpose:
  - **Column 0**: colored `QCheckBox` per channel for visibility toggling. Emits `visibilityChanged(key, bool)`.
  - **Columns 1–11**: channel name (styled in the channel's color, auto-fit width), unit, T1, T2, delta, RMS, average, std dev, peak-peak, min, max.
  - Rows are **persistent** — created once via `set_channels()` and updated in-place via `update_measurements()`. Hidden channels show dimmed text and "—" for measurements.
  - Table height is adjustable via a vertical `QSplitter` between the plot and the table (drag the divider).
- **`MainWindow`** — wires everything together: toolbar (Open XML, Reset Zoom), plot widget, measurement table, hover info label, status bar. Applies a dark Fusion theme via both `QPalette` and stylesheet. No side panel — the plot fills the full window width.

### Key Signal Flow
1. **File load**: `MainWindow.load_file()` → `XmlTraceParser.parse()` → `plot_widget.set_trace_data()` + `measurement_table.set_channels()` → `_update_measurements()`.
2. **Cursor move**: `InfiniteLine.sigPositionChanged` → `OscilloscopePlot._on_cursor_moved()` → `cursorMoved` signal → `MainWindow._update_measurements()`.
3. **Hover**: `pg.SignalProxy` (on `scene().sigMouseMoved`) → `OscilloscopePlot._on_hover_moved()` — shows crosshair, uses `np.searchsorted` on per-channel valid time arrays to look up values, emits `hoverValue(str)` → `MainWindow._on_hover()`.
4. **Visibility toggle**: `MeasurementTable.visibilityChanged` → `MainWindow._on_channel_visibility()` → `plot_widget.set_channel_visible()` (toggles curve + updates Y range) → `_update_measurements()`.
5. **Reset zoom**: `MainWindow._reset_zoom()` → resets X range to full time extent + calls `_update_y_range()`.

## XML Input Format

The app expects SINUMERIK trace XML with this structure:
- `<traceDisplaySetup>` (or `_V20`) → `<signals>` → `<signal>` elements with metadata (`key`, `name`, `description`, `color`, `dataType`, `unitsType`, `axisDisplay`, `displayRes`, etc.).
- `<traceData>` → `<dataFrame>` → `<frameHeader>` (start time, stop increment) + `<dataSignal>` elements (id, key, interval, datapointCount) + `<rec time="...">` elements holding per-sample values as attributes keyed by signal ID.
- Channel color comes from the `<traceDisplaySetup>` signal metadata (matched by `key`); falls back to white (`FFFFFF`) if not found.
