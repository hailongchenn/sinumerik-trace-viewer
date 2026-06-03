"""Parser for Siemens SINUMERIK Solution Line Trace XML files."""
from __future__ import annotations

import xml.etree.ElementTree as ET
import numpy as np

from models import TraceData
from parsers.base import BaseParser


class SinumerikXmlParser(BaseParser):
    """Parses SINUMERIK trace XML into a TraceData instance."""

    def supported_extensions(self) -> list[str]:
        return [".xml"]

    def parse(self, filepath: str) -> TraceData:
        tree = ET.parse(filepath)
        root = tree.getroot()

        td = TraceData()

        signal_meta = self._parse_display_setup(root)
        data_frame = self._find_data_frame(root)

        self._parse_frame_header(data_frame, td)
        data_signals = self._parse_data_signals(data_frame, signal_meta)
        self._parse_records(data_frame, data_signals, td)
        self._build_channels(data_signals, td)

        return td

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_display_setup(root: ET.Element) -> dict[str, dict]:
        """Extract signal metadata from <traceDisplaySetup> (or V20 variant)."""
        display_setup = root.find("traceDisplaySetup")
        if display_setup is None:
            display_setup = root.find("traceDisplaySetup_V20")

        signal_meta: dict[str, dict] = {}
        if display_setup is None:
            return signal_meta

        signals_elem = display_setup.find("signals")
        if signals_elem is None:
            return signal_meta

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
        return signal_meta

    @staticmethod
    def _find_data_frame(root: ET.Element) -> ET.Element:
        trace_data = root.find("traceData")
        if trace_data is None:
            raise ValueError("No <traceData> found in XML")

        data_frame = trace_data.find("dataFrame")
        if data_frame is None:
            raise ValueError("No <dataFrame> found in XML")
        return data_frame

    @staticmethod
    def _parse_frame_header(data_frame: ET.Element, td: TraceData) -> None:
        frame_header = data_frame.find("frameHeader")
        if frame_header is not None:
            td.start_time = frame_header.get("startTime", "")
            td.stop_inc = float(frame_header.get("stopInc", "0"))

    @staticmethod
    def _parse_data_signals(
        data_frame: ET.Element, signal_meta: dict[str, dict]
    ) -> dict[str, dict]:
        """Build a data_signals dict keyed by field id."""
        data_signals: dict[str, dict] = {}
        for ds in data_frame.findall("dataSignal"):
            fid = ds.get("id")
            key = ds.get("key")
            info: dict = {
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
                info.update({
                    "color": signal_meta[key].get("color", "FFFFFF"),
                    "displayRes": signal_meta[key].get("displayRes", 5),
                    "axisDisplay": signal_meta[key].get("axisDisplay", "leftSide"),
                })
            else:
                info["color"] = "FFFFFF"
                info["displayRes"] = 5
                info["axisDisplay"] = "leftSide"
            data_signals[fid] = info
        return data_signals

    @staticmethod
    def _parse_records(
        data_frame: ET.Element,
        data_signals: dict[str, dict],
        td: TraceData,
    ) -> None:
        """Parse <rec> elements into time and field value arrays."""
        recs = data_frame.findall("rec")
        n = len(recs)

        time_vals = np.zeros(n, dtype=np.float64)
        field_values = {
            fid: np.full(n, np.nan, dtype=np.float64) for fid in data_signals
        }

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
        td._field_values = field_values  # temporary, consumed by _build_channels

    @staticmethod
    def _build_channels(
        data_signals: dict[str, dict], td: TraceData
    ) -> None:
        """Populate td.channels and td.signals from parsed data."""
        field_values = getattr(td, "_field_values", {})
        for fid, meta in data_signals.items():
            key = meta["key"]
            td.channels[key] = {
                "data": field_values.get(fid, np.array([])),
                "meta": meta,
            }
            td.signals.append(meta)


# Keep alias for backward compatibility
XmlTraceParser = SinumerikXmlParser
