import io
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from pyseis_io.core.writer import InternalFormatWriter
from pyseis_io.core.reader import InternalFormatReader

def test_writer_and_reader_file_roundtrip(tmp_path):
    out_file = tmp_path / "test_dataset.parquet"
    
    # 50 traces x 1000 samples
    traces_in = np.random.randn(50, 1000).astype(np.float32)
    headers_in = pd.DataFrame({
        "shot_number": np.repeat([1, 2, 3, 4, 5], 10),
        "channel_number": np.tile(np.arange(1, 11), 5),
        "offset": np.linspace(50.0, 500.0, 50, dtype=np.float32)
    })
    meta_in = {
        "sample_rate": 0.002,
        "domain": "time",
        "survey": {"name": "UnitTestSurvey"}
    }
    
    # Write
    writer = InternalFormatWriter(out_file)
    res_path = writer.write(traces_in, headers_in, meta_in)
    assert Path(res_path).exists()
    
    # Read metadata footer
    reader = InternalFormatReader(out_file)
    meta_out = reader.read_metadata()
    assert meta_out["sample_rate"] == 0.002
    assert meta_out["domain"] == "time"
    assert meta_out["survey"]["name"] == "UnitTestSurvey"
    assert meta_out["n_traces"] == 50
    assert meta_out["n_samples"] == 1000
    
    # Read full traces (zero copy 2D numpy view)
    traces_out = reader.read_traces()
    assert traces_out.shape == (50, 1000)
    np.testing.assert_allclose(traces_out, traces_in, rtol=1e-6)
    
    # Read headers
    headers_out = reader.read_headers()
    assert len(headers_out) == 50
    assert list(headers_out["shot_number"]) == list(headers_in["shot_number"])

def test_in_memory_bytesio_roundtrip():
    traces_in = np.random.randn(20, 500).astype(np.float32)
    headers_in = pd.DataFrame({
        "shot_number": [10] * 20,
        "channel_number": np.arange(1, 21)
    })
    meta_in = {"sample_rate": 0.001}
    
    buf = io.BytesIO()
    writer = InternalFormatWriter(buf)
    writer.write(traces_in, headers_in, meta_in)
    
    # Read back from buffer (Zero Disk I/O!)
    reader = InternalFormatReader(buf)
    meta_out = reader.read_metadata()
    assert meta_out["sample_rate"] == 0.001
    
    traces_out = reader.read_traces()
    assert traces_out.shape == (20, 500)
    np.testing.assert_allclose(traces_out, traces_in, rtol=1e-6)

def test_predicate_pushdown_filtering(tmp_path):
    out_file = tmp_path / "shot_dataset.parquet"
    
    traces_in = np.random.randn(40, 200).astype(np.float32)
    headers_in = pd.DataFrame({
        "shot_number": np.repeat([100, 200, 300, 400], 10),
        "offset": np.linspace(10, 400, 40)
    })
    
    writer = InternalFormatWriter(out_file)
    writer.write(traces_in, headers_in)
    
    # Read only Shot 200 via predicate pushdown
    reader = InternalFormatReader(out_file)
    table_shot200 = reader.read_table(filters=[("shot_number", "==", 200)])
    
    assert len(table_shot200) == 10
    traces_shot200 = reader.read_traces(table_shot200)
    assert traces_shot200.shape == (10, 200)
    np.testing.assert_allclose(traces_shot200, traces_in[10:20], rtol=1e-6)
