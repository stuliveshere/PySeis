import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add src to path so pyseis can be imported
# This is critical for tests to run against the local source code
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def synthetic_data(tmp_path):
    """Create a synthetic SeismicData dataset."""
    n_traces = 10
    n_samples = 100
    sample_rate = 0.004
    
    data = np.random.randn(n_traces, n_samples).astype(np.float32)
    
    # Create headers
    headers = pd.DataFrame({
        'trace_id': np.arange(n_traces),
        'source_id': np.arange(n_traces).astype(str),
        'receiver_id': (np.arange(n_traces) + 100).astype(str),
        'cdp_id': np.arange(n_traces).astype(str),
        'trace_sequence_number': np.arange(n_traces),
        'offset': np.full(n_traces, 100.0),
        'mute_start': np.zeros(n_traces),
        'mute_end': np.zeros(n_traces),
        'total_static': np.zeros(n_traces),
        'trace_identification_code': np.ones(n_traces),
        'correlated': np.zeros(n_traces, dtype=bool),
        'trace_weighting_factor': np.ones(n_traces),
        'source_x': np.arange(n_traces) * 10,
        'source_y': np.zeros(n_traces),
        'receiver_x': np.arange(n_traces) * 10 + 100,
        'receiver_y': np.zeros(n_traces),
        'num_samples': np.full(n_traces, n_samples),
        'sample_rate': np.full(n_traces, int(sample_rate * 1e6)), # micros
        # Add fldr for viewer test
        'fldr': np.array([1, 1, 1, 1, 1, 2, 2, 2, 2, 2]) # 2 groups
    })
    
    # Write to internal format first to get a valid SeismicData on disk
    from pyseis.core.writer import InternalFormatWriter
    
    path = tmp_path / "synthetic_internal.parquet"
    writer = InternalFormatWriter(path, overwrite=True)
    writer.write(data, headers, metadata={"sample_rate": sample_rate})
    
    return path
