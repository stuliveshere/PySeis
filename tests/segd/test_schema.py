"""
Tests for 5-layer YAML Schema engine, merging, and auto-detection.
"""

import pytest
from pathlib import Path
from pyseis_io.segd.schema import SchemaManager

def test_schema_load_effective():
    manager = SchemaManager()
    schema = manager.load_effective_schema(revision="2.1", manufacturer="smartsolo", variant="version002")
    
    assert schema.revision == "2.1"
    assert schema.manufacturer == "smartsolo"
    assert "general_header_1" in schema.blocks
    assert "general_header_2" in schema.blocks
    assert "demux_trace_header" in schema.blocks

    # Check mapping
    sg_map = schema.get_mapping("sg")
    assert "FFID" in sg_map or "tracl" in sg_map or len(sg_map) > 0


def test_schema_auto_detect():
    manager = SchemaManager()
    
    # Construct a 64-byte mock buffer for SmartSolo Rev 2.1
    buf = bytearray(64)
    buf[16] = 0x61 # Manufacturer code 0x61 (SmartSolo)
    buf[42] = 0x20 # Rev 2.1 in GH2

    schema = manager.auto_detect_schema(bytes(buf))
    assert schema.manufacturer == "smartsolo"
    assert schema.revision == "2.1"
