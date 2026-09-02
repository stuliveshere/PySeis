"""
Automated corpus tests for scraped real-world SEG-Y files in data/segy.
Tests the complete pipeline: Read SEG-Y -> Write Parquet -> Read Parquet -> Write SEG-Y -> Verify Propagation.
"""

import pytest
import numpy as np
from pathlib import Path

from pyseis_io.segy import SEGYReader, SEGYImporter, SEGYExporter
from pyseis_io.core.dataset import SeismicData

def get_scraped_segy_files():
    data_dir = Path(__file__).parent.parent.parent / "data" / "segy"
    if not data_dir.exists():
        return []
    return [f for f in data_dir.iterdir() if f.is_file() and f.suffix.lower() in (".segy", ".sgy")]


def test_scraped_segy_corpus(tmp_path):
    files = get_scraped_segy_files()
    if not files:
        pytest.skip("No scraped SEG-Y files found in data/segy directory")

    for idx, orig_segf in enumerate(files):
        # 1. Read Original SEG-Y & Probe
        with SEGYReader(orig_segf) as orig_reader:
            orig_probe = orig_reader.probe()
            assert orig_probe["num_traces"] >= 0
            assert orig_probe["samples_per_trace"] > 0
            assert orig_probe["sample_interval_us"] > 0

            if orig_probe["num_traces"] == 0:
                continue

            orig_hdr_bytes, orig_samples_first = orig_reader.read_trace(0)
            assert len(orig_hdr_bytes) == 240
            assert len(orig_samples_first) == orig_probe["samples_per_trace"]

            _, orig_all_samples = orig_reader.read_all_traces()

        # 2. Import into Parquet (.seis)
        importer = SEGYImporter(orig_segf)
        scan_df = importer.scan()
        assert len(scan_df) == orig_probe["num_traces"]

        parquet_path = tmp_path / f"dataset_{idx}.seis"
        ds = importer.import_data(parquet_path)
        assert ds.n_traces == orig_probe["num_traces"]
        assert ds.n_samples == orig_probe["samples_per_trace"]

        # 3. Read Parquet & Export to final SEG-Y file
        exported_segy_path = tmp_path / f"reexported_{idx}.segy"
        exporter = SEGYExporter(ds)
        exporter.export(exported_segy_path)

        assert exported_segy_path.exists()

        # 4. Read final SEG-Y & Verify Header / Amplitude Propagation
        with SEGYReader(exported_segy_path) as final_reader:
            final_probe = final_reader.probe()
            assert final_probe["num_traces"] == orig_probe["num_traces"]
            assert final_probe["samples_per_trace"] == orig_probe["samples_per_trace"]
            assert final_probe["sample_interval_us"] == orig_probe["sample_interval_us"]

            _, final_all_samples = final_reader.read_all_traces()
            np.testing.assert_allclose(orig_all_samples, final_all_samples, rtol=1e-4, atol=1e-4)

        # 5. Verify Header Propagation via SEGYImporter on final file
        final_importer = SEGYImporter(exported_segy_path)
        final_scan_df = final_importer.scan()
        assert len(final_scan_df) == len(scan_df)

        # Check core header column propagation
        for col in ("file_number", "channel_number", "source_x", "receiver_x", "fldr", "tracf", "sx", "gx"):
            if col in scan_df.columns and col in final_scan_df.columns:
                np.testing.assert_allclose(
                    scan_df[col].values,
                    final_scan_df[col].values,
                    rtol=1e-3,
                    err_msg=f"Header column '{col}' mismatch after roundtrip"
                )
