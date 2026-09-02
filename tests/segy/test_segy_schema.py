"""
Tests for SEG-Y YAML Schema engine, endianness auto-detection, and revision management.
"""

import pytest
from pyseis.segy.schema import SEGYSchemaManager

def test_segy_schema_load():
    manager = SEGYSchemaManager()
    schema_rev0 = manager.load_revision_schema("rev0")
    assert schema_rev0.revision == "rev0"
    assert "binary_header" in schema_rev0.blocks
    assert "trace_header" in schema_rev0.blocks

    schema_rev1 = manager.load_revision_schema("rev1")
    assert schema_rev1.revision == "rev1"
    bin_block = schema_rev1.get_block("binary_header")
    assert bin_block is not None
    # Check segyrev field exists in Rev 1
    field_names = [f.name for f in bin_block.fields]
    assert "segyrev" in field_names

def test_segy_auto_detect_endian():
    manager = SEGYSchemaManager()
    # 3600 byte buffer with Big Endian format code (5) at offset 3224
    buf = bytearray(3600)
    buf[3224] = 0x00
    buf[3225] = 0x05

    schema = manager.auto_detect(bytes(buf))
    assert schema.endian == ">"

    # Little endian format code 5 (0x0500)
    buf2 = bytearray(3600)
    buf2[3224] = 0x05
    buf2[3225] = 0x00

    schema2 = manager.auto_detect(bytes(buf2))
    assert schema2.endian == "<"
