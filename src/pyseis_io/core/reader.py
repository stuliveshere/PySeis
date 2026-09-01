"""
Internal format reader for pyseis-io single-Parquet datasets.
"""

import io
from pathlib import Path
from typing import Union, Optional, Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .footer_metadata import read_footer_metadata

class InternalFormatReader:
    """
    Reader for seismic data stored in the single-Parquet file format.
    Supports file paths, in-memory buffers, instant footer metadata reads,
    and predicate pushdown gather filtering.
    """
    
    def __init__(self, source: Union[str, Path, io.BytesIO, pa.Buffer, pa.NativeFile]):
        """
        Initialize the reader.
        
        Args:
            source: File path or in-memory byte buffer.
        """
        self.source = source
        if isinstance(self.source, (str, Path)):
            self.source_path = str(self.source)
            if not Path(self.source_path).exists():
                raise FileNotFoundError(f"Dataset file not found: {self.source_path}")
        else:
            self.source_path = None
            if isinstance(self.source, bytes):
                self.source = pa.BufferReader(self.source)
            elif isinstance(self.source, io.BytesIO):
                self.source.seek(0)
                
    def read_metadata(self) -> Dict[str, Any]:
        """
        Read embedded global metadata and provenance from the Parquet file footer.
        Reads only the file footer without reading trace data arrays.
        
        Returns:
            Dict[str, Any] containing dataset metadata.
        """
        return read_footer_metadata(self.source)

    def read_table(
        self,
        filters: Optional[List[Union[Tuple, List[Tuple]]]] = None,
        columns: Optional[List[str]] = None
    ) -> pa.Table:
        """
        Read PyArrow Table from the Parquet dataset with optional predicate pushdown filters.
        
        Args:
            filters: Parquet predicate pushdown filters (e.g. [('shot_number', '==', 105)]).
            columns: Specific column names to read. If None, reads all columns.
            
        Returns:
            pa.Table: Loaded PyArrow table.
        """
        if isinstance(self.source, io.BytesIO):
            self.source.seek(0)
            
        return pq.read_table(self.source, filters=filters, columns=columns)

    def read_traces(self, table: Optional[pa.Table] = None) -> np.ndarray:
        """
        Extract 2D NumPy array of trace amplitudes from a PyArrow Table (zero-copy view).
        
        Args:
            table: Loaded PyArrow table. If None, reads the full table.
            
        Returns:
            2D NumPy array of shape (n_traces, n_samples).
        """
        if table is None:
            table = self.read_table(columns=["samples"])
            
        if "samples" not in table.column_names:
            raise KeyError("Table does not contain 'samples' column")
            
        samples_col = table["samples"]
        
        # Combine chunked arrays if necessary
        chunked_samples = samples_col.combine_chunks()
        
        # Extract underlying values buffer
        values = chunked_samples.values.to_numpy()
        
        # Calculate dimensions
        n_traces = len(table)
        if n_traces == 0:
            return np.empty((0, 0), dtype=np.float32)
            
        n_samples = len(values) // n_traces
        return values.reshape(n_traces, n_samples)

    def read_headers(self, table: Optional[pa.Table] = None) -> pd.DataFrame:
        """
        Extract Pandas DataFrame of trace header columns (excluding 'samples').
        
        Args:
            table: Loaded PyArrow table. If None, reads full table headers.
            
        Returns:
            Pandas DataFrame containing scalar trace headers.
        """
        if table is None:
            # Read all columns except samples if possible, or read table
            table = self.read_table()
            
        header_cols = [c for c in table.column_names if c != "samples"]
        return table.select(header_cols).to_pandas()
