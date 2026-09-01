"""
Internal format writer for pyseis-io single-Parquet datasets.
"""

import io
from pathlib import Path
from typing import Union, Optional, Dict, Any
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .schema import build_dataset_schema
from .footer_metadata import attach_footer_metadata

class InternalFormatWriter:
    """
    Writer for seismic data in the single-Parquet file format.
    
    Combines 1D trace amplitude vectors (FixedSizeList) and scalar headers into
    a single Parquet table, with embedded JSON dataset metadata in the file footer.
    """
    
    def __init__(self, destination: Union[str, Path, io.BytesIO, pa.NativeFile], overwrite: bool = True):
        """
        Initialize the writer.
        
        Args:
            destination: Output file path or in-memory byte buffer.
            overwrite: If True, overwrite existing file if destination is a path.
        """
        self.destination = destination
        self.overwrite = overwrite
        
        if isinstance(self.destination, (str, Path)):
            self.path = Path(self.destination)
            if self.path.exists() and not self.overwrite:
                raise FileExistsError(f"Destination file already exists: {self.path}")
        else:
            self.path = None

    def write(
        self,
        traces: np.ndarray,
        headers: pd.DataFrame,
        metadata: Optional[Dict[str, Any]] = None,
        row_group_size: int = 10000,
        compression: str = "zstd"
    ) -> Union[str, Path, io.BytesIO]:
        """
        Write trace amplitudes, headers, and metadata to a single Parquet dataset.
        
        Args:
            traces: 2D NumPy array of shape (n_traces, n_samples) and float32 dtype.
            headers: Pandas DataFrame containing trace header columns (length must equal n_traces).
            metadata: Dictionary containing global metadata (e.g. sample_rate, domain, survey, provenance).
            row_group_size: Number of traces per Parquet row group.
            compression: Compression codec for Parquet data ('zstd', 'snappy', 'gzip', 'none').
            
        Returns:
            The destination file path or in-memory buffer.
        """
        if not isinstance(traces, np.ndarray) or traces.ndim != 2:
            raise ValueError("traces must be a 2D NumPy array of shape (n_traces, n_samples)")
            
        if not isinstance(headers, pd.DataFrame):
            raise ValueError("headers must be a pandas DataFrame")
            
        n_traces, n_samples = traces.shape
        
        if len(headers) != n_traces:
            raise ValueError(
                f"Header length ({len(headers)}) does not match trace count ({n_traces})"
            )
            
        # Ensure float32 dtype for trace amplitudes
        if traces.dtype != np.float32:
            traces = traces.astype(np.float32)
            
        # Construct Arrow FixedSizeListArray for trace samples
        list_type = pa.list_(pa.float32(), n_samples)
        sample_array = pa.FixedSizeListArray.from_arrays(traces.ravel(), type=list_type)
        
        # Build dictionary of PyArrow arrays for headers + samples
        table_dict = {"samples": sample_array}
        
        for col in headers.columns:
            if col == "samples":
                continue
            table_dict[col] = pa.array(headers[col])
            
        # Build PyArrow schema and table
        schema = build_dataset_schema(n_samples, headers)
        table = pa.Table.from_pydict(table_dict, schema=schema)
        
        # Format metadata
        meta = metadata.copy() if metadata else {}
        meta["n_traces"] = n_traces
        meta["n_samples"] = n_samples
        if "sample_rate" not in meta:
            meta["sample_rate"] = 0.002  # Default 2ms
            
        # Attach footer metadata to schema
        table = attach_footer_metadata(table, meta)
        
        # Write Parquet table
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(table, self.path, row_group_size=row_group_size, compression=compression)
            return self.path
        else:
            if isinstance(self.destination, io.BytesIO):
                self.destination.seek(0)
            pq.write_table(table, self.destination, row_group_size=row_group_size, compression=compression)
            return self.destination
