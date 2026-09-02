"""
End-to-End integration tests for SEG-D reader, writer, importer, exporter, and scanner.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from pyseis.segd import (
    SEGDWriter,
    SEGDReader,
    SEGDImporter,
    SEGDExporter,
    CorpusScanner
)
from pyseis.core.dataset import SeismicData

def test_segd_write_and_read(tmp_path):
    segd_path = tmp_path / "test_shot.segd"
    
    n_traces = 5
    n_samples = 100
    samples = np.random.randn(n_traces, n_samples).astype(np.float32)

    headers = [
        {"SOU_X": 1000.0 + i, "SOU_Y": 2000.0, "REC_X": 500.0 + i * 10, "REC_Y": 2000.0}
        for i in range(n_traces)
    ]

    writer = SEGDWriter(target=segd_path, format_code=0x8058, sample_interval_us=2000)
    writer.write(samples=samples, headers=headers)

    assert segd_path.exists()

    with SEGDReader(segd_path) as reader:
        probe = reader.probe()
        assert probe["num_traces"] == n_traces
        assert probe["samples_per_trace"] == n_samples
        assert probe["sample_interval_us"] == 2000

        hdr_list, read_samples = reader.read_all_traces()
        assert len(hdr_list) == n_traces
        np.testing.assert_allclose(samples, read_samples, rtol=1e-5)


def test_segd_scanner(tmp_path):
    segd_path = tmp_path / "scan_shot.segd"
    samples = np.zeros((3, 50), dtype=np.float32)
    SEGDWriter(target=segd_path, sample_interval_us=1000).write(samples)

    scanner = CorpusScanner()
    report = scanner.scan_file(segd_path)

    assert report["status"] == "GOOD"
    assert report["num_traces"] == 3
    assert report["sample_interval_us"] == 1000


def test_segd_import_and_export_roundtrip(tmp_path):
    segd_path = tmp_path / "original.segd"
    seis_path = tmp_path / "imported.seis"
    exported_segd = tmp_path / "exported.segd"

    n_traces = 4
    n_samples = 80
    samples = np.random.randn(n_traces, n_samples).astype(np.float32)

    SEGDWriter(target=segd_path, sample_interval_us=2000).write(samples)

    # 1. Import SEG-D -> .seis
    importer = SEGDImporter(segd_path)
    scan_df = importer.scan()
    assert len(scan_df) == 1

    ds = importer.import_data(seis_path)
    assert ds.n_traces == n_traces
    assert ds.n_samples == n_samples

    imported_data = ds.data[:].compute()
    np.testing.assert_allclose(samples, imported_data, rtol=1e-5)

    # 2. Export .seis -> SEG-D
    exporter = SEGDExporter(ds)
    exporter.export(exported_segd)
    assert exported_segd.exists()

    # 3. Read exported SEG-D back
    with SEGDReader(exported_segd) as reader:
        _, re_read_samples = reader.read_all_traces()
        np.testing.assert_allclose(samples, re_read_samples, rtol=1e-5)
