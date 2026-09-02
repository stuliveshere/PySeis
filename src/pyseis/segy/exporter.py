"""
High-Level SEGYExporter for exporting pyseis internal datasets into SEG-Y files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from pyseis.base import SeismicExporter
from pyseis.core.dataset import SeismicData
from .writer import SEGYWriter

class SEGYExporter(SeismicExporter):
    """
    Writer for exporting pyseis internal .seis datasets to SEG-Y files.
    """

    def __init__(
        self,
        seismic_data: Union[SeismicData, str, Path],
        header_def: Optional[str] = None,
        mapping_path: Optional[str] = None,
        format_code: int = 5, # IEEE Float
        endian: str = ">"
    ):
        if isinstance(seismic_data, (str, Path)):
            self.seismic_data = SeismicData.open(seismic_data)
        else:
            self.seismic_data = seismic_data

        self.format_code = format_code
        self.endian = endian

    def export(self, output_path: Union[str, Path], **kwargs) -> None:
        """Export internal dataset to SEG-Y file."""
        meta = self.seismic_data.metadata
        sample_rate = meta.get("sample_rate", meta.get("sample_rate_us", getattr(self.seismic_data, "sample_rate", 0.004)))
        if isinstance(sample_rate, (int, float)):
            if sample_rate < 1.0: # seconds (e.g. 0.004)
                sample_rate_us = int(sample_rate * 1_000_000)
            else: # micros (e.g. 4000)
                sample_rate_us = int(sample_rate)
        else:
            sample_rate_us = 4000

        traces_2d = self.seismic_data.data[:].compute()
        headers_df = self.seismic_data.headers
        headers_list = headers_df.to_dict(orient="records")

        writer = SEGYWriter(
            target=output_path,
            format_code=self.format_code,
            sample_interval_us=sample_rate_us,
            endian=self.endian
        )
        writer.write(samples=traces_2d, headers=headers_list)
