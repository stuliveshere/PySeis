import io
import pyarrow as pa
import pandas as pd
import pytest

from pyseis_io.core.footer_metadata import (
    encode_footer_metadata,
    decode_footer_metadata,
    attach_footer_metadata,
    read_footer_metadata,
    METADATA_KEY
)
from pyseis_io.core.schema import (
    get_trace_vector_type,
    build_dataset_schema,
    DEFAULT_HEADER_TYPES
)

def test_encode_decode_footer_metadata():
    meta = {
        "sample_rate": 0.002,
        "n_samples": 1000,
        "domain": "time",
        "survey": {"name": "Test Survey"}
    }
    encoded = encode_footer_metadata(meta)
    assert METADATA_KEY in encoded
    decoded = decode_footer_metadata(encoded)
    assert decoded["sample_rate"] == 0.002
    assert decoded["n_samples"] == 1000
    assert decoded["survey"]["name"] == "Test Survey"

def test_attach_and_read_footer_metadata():
    meta = {"sample_rate": 0.004, "domain": "depth"}
    
    # Create simple PyArrow table
    table = pa.Table.from_pydict({"a": [1, 2, 3]})
    table_with_meta = attach_footer_metadata(table, meta)
    
    # Write to in-memory Parquet
    buf = io.BytesIO()
    import pyarrow.parquet as pq
    pq.write_table(table_with_meta, buf)
    
    # Read metadata from buffer
    read_meta = read_footer_metadata(buf)
    assert read_meta["sample_rate"] == 0.004
    assert read_meta["domain"] == "depth"

def test_build_dataset_schema():
    n_samples = 500
    headers_df = pd.DataFrame({
        "shot_number": [101, 102],
        "offset": [150.0, 200.0],
        "custom_header": ["A", "B"]
    })
    
    schema = build_dataset_schema(n_samples, headers_df)
    assert "samples" in schema.names
    assert "shot_number" in schema.names
    assert "offset" in schema.names
    assert "custom_header" in schema.names
    
    # Check trace vector type
    samples_field = schema.field("samples")
    assert isinstance(samples_field.type, pa.FixedSizeListType)
    assert samples_field.type.list_size == n_samples
    assert samples_field.type.value_type == pa.float32()
    
    # Check default header types
    assert schema.field("shot_number").type == DEFAULT_HEADER_TYPES["shot_number"]
    assert schema.field("offset").type == DEFAULT_HEADER_TYPES["offset"]
