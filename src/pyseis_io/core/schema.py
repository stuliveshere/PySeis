"""
PyArrow schema utilities for pyseis-io single-Parquet datasets.

Provides clean PyArrow schema construction for FixedSizeList trace sample vectors
and standardized domain header data types.
"""

from typing import Dict, Any, Optional
import pyarrow as pa
import pandas as pd

# Default Arrow data types for standard seismic domain headers
DEFAULT_HEADER_TYPES: Dict[str, pa.DataType] = {
    # Trace Keys & Data
    "offset": pa.float32(),
    "mute_start": pa.float32(),
    "mute_end": pa.float32(),
    "total_static": pa.float32(),
    "trace_code": pa.int32(),  # 1: Live, 2: Dead, 3: Aux
    "trace_weighting_factor": pa.float32(),

    # Shot Keys (Source Domain)
    "shot_number": pa.int32(),
    "file_number": pa.int32(),
    "source_line": pa.int32(),
    "source_station": pa.int32(),
    "source_index": pa.int32(),
    "shot_time": pa.int64(),  # Milliseconds since Unix Epoch
    "recording_delay": pa.float32(),
    "source_x": pa.float64(),
    "source_y": pa.float64(),
    "source_elevation": pa.float32(),
    "source_depth": pa.float32(),
    "source_static": pa.float32(),

    # Receiver Keys (Receiver Domain)
    "channel_number": pa.int32(),
    "receiver_line": pa.int32(),
    "receiver_station": pa.int32(),
    "receiver_index": pa.int32(),
    "receiver_x": pa.float64(),
    "receiver_y": pa.float64(),
    "receiver_elevation": pa.float32(),
    "receiver_static": pa.float32(),

    # CDP Keys (Stacking / 3D Binning Domain)
    "cdp": pa.int32(),
    "cdp_trace_number": pa.int32(),
    "inline": pa.int32(),
    "crossline": pa.int32(),
    "cdp_x": pa.float64(),
    "cdp_y": pa.float64(),
}

def get_trace_vector_type(n_samples: int) -> pa.DataType:
    """
    Construct a PyArrow FixedSizeList type for trace sample vectors of length n_samples.
    
    Args:
        n_samples: Number of amplitude samples per trace.
        
    Returns:
        pa.DataType representing FixedSizeList(Float32, n_samples).
    """
    return pa.list_(pa.float32(), n_samples)

def build_dataset_schema(
    n_samples: int,
    headers_df: Optional[pd.DataFrame] = None,
    custom_types: Optional[Dict[str, pa.DataType]] = None
) -> pa.Schema:
    """
    Build a complete PyArrow Schema for a single-Parquet dataset.
    
    Args:
        n_samples: Length of each trace sample vector.
        headers_df: Optional Pandas DataFrame of header columns to infer types from.
        custom_types: Optional map of column name -> PyArrow DataType overrides.
        
    Returns:
        pa.Schema with 'samples' vector column and scalar header fields.
    """
    fields = [pa.field("samples", get_trace_vector_type(n_samples))]
    
    overrides = custom_types or {}
    
    if headers_df is not None:
        for col in headers_df.columns:
            if col == "samples":
                continue
            if col in overrides:
                col_type = overrides[col]
            elif col in DEFAULT_HEADER_TYPES:
                col_type = DEFAULT_HEADER_TYPES[col]
            else:
                # Convert pandas dtype to PyArrow dtype
                col_type = pa.Schema.from_pandas(headers_df[[col]]).field(0).type
            fields.append(pa.field(col, col_type))
            
    return pa.schema(fields)

def validate_header_dataframe(df: pd.DataFrame) -> None:
    """
    Validate that a header DataFrame is valid for writing.
    
    Args:
        df: Pandas DataFrame of trace headers.
        
    Raises:
        ValueError: If DataFrame is invalid or empty.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Header data must be a non-empty pandas DataFrame")
