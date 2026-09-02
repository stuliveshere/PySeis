"""
Automated corpus tests for scraped real-world SEG-D files in data/segd.
Tests the complete pipeline: Read SEG-D -> Write Parquet -> Read Parquet -> Write SEG-D -> Verify Propagation.
"""

import pytest
import numpy as np
from pathlib import Path

from pyseis_io.segd import SEGDReader, SEGDImporter, SEGDExporter
from pyseis_io.core.dataset import SeismicData

def get_scraped_segd_files():
    data_dir = Path(__file__).parent.parent.parent / "data" / "segd"
    if not data_dir.exists():
        return []
    return [f for f in data_dir.iterdir() if f.is_file() and f.suffix.lower() in (".segd", ".sgd", ".raw")]


def test_scraped_segd_corpus(tmp_path):
    files = get_scraped_segd_files()
    if not files:
        pytest.skip("No scraped SEG-D files found in data/segd directory")

    for idx, orig_segf in enumerate(files):
        # 1. Read Original SEG-D & Probe
        with SEGDReader(orig_segf) as orig_reader:
            orig_probe = orig_reader.probe()
            assert orig_probe["num_traces"] >= 0
            assert orig_probe["samples_per_trace"] > 0
            assert orig_probe["sample_interval_us"] > 0

            if orig_probe["num_traces"] == 0:
                continue

            orig_hdr_bytes, orig_samples_first = orig_reader.read_trace(0)
            assert len(orig_hdr_bytes) >= 32
            assert len(orig_samples_first) == orig_probe["samples_per_trace"]

            _, orig_all_samples = orig_reader.read_all_traces()

        # 2. Import into Parquet (.seis)
        importer = SEGDImporter(orig_segf)
        scan_df = importer.scan()
        assert len(scan_df) == 1
        assert scan_df["status"].iloc[0] == "GOOD"
        assert scan_df["num_traces"].iloc[0] == orig_probe["num_traces"]

        parquet_path = tmp_path / f"dataset_segd_{idx}.seis"
        ds = importer.import_data(parquet_path)
        assert ds.n_traces == len(orig_all_samples)
        assert ds.n_samples == orig_probe["samples_per_trace"]

        # 3. Read Parquet & Export to final SEG-D file
        exported_segd_path = tmp_path / f"reexported_{idx}.segd"
        exporter = SEGDExporter(ds)
        exporter.export(exported_segd_path)

        assert exported_segd_path.exists()

        # 4. Read final SEG-D & Verify Header / Amplitude Propagation
        with SEGDReader(exported_segd_path) as final_reader:
            final_probe = final_reader.probe()
            assert final_probe["num_traces"] == len(orig_all_samples)
            assert final_probe["samples_per_trace"] == orig_probe["samples_per_trace"]
            assert final_probe["sample_interval_us"] == orig_probe["sample_interval_us"]

            _, final_all_samples = final_reader.read_all_traces()
            np.testing.assert_allclose(orig_all_samples, final_all_samples, rtol=1e-4, atol=1e-4)

        # 5. Verify Header Propagation via SEGDImporter on final file
        final_importer = SEGDImporter(exported_segd_path)
        final_scan_df = final_importer.scan()
        assert len(final_scan_df) == 1
        assert final_scan_df["num_traces"].iloc[0] == len(orig_all_samples)
