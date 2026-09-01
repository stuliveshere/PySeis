# **pyseis-io: Single-Parquet File Format Architecture & API Documentation**

`pyseis-io` defines a **lean, unified, high-performance dataset format** for seismic data built on top of **Apache Arrow and Parquet**:

* **Single-File / Single-Buffer Storage**: A complete seismic dataset resides in a single `.parquet` file (or an in-memory byte buffer).
* **Fixed-Length Vector Traces**: Amplitudes are stored in a `FixedSizeList(Float32, n_samples)` column for zero-copy 2D NumPy matrix access.
* **Integrated Headers**: Trace attributes (`offset`, `cdp`, `source_id`, coordinates) are stored alongside trace vectors in the same Parquet table.
* **Embedded Footer Metadata**: Global attributes (`sample_rate`, domain, spatial CRS) and operation history (`provenance`) are stored as a JSON payload in the Parquet file footer (`key_value_metadata["pyseis_metadata"]`).
* **Zero-Disk / In-Memory Support**: Full support for in-memory stream buffers (`io.BytesIO` / `pyarrow.BufferOutputStream`), enabling RAM-only processing and instant format conversions without filesystem I/O.
* **Predicate Pushdown Gather Access**: Fast filtering and reading of specific gathers (shot, CDP, receiver) leveraging Parquet row group min/max statistics.

---

# 1. Dataset Layout & Storage Engine

Unlike traditional multi-file formats or complex directory trees, a `pyseis-io` dataset is stored as a single self-contained Parquet file:

```
<dataset_name>.parquet
```

Or, for in-memory streaming pipelines, a RAM-resident byte buffer (`io.BytesIO` / `pyarrow.Buffer`).

### **Parquet Table Schema**

Every row in the Parquet table represents **1 seismic trace**:

| Column Name | Apache Arrow Data Type | Description |
| :--- | :--- | :--- |
| **`samples`** | `FixedSizeList(Float32, n_samples)` | Trace amplitude vector of length `n_samples` |
| **`trace_id`** | `Int32` | Unique trace index within dataset |
| **`source_id`** | `Int32` or `String` | Source / Shot identifier |
| **`receiver_id`** | `Int32` or `String` | Receiver identifier |
| **`cdp_id`** | `Int32` | Common Depth Point / Midpoint identifier |
| **`trace_sequence_number`** | `Int32` | Sequence number within gather |
| **`offset`** | `Float32` | Source-to-receiver offset distance |
| **`source_x`**, **`source_y`** | `Float64` | Source coordinates |
| **`receiver_x`**, **`receiver_y`** | `Float64` | Receiver coordinates |
| **`cdp_x`**, **`cdp_y`** | `Float64` | CDP coordinates |
| *...custom headers* | *scalar types* | Any acquisition/processing headers |

---

# 2. File Footer Metadata (`pyseis_metadata`)

Global metadata and operation history are embedded directly into the Parquet file footer's `key_value_metadata` map under the `"pyseis_metadata"` key as a JSON-encoded string.

### **JSON Payload Schema**

```json
{
  "pyseis_version": "2.0.0",
  "sample_rate": 0.002,
  "sample_rate_unit": "seconds",
  "n_samples": 2000,
  "domain": "time",
  "survey": {
    "name": "3D_Survey_Block_A",
    "crs": "EPSG:32631"
  },
  "provenance": [
    {
      "action": "imported_from_segy",
      "timestamp": "2026-09-01T21:30:00Z",
      "user": "geophysicist",
      "source_file": "raw_survey.sgy"
    }
  ]
}
```

Reading dataset metadata requires reading **only the tiny file footer** without loading trace arrays into memory.

---

# 3. Core Modules and API

## **3.1 SeismicData**

Defined in `src/pyseis_io/core/dataset.py`

`SeismicData` is the primary high-level interface for inspecting, filtering, and writing seismic datasets.

### Key Properties

```python
sd.n_traces       # Int: Total number of traces
sd.n_samples      # Int: Number of samples per trace
sd.sample_rate    # Float: Sample interval in seconds (e.g. 0.002)
sd.data           # 2D NumPy Array (N_traces x N_samples), zero-copy view
sd.headers        # Pandas DataFrame of trace header columns
sd.provenance     # List of dicts: Operation history
```

### Factory Methods

```python
# Open from disk file
sd = SeismicData.open("dataset.parquet")

# Open from in-memory byte buffer (Zero Disk I/O)
sd = SeismicData.from_buffer(buffer_or_bytes)
```

### Gather Filtering (Predicate Pushdown)

```python
# Extract Shot Gather #105 using Parquet predicate pushdown
shot_105 = sd.filter(source_id=105)

# Extract CDP Gather #1200
cdp_1200 = sd.filter(cdp_id=1200)
```

### Save / Export

```python
# Save to disk
sd.save("output_dataset.parquet")

# Export to in-memory BytesIO buffer
buf = sd.to_buffer()
```

---

## **3.2 InternalFormatWriter**

Defined in `src/pyseis_io/core/writer.py`

Responsible for building PyArrow Tables with `FixedSizeList` trace arrays, attaching footer metadata, and serializing to disk or RAM buffers.

```python
from pyseis_io.core.writer import InternalFormatWriter

writer = InternalFormatWriter("dataset.parquet")
writer.write(
    traces=traces_2d_array,        # NumPy array (N_traces, N_samples)
    headers=headers_df,            # Pandas DataFrame
    metadata={"sample_rate": 0.002} # Metadata dict
)
```

---

## **3.3 InternalFormatReader**

Defined in `src/pyseis_io/core/reader.py`

Responsible for fast header-only inspection, predicate pushdown gather loading, and extracting zero-copy 2D NumPy array views from `FixedSizeList` trace columns.

```python
from pyseis_io.core.reader import InternalFormatReader

reader = InternalFormatReader("dataset.parquet")
metadata = reader.read_metadata()  # Reads footer only
sd = reader.read()                 # Full or filtered SeismicData
```

---

# 4. Zero-Disk & In-Memory Streaming Workflows

`pyseis-io` supports diskless in-memory format conversions and network streaming:

```python
import io
import pyseis_io as ps

# Read SEG-Y file directly in RAM
segy_reader = ps.SEGYReader("raw_data.sgy")

# Convert to in-memory Parquet buffer (No disk write!)
ram_buffer = segy_reader.to_parquet_buffer()

# Query or load into Pandas / DuckDB straight from RAM
sd = ps.SeismicData.from_buffer(ram_buffer)
shot_gather = sd.filter(source_id=101)
```

---

# 5. Core Design Principles

1. **Single-File Simplicity**: One file per dataset. No multi-file directories, missing manifest errors, or schema copy boilerplate.
2. **Zero-Copy Matrix Access**: `FixedSizeList(Float32)` column layout allows instant 2D NumPy views without `vstack` overhead.
3. **Gather-Optimized**: Parquet row groups aligned with gather keys (e.g. `source_id`, `cdp_id`) enable ultra-fast predicate pushdown reads.
4. **Self-Contained Metadata**: Parquet file footer stores all dataset properties and provenance lineage.
5. **Diskless Execution**: Full support for in-memory stream buffers (`io.BytesIO`) for cloud microservices and interactive notebooks.
