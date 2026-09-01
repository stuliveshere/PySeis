import io
import numpy as np
import pandas as pd
import pytest

from pyseis_io.core.dataset import SeismicData

def test_seismic_data_create_and_properties():
    traces = np.random.randn(30, 400).astype(np.float32)
    headers = pd.DataFrame({
        "shot_number": np.repeat([1, 2, 3], 10),
        "offset": np.linspace(100, 1000, 30)
    })
    meta = {"sample_rate": 0.002, "domain": "time"}
    
    sd = SeismicData.create(traces, headers, meta)
    
    assert sd.n_traces == 30
    assert sd.n_samples == 400
    assert sd.sample_rate == 0.002
    assert sd.data.shape == (30, 400)
    assert len(sd.headers) == 30
    np.testing.assert_allclose(sd.data, traces, rtol=1e-6)

def test_seismic_data_filter():
    traces = np.random.randn(30, 400).astype(np.float32)
    headers = pd.DataFrame({
        "shot_number": np.repeat([1, 2, 3], 10),
        "channel_number": np.tile(np.arange(1, 11), 3)
    })
    
    sd = SeismicData.create(traces, headers)
    
    # Filter Shot #2
    shot_2 = sd.filter(shot_number=2)
    assert shot_2.n_traces == 10
    assert shot_2.n_samples == 400
    np.testing.assert_allclose(shot_2.data, traces[10:20], rtol=1e-6)

def test_seismic_data_slice():
    traces = np.random.randn(50, 200).astype(np.float32)
    headers = pd.DataFrame({"shot_number": np.arange(50)})
    
    sd = SeismicData.create(traces, headers)
    
    # Slice first 10 traces
    subset = sd[0:10]
    assert subset.n_traces == 10
    np.testing.assert_allclose(subset.data, traces[0:10], rtol=1e-6)
    
    # Single trace
    single = sd[5]
    assert single.n_traces == 1
    np.testing.assert_allclose(single.data, traces[5:6], rtol=1e-6)

def test_seismic_data_buffer_roundtrip():
    traces = np.random.randn(15, 300).astype(np.float32)
    headers = pd.DataFrame({"channel_number": np.arange(15)})
    meta = {"sample_rate": 0.004}
    
    sd = SeismicData.create(traces, headers, meta)
    
    # Export to RAM buffer
    buf = sd.to_buffer()
    
    # Load from RAM buffer
    sd_mem = SeismicData.from_buffer(buf)
    assert sd_mem.n_traces == 15
    assert sd_mem.n_samples == 300
    assert sd_mem.sample_rate == 0.004
    np.testing.assert_allclose(sd_mem.data, traces, rtol=1e-6)
