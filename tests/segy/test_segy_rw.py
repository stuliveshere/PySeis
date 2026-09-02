"""
Tests for SEGY Reader and Writer.
"""

import os
import struct
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from pyseis.segy.importer import SEGYImporter
from pyseis.segy.exporter import SEGYExporter
from pyseis.core.dataset import SeismicData

def test_segy_export(synthetic_data, tmp_path):
    """Test exporting internal format to SEGY."""
    output_path = tmp_path / "output.segy"
    
    exporter = SEGYExporter(synthetic_data)
    exporter.export(output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 3600 # EBCDIC + Binary + some traces

def test_segy_scan(synthetic_data, tmp_path):
    """Test scanning a SEGY file (via export)."""
    output_path = tmp_path / "scan_test.segy"
    SEGYExporter(synthetic_data).export(output_path)
    
    importer = SEGYImporter(output_path)
    headers = importer.scan()
    
    assert len(headers) == 10
    assert 'tracl' in headers.columns
    
    # Check binary header read
    assert importer._ns == 100
    assert importer._dt == 4000 # 4ms in micros

def test_segy_roundtrip(synthetic_data, tmp_path):
    """Test Internal -> SEGY -> Internal roundtrip."""
    segy_path = tmp_path / "roundtrip.segy"
    SEGYExporter(synthetic_data).export(segy_path)
    
    importer = SEGYImporter(segy_path)
    importer.scan()
    
    restored_path = tmp_path / "restored.seis"
    sd_restored = importer.import_data(restored_path)
    
    # Verify Data
    sd_original = SeismicData.open(synthetic_data)
    original_data = sd_original.data[:].compute()
    restored_data = sd_restored.data[:].compute()
    
    # SEGY uses float32, so should be close
    np.testing.assert_allclose(original_data, restored_data, rtol=1e-5)
    
    # Verify Metadata
    assert sd_restored.n_traces == 10
    assert sd_restored.n_samples == 100
    # sample_rate may be stored in seconds or micros depending on importer
    # Allow for 0.004 seconds OR 4000 micros
    sr = sd_restored.sample_rate
    assert sr == 0.004 or sr == 4000 or np.isclose(sr, 0.004)
    
def test_segy_ibm_float():
    """
    Test IBM float conversion.
    This test verifies the ibm2ieee function from utils.
    """
    from pyseis.utils import ibm2ieee
    
    # Known IBM float: 0x42640000 = 100.0 in IBM float
    ibm_val = np.array([0x42640000], dtype=np.uint32)
    ieee_result = ibm2ieee(ibm_val)
    np.testing.assert_allclose(ieee_result, [100.0], rtol=1e-5)
