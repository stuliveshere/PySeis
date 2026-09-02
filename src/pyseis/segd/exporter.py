"""
High-Level SEGDExporter for exporting pyseis internal datasets into SEG-D files.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from pyseis.base import SeismicExporter
from pyseis.core.dataset import SeismicData
from .writer import SEGDWriter

class SEGDExporter(SeismicExporter):
    """
    Exporter converting internal pyseis .seis datasets into SEG-D files.
    """

    def __init__(
        self,
        seismic_data: Union[SeismicData, str, Path],
        format_code: int = 0x8058,
        gather_type: str = "SG"
    ):
        if isinstance(seismic_data, (str, Path)):
            self.seismic_data = SeismicData.open(seismic_data)
        else:
            self.seismic_data = seismic_data

        self.format_code = format_code
        self.gather_type = gather_type

    def export(self, output_path: Union[str, Path], **kwargs) -> None:
        """Export internal dataset to SEG-D file."""
        meta = self.seismic_data.metadata
        sample_rate_us = int(meta.get("sample_rate_us", meta.get("sample_rate_ms", 2.0) * 1000.0))

        traces_2d = self.seismic_data.data[:].compute()
        headers_df = self.seismic_data.headers

        headers_list = headers_df.to_dict(orient="records")

        writer = SEGDWriter(
            target=output_path,
            format_code=self.format_code,
            sample_interval_us=sample_rate_us,
            gather_type=self.gather_type
        )
        writer.write(samples=traces_2d, headers=headers_list)
