"""Tests for the SINUMERIK XML parser."""
from pathlib import Path
import sys

# Add project root to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import SinumerikXmlParser


def test_parser_loads_real_xml():
    """Verify the parser can load the test XML file successfully."""
    xml_path = (
        Path(__file__).parent.parent
        / "Tav23362_2140_frenata_15_4_26_EmgTest.xml"
    )
    if not xml_path.exists():
        print("SKIP: test XML file not found")
        return

    parser = SinumerikXmlParser()
    td = parser.parse(str(xml_path))

    # Basic assertions
    assert td.time is not None, "Time array should not be None"
    assert len(td.time) > 0, "Time array should not be empty"
    assert len(td.signals) > 0, "Should have at least one signal"
    assert len(td.channels) == len(td.signals), "Channels and signals should match"

    # Check data integrity
    for key, ch_data in td.channels.items():
        assert "data" in ch_data, f"Channel {key} missing 'data'"
        assert "meta" in ch_data, f"Channel {key} missing 'meta'"
        assert len(ch_data["data"]) == len(td.time), (
            f"Channel {key} data length mismatch"
        )

    print(f"OK: Loaded {len(td.signals)} channels, {len(td.time)} time points")
    print(f"    Duration: {td.stop_inc:.3f}s, Start: {td.start_time}")


if __name__ == "__main__":
    test_parser_loads_real_xml()
