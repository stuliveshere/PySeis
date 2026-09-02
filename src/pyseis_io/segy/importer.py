"""
High-Level SEGYImporter for importing SEG-Y files into pyseis-io single-Parquet datasets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from pyseis_io.base import SeismicImporter
from pyseis_io.core.writer import InternalFormatWriter
from pyseis_io.core.dataset import SeismicData

from .reader import SEGYReader
from .fill_plan import SEGYFillPlan
from .schema import SEGYSchemaManager, SEGYEffectiveSchema

class SEGYImporter(SeismicImporter):
    """
    Reader and importer for SEG-Y files converting into pyseis-io internal .seis format.
    Supports auto-detecting endianness, revision specs, custom header mappings,
    and global coordinate reference subtractions.
    """

    def __init__(
        self,
        path: Union[str, Path],
        header_def: Optional[str] = None,
        mapping_path: Optional[str] = None,
        custom_mappings: Optional[List[Dict[str, Any]]] = None,
        global_xref: float = 0.0,
        global_yref: float = 0.0
    ):
        self.segy_path = Path(path)
        if not self.segy_path.exists():
            raise FileNotFoundError(f"SEG-Y file not found: {path}")

        self.mapping_path = Path(mapping_path) if mapping_path else None
        self.custom_mappings = custom_mappings or []
        self.global_xref = global_xref
        self.global_yref = global_yref

        self.schema_manager = SEGYSchemaManager()

        with SEGD_Or_SEGYReader(self.segy_path, schema_manager=self.schema_manager) as probe_reader:
            self._probe_info = probe_reader.probe()
            self._effective_schema = probe_reader.schema
            self._ns = self._probe_info["samples_per_trace"]
            self._dt = self._probe_info["sample_interval_us"]
            self._format_code = self._probe_info["format_code"]

    def scan(self) -> pd.DataFrame:
        """
        Scan and return trace headers from the SEG-Y file.
        """
        with SEGD_Or_SEGYReader(self.segy_path, schema=self._effective_schema, schema_manager=self.schema_manager) as reader:
            hdr_bytes_list, _ = reader.read_all_traces()
            plan = SEGYFillPlan(
                schema=reader.schema,
                mapping_file=self.mapping_path,
                custom_mappings=self.custom_mappings,
                global_xref=self.global_xref,
                global_yref=self.global_yref
            )
            return plan.extract_headers_bulk(hdr_bytes_list)

    def import_data(self, output_path: Union[str, Path], chunk_size: int = 1000, **kwargs) -> SeismicData:
        """
        Convert SEG-Y file into single-Parquet .seis dataset.
        """
        with SEGD_Or_SEGYReader(self.segy_path, schema=self._effective_schema, schema_manager=self.schema_manager) as reader:
            hdr_bytes_list, samples_arr = reader.read_all_traces()

            plan = SEGYFillPlan(
                schema=reader.schema,
                mapping_file=self.mapping_path,
                custom_mappings=self.custom_mappings,
                global_xref=self.global_xref,
                global_yref=self.global_yref
            )
            headers_df = plan.extract_headers_bulk(hdr_bytes_list)
            headers_df["FILENAME"] = self.segy_path.name

            meta = {
                "sample_rate": reader.record_info.sample_interval_us / 1_000_000.0,
                "sample_rate_us": reader.record_info.sample_interval_us,
                "sample_rate_ms": reader.record_info.sample_interval_us / 1000.0,
                "format": "SEG-Y",
                "revision": reader.record_info.revision,
                "endian": reader.record_info.endian,
                "domain": "time"
            }

            writer = InternalFormatWriter(output_path, overwrite=True)
            writer.write(samples_arr, headers_df, metadata=meta)

        return SeismicData.open(output_path)


# Alias helper to avoid name confusion
SEGD_Or_SEGYReader = SEGYReader
