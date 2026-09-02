"""
Core data models and high-level SeismicData interface for pyseis.
"""

import io
from pathlib import Path
from typing import Optional, Union, Tuple, List, Dict, Any
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .reader import InternalFormatReader
from .writer import InternalFormatWriter

class SeismicArray(np.ndarray):
    """
    Subclass of np.ndarray providing a no-op .compute() method for backwards-compatibility.
    """
    def compute(self):
        return np.asarray(self)

class SeismicData:
    """
    High-level, unified container for seismic trace data, headers, and metadata.
    Backed by Apache Arrow Tables for zero-copy 2D NumPy array access and fast gather filtering.
    """

    def __init__(
        self,
        table: pa.Table,
        metadata: Optional[Dict[str, Any]] = None,
        source_path: Optional[Union[str, Path]] = None
    ):
        """
        Initialize a SeismicData instance.
        
        Args:
            table: PyArrow Table containing trace vector column 'samples' and header columns.
            metadata: Dataset metadata dictionary.
            source_path: Optional file path origin.
        """
        if not isinstance(table, pa.Table):
            raise TypeError("table must be a PyArrow Table")
            
        self.table = table
        self.source_path = Path(source_path) if source_path else None
        
        # Extract metadata from table schema or argument
        if metadata is not None:
            self.metadata = metadata
        else:
            from .footer_metadata import decode_footer_metadata
            self.metadata = decode_footer_metadata(table.schema.metadata)
            
        # Inspect trace vector type for n_samples
        if "samples" in table.column_names:
            samples_type = table.schema.field("samples").type
            if isinstance(samples_type, pa.FixedSizeListType):
                self._n_samples = samples_type.list_size
            else:
                self._n_samples = self.metadata.get("n_samples", 0)
        else:
            self._n_samples = self.metadata.get("n_samples", 0)

    @property
    def n_traces(self) -> int:
        """Total number of traces in this view."""
        return len(self.table)

    @property
    def n_samples(self) -> int:
        """Number of time samples per trace."""
        return self._n_samples

    @property
    def sample_rate(self) -> float:
        """Sample interval in seconds (e.g. 0.002 for 2ms)."""
        return float(self.metadata.get("sample_rate", 0.002))

    @property
    def provenance(self) -> List[Dict[str, Any]]:
        """List of provenance history events."""
        return self.metadata.get("provenance", [])

    @property
    def data(self) -> np.ndarray:
        """
        Extract 2D NumPy array of trace amplitudes (n_traces, n_samples).
        Zero-copy view backed by PyArrow memory buffers.
        """
        if "samples" not in self.table.column_names or len(self.table) == 0:
            arr = np.empty((0, self.n_samples), dtype=np.float32)
        else:
            chunked = self.table["samples"].combine_chunks()
            values = chunked.values.to_numpy()
            arr = values.reshape(self.n_traces, self.n_samples)
        return arr.view(SeismicArray)

    @property
    def headers(self) -> pd.DataFrame:
        """
        Materialize scalar trace headers as a Pandas DataFrame (excluding 'samples').
        """
        header_cols = [c for c in self.table.column_names if c != "samples"]
        if not header_cols:
            return pd.DataFrame(index=range(self.n_traces))
        return self.table.select(header_cols).to_pandas()

    def filter(self, **kwargs) -> 'SeismicData':
        """
        Filter traces by exact header match (e.g. sd.filter(shot_number=105, cdp=1200)).
        
        Args:
            **kwargs: Header key-value pairs to match.
            
        Returns:
            SeismicData: Filtered view of dataset.
        """
        if not kwargs:
            return self
            
        # Build Arrow expression / filter mask
        mask = None
        for col, val in kwargs.items():
            if col not in self.table.column_names:
                raise KeyError(f"Header column '{col}' not found in dataset schema")
            col_array = self.table[col]
            expr = pa.compute.equal(col_array, val)
            mask = expr if mask is None else pa.compute.and_(mask, expr)
            
        filtered_table = self.table.filter(mask)
        return SeismicData(filtered_table, metadata=self.metadata, source_path=self.source_path)

    def __getitem__(self, key: Union[int, slice]) -> 'SeismicData':
        """
        Slice the dataset along the trace dimension.
        
        Returns a new SeismicData view.
        """
        if isinstance(key, slice):
            start, stop, step = key.indices(self.n_traces)
            length = max(0, stop - start)
            sliced_table = self.table.slice(start, length)
            if step != 1 and len(sliced_table) > 0:
                indices = pa.array(np.arange(0, len(sliced_table), step))
                sliced_table = sliced_table.take(indices)
            return SeismicData(sliced_table, metadata=self.metadata, source_path=self.source_path)
        elif isinstance(key, int):
            if key < 0:
                key += self.n_traces
            if key < 0 or key >= self.n_traces:
                raise IndexError("Trace index out of range")
            sliced_table = self.table.slice(key, 1)
            return SeismicData(sliced_table, metadata=self.metadata, source_path=self.source_path)
        else:
            raise TypeError("Index must be an integer or slice")

    def compute(self) -> Tuple[np.ndarray, pd.DataFrame]:
        """
        Return the 2D trace amplitude array and headers DataFrame.
        """
        return self.data, self.headers

    @classmethod
    def open(
        cls,
        source: Union[str, Path, io.BytesIO, pa.Buffer],
        filters: Optional[List[Union[Tuple, List[Tuple]]]] = None
    ) -> 'SeismicData':
        """
        Open a single-Parquet dataset from disk file or in-memory buffer.
        
        Args:
            source: Path to .parquet file or in-memory byte buffer.
            filters: Optional Parquet predicate pushdown filter list.
            
        Returns:
            SeismicData: The loaded dataset instance.
        """
        reader = InternalFormatReader(source)
        table = reader.read_table(filters=filters)
        metadata = reader.read_metadata()
        source_path = str(source) if isinstance(source, (str, Path)) else None
        return cls(table, metadata=metadata, source_path=source_path)

    @classmethod
    def from_buffer(cls, buffer: Union[bytes, io.BytesIO]) -> 'SeismicData':
        """
        Construct SeismicData directly from an in-memory byte buffer (zero-disk I/O).
        
        Args:
            buffer: In-memory bytes or BytesIO stream.
            
        Returns:
            SeismicData instance.
        """
        return cls.open(buffer)

    @classmethod
    def create(
        cls,
        traces: np.ndarray,
        headers: pd.DataFrame,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'SeismicData':
        """
        Create an in-memory SeismicData instance from trace arrays and headers.
        
        Args:
            traces: 2D NumPy array (n_traces, n_samples).
            headers: Pandas DataFrame of scalar headers.
            metadata: Dataset metadata dict.
            
        Returns:
            SeismicData instance.
        """
        buf = io.BytesIO()
        writer = InternalFormatWriter(buf)
        writer.write(traces, headers, metadata)
        return cls.from_buffer(buf)

    def save(
        self,
        destination: Union[str, Path, io.BytesIO],
        overwrite: bool = True,
        compression: str = "zstd"
    ) -> Union[str, Path, io.BytesIO]:
        """
        Save the dataset to disk or an in-memory byte buffer.
        
        Args:
            destination: File path or BytesIO buffer.
            overwrite: If True, overwrite existing destination file.
            compression: Parquet compression algorithm ('zstd', 'snappy', etc.).
            
        Returns:
            Destination path or buffer.
        """
        writer = InternalFormatWriter(destination, overwrite=overwrite)
        return writer.write(
            traces=self.data,
            headers=self.headers,
            metadata=self.metadata,
            compression=compression
        )

    def to_buffer(self) -> io.BytesIO:
        """
        Export dataset to an in-memory BytesIO buffer (RAM-only).
        
        Returns:
            io.BytesIO containing valid Parquet dataset bytes.
        """
        buf = io.BytesIO()
        self.save(buf)
        buf.seek(0)
        return buf

    def close(self) -> None:
        """
        Release any open resources (no-op for Arrow table views).
        """
        pass

    def summary(self) -> str:
        """
        Return a human-readable textual summary of the dataset.
        """
        lines = [
            "SeismicData Summary:",
            "-------------------",
            f"Source: {self.source_path or 'In-Memory Buffer'}",
            f"Traces: {self.n_traces}",
            f"Samples: {self.n_samples}",
            f"Sample Rate: {self.sample_rate * 1e6:.2f} us ({self.sample_rate * 1000.0:.2f} ms / {self.sample_rate:.4f} s)",
            f"Duration: {self.n_samples * self.sample_rate:.2f} s",
            f"Raw Size: {(self.n_traces * self.n_samples * 4) / (1024 * 1024):.2f} MB",
            "",
            "Header Columns:",
            ", ".join([c for c in self.table.column_names if c != "samples"]) or "(None)"
        ]
        return "\n".join(lines)
