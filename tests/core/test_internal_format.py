import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from pyseis.core.writer import InternalFormatWriter
from pyseis.core.reader import InternalFormatReader
from pyseis.core.dataset import SeismicData

@pytest.fixture
def temp_dataset_path(tmp_path: Path) -> Path:
    """Returns a path to a temporary dataset parquet file."""
    return tmp_path / "test_dataset.parquet"

def test_create_and_read_single_parquet_dataset(temp_dataset_path: Path):
    n_traces, n_samples = 20, 100
    traces_in = np.random.randn(n_traces, n_samples).astype(np.float32)
    headers_in = pd.DataFrame({
        "shot_number": np.repeat([1, 2], 10),
        "channel_number": np.tile(np.arange(1, 11), 2),
        "offset": np.linspace(100.0, 1000.0, 20, dtype=np.float32)
    })
    meta_in = {"sample_rate": 0.002, "domain": "time"}

    writer = InternalFormatWriter(temp_dataset_path, overwrite=True)
    writer.write(traces_in, headers_in, meta_in)

    assert temp_dataset_path.exists()

    sd = SeismicData.open(temp_dataset_path)
    assert sd.n_traces == n_traces
    assert sd.n_samples == n_samples
    assert sd.sample_rate == 0.002
    np.testing.assert_allclose(sd.data, traces_in, rtol=1e-6)

def test_gather_filtering_on_single_parquet(temp_dataset_path: Path):
    traces_in = np.random.randn(30, 50).astype(np.float32)
    headers_in = pd.DataFrame({
        "shot_number": np.repeat([10, 20, 30], 10),
        "channel_number": np.tile(np.arange(1, 11), 3)
    })

    writer = InternalFormatWriter(temp_dataset_path, overwrite=True)
    writer.write(traces_in, headers_in)

    sd = SeismicData.open(temp_dataset_path)
    
    # Filter shot 20
    shot_20 = sd.filter(shot_number=20)
    assert shot_20.n_traces == 10
    np.testing.assert_allclose(shot_20.data, traces_in[10:20], rtol=1e-6)

def test_overwrite_protection(temp_dataset_path: Path):
    traces = np.random.randn(10, 20).astype(np.float32)
    headers = pd.DataFrame({"shot_number": np.arange(10)})

    writer1 = InternalFormatWriter(temp_dataset_path, overwrite=True)
    writer1.write(traces, headers)

    # Overwrite = False raises FileExistsError
    with pytest.raises(FileExistsError):
        writer2 = InternalFormatWriter(temp_dataset_path, overwrite=False)
