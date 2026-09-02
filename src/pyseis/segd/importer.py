"""
High-Level SEGDImporter for importing external SEG-D files into pyseis single-Parquet datasets.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from pyseis.base import SeismicImporter
from pyseis.core.writer import InternalFormatWriter
from pyseis.core.dataset import SeismicData

from .reader import SEGDReader
from .scanner import CorpusScanner
from .fill_plan import TraceFillPlan
from .schema import SchemaManager, EffectiveSchema

class SEGDImporter(SeismicImporter):
    """
    Reader and importer for SEG-D files converting into pyseis internal .seis format.
    Supports auto-detecting schemas, custom byte mappings, multi-file corpus scanning,
    and global coordinate reference subtractions.
    """

    def __init__(
        self,
        path: Union[str, Path],
        schema: Optional[EffectiveSchema] = None,
        custom_mappings: Optional[List[Dict[str, Any]]] = None,
        global_xref: float = 0.0,
        global_yref: float = 0.0,
        diagnostic_level: str = "strict"
    ):
        self.source_path = Path(path)
        self.schema = schema
        self.custom_mappings = custom_mappings or []
        self.global_xref = global_xref
        self.global_yref = global_yref
        self.diagnostic_level = diagnostic_level.lower()

        self.schema_manager = SchemaManager()
        self.scanner = CorpusScanner(schema_manager=self.schema_manager)

        if self.source_path.is_file():
            self.file_list = [self.source_path]
        elif self.source_path.is_dir():
            self.file_list = list(self.source_path.glob("*.segd"))
            if not self.file_list:
                self.file_list = [f for f in self.source_path.iterdir() if f.is_file() and f.name.lower().endswith(".segd")]
        else:
            raise FileNotFoundError(f"Source path not found: {path}")

        if not self.file_list:
            raise ValueError(f"No SEG-D files found at {path}")

        # Probe first file to extract base timing metadata
        with SEGDReader(self.file_list[0], schema=self.schema, schema_manager=self.schema_manager) as probe_reader:
            self._probe_info = probe_reader.probe()
            self._effective_schema = probe_reader.schema

    def scan(self) -> pd.DataFrame:
        """Perform pre-flight scan across input file(s)."""
        if self.source_path.is_dir():
            return self.scanner.scan_directory(self.source_path, strictness=self.diagnostic_level)
        else:
            res = self.scanner.scan_file(self.source_path)
            return pd.DataFrame([res])

    def import_data(self, output_path: Union[str, Path], chunk_size: int = 1000, **kwargs) -> SeismicData:
        """
        Convert SEG-D file(s) into single-Parquet .seis dataset.
        """
        all_traces: List[np.ndarray] = []
        all_headers: List[pd.DataFrame] = []

        for segd_file in self.file_list:
            with SEGDReader(segd_file, schema=self._effective_schema, schema_manager=self.schema_manager) as reader:
                hdr_bytes_list, samples_arr = reader.read_all_traces()

                # Compile and execute fill plan for headers
                plan = TraceFillPlan(
                    schema=reader.schema,
                    gather_type=reader.record_info.gather_type,
                    custom_mappings=self.custom_mappings,
                    global_xref=self.global_xref,
                    global_yref=self.global_yref
                )
                headers_df = plan.execute_bulk(hdr_bytes_list)
                headers_df["FILENAME"] = segd_file.name

                all_traces.append(samples_arr)
                all_headers.append(headers_df)

        combined_traces = np.vstack(all_traces)
        combined_headers = pd.concat(all_headers, ignore_index=True)

        meta = {
            "sample_rate": self._probe_info["sample_interval_us"] / 1_000_000.0,
            "sample_rate_us": self._probe_info["sample_interval_us"],
            "sample_rate_ms": self._probe_info["sample_interval_us"] / 1000.0,
            "format": "SEG-D",
            "revision": self._probe_info["revision"],
            "manufacturer": self._probe_info["manufacturer"],
            "variant_id": self._probe_info["variant_id"],
            "domain": "time"
        }

        writer = InternalFormatWriter(output_path, overwrite=True)
        writer.write(combined_traces, combined_headers, metadata=meta)

        return SeismicData.open(output_path)

    def read(self) -> SeismicData:
        """
        Convenience method to scan and import data into an in-memory SeismicData object.
        """
        return self.import_data(io.BytesIO())
