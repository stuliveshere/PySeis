# PySeis

A fast, simple, and flexible Python I/O library for seismic data.

## Core Philosophy

`pyseis` is fundamentally an **I/O library** designed to make reading and writing seismic data effortless. It seamlessly converts complex seismic binary formats into native Python data structures—specifically **2D NumPy arrays** for trace amplitudes and **Pandas DataFrames** for trace headers.

By eliminating the need to reinvent I/O for every project, `pyseis` empowers geophysicists, processing engineers, and researchers to focus on writing custom Python scripts for processing, analysis, and visualization.

## Key Capabilities

- **Multi-Format I/O**: Read and write industry-standard seismic formats including **SEG-Y**, **SEG-D** (Rev 0.0–3.1), **Seismic Unix (SU)**, **JavaSeis**, and **RSF (Madagascar)**.
- **YAML-Backed Schemas**: Human-editable YAML schema definitions allow seamless customization for different format versions, manufacturer profiles (e.g., Sercel, SmartSolo), and custom user headers without changing code.
- **Direct Memory & Buffer Access**: Read and write seismic streams directly to/from RAM memory buffers (`io.BytesIO` / `pyarrow.Buffer`) into Pandas DataFrames and NumPy arrays for zero-disk workflows.
- **High-Performance Parquet Storage Engine**: Includes an internal single-file Parquet dataset format (`.parquet`) for persistent, high-performance on-disk storage, feature-rich predicate pushdown gather filtering (Shot, CDP, Receiver), and embedded JSON metadata/provenance lineage.
- **GIS Export & Interactive QC**: Export survey geometries to GeoPackage (`.gpkg`) for QGIS integration, and inspect gathers interactively using the built-in `pyseis-view` CLI viewer.

---

## Installation

```bash
pip install -e .
```

---

## Quick Start

### 1. Reading Seismic Data into Pandas & NumPy

```python
import pyseis as ps

# Read dataset into a SeismicData container
sd = ps.open("my_dataset.parquet")

# 2D NumPy array for amplitudes (shape: n_traces x n_samples)
amplitudes = sd.data

# Pandas DataFrame for trace headers
headers_df = sd.headers

print(f"Traces: {sd.n_traces}, Samples: {sd.n_samples}, dt: {sd.sample_rate}s")
```

### 2. Fast Gather Filtering (Predicate Pushdown)

```python
# Filter Shot Gather #105 instantly without loading unneeded traces
shot_105 = sd.filter(source_id=105)

shot_amplitudes = shot_105.data    # 2D NumPy array
shot_headers = shot_105.headers    # Pandas DataFrame
```

### 3. Converting Formats (e.g. SEG-Y to Parquet)

```python
from pyseis.segy.importer import SEGYImporter

# Import SEG-Y and save as single-file Parquet dataset
importer = SEGYImporter("input_data.sgy")
sd = importer.read()
sd.save("output_data.parquet")
```

---

## Seismic Processing Cookbook

`pyseis` includes a collection of Python recipes for common seismic processing tasks using standard NumPy and SciPy operations:

### Recipe 1: Applying Automatic Gain Control (AGC)

```python
import numpy as np

def apply_agc(data: np.ndarray, window_size: int = 100) -> np.ndarray:
    """Apply RMS Automatic Gain Control along trace samples."""
    gain_data = np.zeros_like(data)
    half_win = window_size // 2
    
    for i in range(data.shape[1]):
        start = max(0, i - half_win)
        end = min(data.shape[1], i + half_win)
        rms = np.sqrt(np.mean(data[:, start:end] ** 2, axis=1, keepdims=True) + 1e-10)
        gain_data[:, i] = data[:, i] / rms.squeeze()
        
    return gain_data

# Apply AGC directly to SeismicData NumPy matrix
agc_amplitudes = apply_agc(sd.data, window_size=150)
```

### Recipe 2: Sorting and Stacking CDP Gathers

```python
# Sort headers and trace amplitudes by CDP and Offset
sorted_indices = sd.headers.sort_values(by=["cdp_id", "offset"]).index
sorted_amplitudes = sd.data[sorted_indices]

# Compute mean stack across traces per CDP
cdp_stack = sd.headers.groupby("cdp_id").apply(
    lambda grp: sd.data[grp.index].mean(axis=0)
)
```

---

## Dataset Architecture

A `pyseis` dataset is stored as a self-contained Parquet file:

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

---

## Package Structure

```
pyseis/
├── core/                  # Single-Parquet engine, dataset model, reader, writer, schema
├── segy/                  # SEG-Y importer/exporter & header mapping
├── segd/                  # SEG-D importer/exporter & multi-revision schemas
├── su/                    # Seismic Unix (SU) importer/exporter
├── javaseis/              # JavaSeis format reader/parser
├── rsf/                   # RSF (Madagascar) format support
├── gpkg/                  # GeoPackage GIS spatial exporter
└── visualization/         # Seismic data viewer & interactive plotting
```

---

## License

GNU Affero General Public License v3.0

## Documentation

For full architectural details and API specification, see [docs/architecture.md](docs/architecture.md).
