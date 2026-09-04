# PySeis

A fast, flexible, and schema-driven Python library for seismic data I/O and processing.

---

## History & Origins

`pyseis` began around 2011 as a collection of Python modules designed to run inline with Seismic Unix (SU). Over time, it expanded into a broad set of scripts and processing functions, but lacked a cohesive overall structure. That original codebase is archived and still available at [PySeis-archive](https://github.com/stuliveshere/PySeis-archive).

It was ultimately decided to re-implement `pyseis` from the ground up with a dedicated focus on **I/O to and from various seismic file formats**—making seismic data seamlessly available in standard **Pandas DataFrames** and **NumPy arrays**.

---

## Design Philosophy

### 1. Zero I/O Re-Invention
`pyseis` is fundamentally an I/O library. Its primary goal is to eliminate the boilerplate of parsing binary seismic streams so that data can be read directly into **2D NumPy arrays** (for trace amplitudes) and **Pandas DataFrames** (for headers), modified in some way, and then written back out to a seismic file.

### 2. Layered YAML Schema Architecture
To achieve both flexibility and speed, `pyseis` uses a hierarchical chain of human-editable YAML files:
1. **Base Standard YAML**: Official SEG specifications (e.g., SEG-D Rev 0.0, 1.0, 2.1, 3.1, SEG-Y Rev 0–2).
2. **Manufacturer Overrides**: Hardware-specific quirks (e.g., Sercel, SmartSolo).
3. **Custom / Field Overrides**: User-defined header fields and runtime extensions.

At runtime, `pyseis` compiles these nested YAML definitions directly into optimized NumPy `dtype` structures for high-speed byte parsing without sacrificing customizability.

Schemas can be easily modified or added, and the schema methodology is easily expanded to other file formats.

### 3. Managing Data Scale: RAM Buffers & Optional Parquet Storage
Seismic datasets are often massive and rarely fit entirely in system memory. While processing in chunks (e.g., gather by gather) works well, constantly parsing and writing raw SEG-Y or SEG-D files imposes severe I/O overheads.

To address scale efficiently:
- **Direct Memory Buffers**: `pyseis` reads directly from SEG-Y/SEG-D into in-memory Pandas and NumPy structures for lightweight workflows.
- **Internal Parquet Format**: For persistent storage, `pyseis` includes an optional **Single-Parquet dataset format**. Built on Apache Arrow, it delivers instant header slicing, native Pandas integration, and predicate pushdown gather filtering without the overhead of legacy binary formats.

---

## Key Features

- **Multi-Format Support**: SEG-Y, SEG-D (Rev 0.0–3.1), Seismic Unix (SU), JavaSeis, and RSF.
- **Nested YAML Schemas**: Fully customizable header definitions and manufacturer profiles compiled to NumPy `dtype`s.
- **In-Memory & Persistent Storage**: Work directly with RAM buffers or save to single-file Parquet datasets.
- **Gather-Optimized Filtering**: Fast predicate pushdown queries for Shot, CDP, Receiver, and Offset gathers.
- **GIS Export & Interactive QC**: Export geometry to GeoPackage (`.gpkg`) and inspect gathers interactively with `pyseis-view`.

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

### 4. Custom Header Locations & Mappings

`pyseis` allows overriding or specifying custom byte locations for non-standard or proprietary header words during import:

#### SEG-Y Custom Header Location
Map raw SEG-Y header fields or non-standard byte locations to custom DataFrame column names using `custom_mappings`:

```python
from pyseis.segy.importer import SEGYImporter

# Map trace header keys (e.g. 'tracl', 'fldr') to custom column names
custom_segy_mappings = [
    {"segy_key": "tracl", "header_name": "custom_trace_seq"},
    {"segy_key": "fldr", "header_name": "custom_field_record"},
]

importer = SEGYImporter("input_data.sgy", custom_mappings=custom_segy_mappings)
sd = importer.read()
print(sd.headers[["custom_trace_seq", "custom_field_record"]].head())
```

#### SEG-D Custom Header Location
Specify arbitrary byte offsets, lengths, data types, and scale factors within trace header blocks (e.g., `demux_trace_header` or trace extension blocks) using `custom_mappings`:

```python
from pyseis.segd.importer import SEGDImporter

# Extract custom fields from specific byte offsets in the trace header
custom_segd_mappings = [
    {
        "header_name": "custom_shot_id",
        "block_role": "demux_trace_header",  # or trace extension block
        "offset": 0,                         # Byte offset within header block
        "length": 2,                         # Byte length (e.g. 2 for uint16/int16, 4 for uint32/int32)
        "type": "uint16",                    # Data type: uint8/16/32, int8/16/32, ieee_float, bcd_digits, etc.
        "scale": 1.0                         # Optional multiplier
    },
    {
        "header_name": "custom_sensor_code",
        "block_role": "demux_trace_header",
        "offset": 12,
        "length": 4,
        "type": "int32"
    }
]

importer = SEGDImporter("shot_gather.segd", custom_mappings=custom_segd_mappings)
sd = importer.read()
print(sd.headers[["custom_shot_id", "custom_sensor_code"]].head())
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
