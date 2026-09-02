"""
Footer metadata management for pyseis single-Parquet datasets.

Handles encoding, decoding, attaching, and extracting JSON dataset metadata
from Parquet file footers (key_value_metadata).
"""

import json
import io
from pathlib import Path
from typing import Dict, Any, Union, Optional
import pyarrow as pa
import pyarrow.parquet as pq

METADATA_KEY = b"pyseis_metadata"

def encode_footer_metadata(metadata_dict: Dict[str, Any]) -> Dict[bytes, bytes]:
    """
    Serialize a Python dictionary into a Parquet-compatible key_value_metadata map.
    
    Args:
        metadata_dict: Dictionary containing dataset metadata (e.g. sample_rate, domain, provenance).
        
    Returns:
        Dict[bytes, bytes] formatted for PyArrow schema metadata.
    """
    json_bytes = json.dumps(metadata_dict, indent=2).encode("utf-8")
    return {METADATA_KEY: json_bytes}

def decode_footer_metadata(raw_metadata: Optional[Dict[bytes, bytes]]) -> Dict[str, Any]:
    """
    Extract and deserialize pyseis_metadata from a Parquet key_value_metadata map.
    
    Args:
        raw_metadata: Raw key_value_metadata dictionary from PyArrow schema or Parquet file footer.
        
    Returns:
        Dict[str, Any] representing the deserialized metadata, or empty dict if not found.
    """
    if not raw_metadata or METADATA_KEY not in raw_metadata:
        return {}
        
    try:
        json_str = raw_metadata[METADATA_KEY].decode("utf-8")
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Failed to parse pyseis_metadata from Parquet footer: {e}") from e

def attach_footer_metadata(table: pa.Table, metadata_dict: Dict[str, Any]) -> pa.Table:
    """
    Attach pyseis_metadata to a PyArrow Table's schema metadata.
    
    Args:
        table: PyArrow Table to update.
        metadata_dict: Metadata dictionary to embed.
        
    Returns:
        New PyArrow Table with updated schema metadata.
    """
    existing_metadata = table.schema.metadata or {}
    new_metadata = {**existing_metadata, **encode_footer_metadata(metadata_dict)}
    return table.replace_schema_metadata(new_metadata)

def read_footer_metadata(source: Union[str, Path, io.BytesIO, pa.Buffer, pa.NativeFile]) -> Dict[str, Any]:
    """
    Read pyseis_metadata from a Parquet file path or in-memory buffer without reading trace data arrays.
    
    Args:
        source: File path or in-memory byte buffer.
        
    Returns:
        Dict[str, Any] containing the embedded dataset metadata.
    """
    if isinstance(source, (str, Path)):
        source = str(source)
    elif isinstance(source, bytes):
        source = pa.BufferReader(source)
    elif isinstance(source, io.BytesIO):
        source.seek(0)
        
    pf = pq.ParquetFile(source)
    metadata_map = pf.metadata.metadata
    return decode_footer_metadata(metadata_map)
