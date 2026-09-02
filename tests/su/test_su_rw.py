"""
Tests for SU Reader and Writer.
"""

import os
import struct
import pytest
import numpy as np
import pandas as pd
import yaml
from pathlib import Path

from pyseis.su.importer import SUImporter
from pyseis.su.exporter import SUExporter
from pyseis.core.dataset import SeismicData

@pytest.fixture
def synthetic_data_dummy():
    # Placeholder to keep pytest happy if it processes imports before conftest? 
    # No, conftest fixtures are global. Just remove it.
    pass


def test_su_interactive_workflow(synthetic_data, tmp_path):
    """Test Scan -> Modify -> Convert workflow."""
    su_path = tmp_path / "interactive.su"
    output_seis = tmp_path / "interactive_output.seis"
    
    # 0. Prep: Export to SU
    writer = SUExporter(synthetic_data)
    writer.export(su_path)
    
    # 1. Initialize
    importer = SUImporter(su_path)
    
    # 2. Scan
    df = importer.scan()
    assert df is not None
    assert len(df) == 10
    assert 'trwf' in df.columns
    # Check default population if it was missing in SU (SU doesn't strictly have this)
    # Our fixture put it in, but SU export maps 'trwf' -> trace_weighting_factor.
    # If not mapped, it would be default. 'trwf' is in SU_TO_SEISDATA.
    
    # 3. Modify
    # Change first trace weighting
    df['trwf'] = df['trwf'].astype(float)
    df.loc[0, 'trwf'] = 0.5
    
    # 4. Convert
    importer.import_data(output_seis)
    
    # 5. Verify
    sd = SeismicData.open(output_seis)
    h = sd.headers
    
    assert h.loc[0, 'trace_weighting_factor'] == 0.5
    # Check data integrity (first sample)
    # We need to compare with original
    sd_orig = SeismicData.open(synthetic_data)
    np.testing.assert_allclose(sd.data[0].compute(), sd_orig.data[0].compute(), rtol=1e-5)

def test_su_validation_trace_count(synthetic_data, tmp_path):
    """Verify error if trace count changes."""
    su_path = tmp_path / "validation.su"
    writer = SUExporter(synthetic_data)
    writer.export(su_path)
    
    importer = SUImporter(su_path)
    df = importer.scan()
    
    # Drop a row
    importer.headers = df.drop(0)
    
    with pytest.raises(ValueError, match="Header count mismatch"):
        importer.import_data(tmp_path / "fail.seis")

def test_su_roundtrip(synthetic_data, tmp_path):
    """Test full roundtrip: Internal -> SU -> Internal."""
    su_path = tmp_path / "test.su"
    output_internal_path = tmp_path / "restored_internal"
    
    # 1. Export to SU
    writer = SUExporter(synthetic_data)
    writer.export(su_path)
    
    assert su_path.exists()
    assert su_path.stat().st_size > 0
    
    # 2. Convert back to Internal (Legacy style calling scan implicitly? No, must call scan)
    importer = SUImporter(su_path)
    importer.scan() # Required now
    importer.import_data(output_internal_path)
    
    assert output_internal_path.exists()
    
    # 3. Compare
    sd_original = SeismicData.open(synthetic_data)
    sd_restored = SeismicData.open(output_internal_path)
    
    # Compare data
    np.testing.assert_allclose(sd_original.data.compute(), sd_restored.data.compute(), rtol=1e-5)
    
    # Compare headers
    h_orig = sd_original.headers
    h_rest = sd_restored.headers
    
    # Check trace_sequence_number
    # Relax dtype check because SU uses int32 but InternalFormat might load as int64
    pd.testing.assert_series_equal(h_orig['trace_sequence_number'], h_rest['trace_sequence_number'], check_names=False, check_dtype=False)
    np.testing.assert_allclose(h_orig['source_x'], h_rest['source_x'])

def test_endian_detection(tmp_path):
    """Test automatic endianness detection."""
    # Create a dummy SU file with Big Endian headers
    su_path = tmp_path / "big_endian.su"
    
    ns = 100
    dt = 4000 # 4ms
    
    with open(su_path, 'wb') as f:
        # Create header
        # ns at 114 (2 bytes), dt at 116 (2 bytes)
        header = bytearray(240)
        struct.pack_into('>H', header, 114, ns)
        struct.pack_into('>H', header, 116, dt)
        f.write(header)
        
        # Write some data (big endian floats)
        data = np.zeros(ns, dtype='>f4')
        f.write(data.tobytes())
        
    importer = SUImporter(su_path)
    # The scan method detects, but sets internal state _endian
    importer.scan() 
    assert importer._endian == '>'
        
    # Test Little Endian
    su_path_le = tmp_path / "little_endian.su"
    with open(su_path_le, 'wb') as f:
        header = bytearray(240)
        struct.pack_into('<H', header, 114, ns)
        struct.pack_into('<H', header, 116, dt)
        f.write(header)
        data = np.zeros(ns, dtype='<f4')
        f.write(data.tobytes())
        
    converter_le = SUImporter(su_path_le)
    converter_le.scan()
    assert converter_le._endian == '<'

def test_su_chunked_conversion(tmp_path, synthetic_data):
    """Test SU conversion with small chunks to force multiple loops."""
    su_file = tmp_path / "test_chunked.su"
    seis_path = tmp_path / "test_chunked.seis"
    
    # Write synthetic SU file
    writer = SUExporter(synthetic_data)
    writer.export(su_file)
    
    # Convert with small chunk size (e.g. 2 traces per chunk)
    importer = SUImporter(su_file)
    importer.scan()
    importer.import_data(seis_path, chunk_size=2)
    
    # Verify
    sd = SeismicData.open(seis_path)
    assert sd.n_traces == 10
    # Data check
    # synthetic_data is SeismicData object or dict? 
    # In other tests: `sd_original = SeismicData.open(synthetic_data)` implies synthetic_data is a PATH fixture.
    # Ah, `synthetic_data` fixture from `conftest` usually returns a PATH if implemented standardly.
    # Let's check `test_su_roundtrip`: `sd_original = SeismicData.open(synthetic_data)`
    # So `synthetic_data` is a path to a .seis dataset.
    
    sd_orig = SeismicData.open(synthetic_data)
    np.testing.assert_allclose(sd.data[:].compute(), sd_orig.data[:].compute(), rtol=1e-5)
    sd.close()

def test_seismic_data_summary(tmp_path, synthetic_data):
    """Test the summary method."""
    seis_path = tmp_path / "test_summary.seis"
    
    # Create dataset manually or just use synthetic_data directly?
    # synthetic_data path works.
    sd = SeismicData.open(synthetic_data)
    summary = sd.summary()
    print(summary)
    
    assert "SeismicData Summary:" in summary
    assert "Traces: 10" in summary
    # Sample rate from fixture? Default usually 4000us (0.004s).
    # Since we fixed units convention, it should say 4000.00 us.
    assert "us" in summary
    
    sd.close()
