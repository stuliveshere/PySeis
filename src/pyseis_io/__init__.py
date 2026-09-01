"""
pyseis-io: Single-Parquet seismic I/O library.
"""

from .core.dataset import SeismicData
from .core.reader import InternalFormatReader
from .core.writer import InternalFormatWriter
from .segy.importer import SEGYImporter
from .su.importer import SUImporter

open = SeismicData.open
from_buffer = SeismicData.from_buffer

__all__ = [
    "SeismicData",
    "InternalFormatReader",
    "InternalFormatWriter",
    "SEGYImporter",
    "SUImporter",
    "open",
    "from_buffer",
]
