"""
PySeis: High-performance seismic data processing, I/O, and storage library.
"""

from .core.dataset import SeismicData
from .core.reader import InternalFormatReader
from .core.writer import InternalFormatWriter
from .segy.importer import SEGYImporter
from .segy.exporter import SEGYExporter
from .su.importer import SUImporter
from .su.exporter import SUExporter
from .segd.importer import SEGDImporter
from .segd.exporter import SEGDExporter

open = SeismicData.open
from_buffer = SeismicData.from_buffer

__all__ = [
    "SeismicData",
    "InternalFormatReader",
    "InternalFormatWriter",
    "SEGYImporter",
    "SEGYExporter",
    "SUImporter",
    "SUExporter",
    "SEGDImporter",
    "SEGDExporter",
    "open",
    "from_buffer",
]
