# pyseis

A standalone I/O library for seismic data featuring a unified, high-performance **Single-Parquet dataset format** with support for industry-standard seismic formats.

## Overview

`pyseis` provides a modern, simplified storage engine for seismic data:

- **Single-Parquet Format**: Entire dataset stored in a single `.parquet` file (or in-memory byte buffer)
- **Zero-Copy Trace Access**: Fixed-length trace vectors stored in Arrow `FixedSizeList` columns for instant 2D NumPy array conversion
- **Gather-Optimized**: Fast predicate pushdown filtering for shot, CDP, and receiver gathers
- **In-Memory / Zero-Disk**: Native support for RAM-only stream buffers (`io.BytesIO` / `pyarrow.BufferOutputStream`)
- **Embedded Metadata**: Global properties (`sample_rate`, domain, spatial CRS) and provenance history stored directly in Parquet file footers
- **Industry Standard Interoperability**: Direct integration with Apache Arrow, Pandas, Polars, DuckDB, SEG-Y, SEG-D, and Seismic Unix (SU)

## Key Features

- **Single-File Simplicity**: One file per dataset—no complex directory trees or schema file bloat.
- **Embedded Footer Metadata**: Dataset properties and audit history stored cleanly in Parquet `key_value_metadata`.
- **Predicate Pushdown Filtering**: Filter gathers by `source_id`, `cdp_id`, or `offset` directly at the I/O layer.
- **Zero-Disk Streaming**: Convert and process datasets in RAM buffers without writing to disk.

## Installation

```bash
pip install -e .
```

## Quick Start

### Creating and Writing a Dataset

```python
import numpy as np
import pandas as pd
from pyseis.core.writer import InternalFormatWriter

# Generate synthetic seismic amplitudes (100 traces x 2000 samples)
traces = np.random.randn(100, 2000).astype(np.float32)

# Generate trace headers
headers = pd.DataFrame({
    "trace_id": np.arange(100, dtype=np.int32),
    "source_id": np.repeat(np.arange(10, dtype=np.int32), 10),
    "receiver_id": np.tile(np.arange(10, dtype=np.int32), 10),
    "cdp_id": np.arange(100, dtype=np.int32),
    "offset": np.linspace(100, 1000, 100, dtype=np.float32)
})

# Write to single Parquet file
writer = InternalFormatWriter("my_dataset.parquet")
writer.write(
    traces=traces,
    headers=headers,
    metadata={"sample_rate": 0.002, "domain": "time"}
)
```

### Reading and Gather Filtering

```python
from pyseis.core.dataset import SeismicData

# Open dataset (reads only tiny file footer instantly)
sd = SeismicData.open("my_dataset.parquet")

print(f"Traces: {sd.n_traces}, Samples per trace: {sd.n_samples}")
print(f"Sample rate: {sd.sample_rate}s")

# Extract Shot Gather #3 using Parquet predicate pushdown (I/O optimization)
shot_3 = sd.filter(source_id=3)

# Instant 2D NumPy array view (zero-copy)
traces_2d = shot_3.data  # Shape: (10, 2000)

# Pandas DataFrame of headers
headers_df = shot_3.headers
```

### Zero-Disk In-Memory Workflows

```python
import io
from pyseis.core.dataset import SeismicData

# Export dataset to an in-memory byte buffer
ram_buffer = sd.to_buffer()

# Open dataset from RAM buffer (zero disk I/O)
sd_mem = SeismicData.from_buffer(ram_buffer)
```

## Dataset Architecture

A dataset is stored as a self-contained Parquet file:

```
my_dataset.parquet
├── Schema:
│   ├── samples: FixedSizeList(Float32, n_samples)
│   ├── trace_id: Int32
│   ├── source_id: Int32 / String
│   ├── receiver_id: Int32 / String
│   └── offset, cdp_id, coordinates...
└── File Footer Metadata (key_value_metadata["pyseis_metadata"]):
    ├── pyseis_version
    ├── sample_rate
    ├── survey / spatial CRS
    └── provenance history
```

## Package Structure

```
pyseis/
├── core/                  # Core single-Parquet engine
│   ├── dataset.py         # SeismicData interface
│   ├── reader.py          # InternalFormatReader & predicate pushdown
│   ├── writer.py          # InternalFormatWriter & PyArrow table builder
│   ├── schema.py          # PyArrow schema generators & validation
│   └── footer_metadata.py # Parquet file footer JSON metadata handler
├── segy/                  # SEG-Y reader/writer support
├── segd/                  # SEG-D reader/writer support
├── su/                    # Seismic Unix support
├── gpkg/                  # GeoPackage GIS exporter
└── legacy/                # Format specs
```

## Development & Testing

```bash
# Run test suite
pytest tests/core/ -v
```

## License

GNU Affero General Public License v3.0

## Documentation

For the full architectural specification, see [docs/architecture.md](docs/architecture.md).
