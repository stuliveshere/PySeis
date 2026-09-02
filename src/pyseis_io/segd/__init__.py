"""
SEG-D reader, writer, schema engine, validator, and importer/exporter package.
"""

from .importer import SEGDImporter
from .exporter import SEGDExporter
from .reader import SEGDReader
from .writer import SEGDWriter
from .scanner import CorpusScanner
from .schema import SchemaManager
from .fill_plan import TraceFillPlan

# Alias SegD for backward compatibility
SegD = SEGDReader

__all__ = [
    "SEGDImporter",
    "SEGDExporter",
    "SEGDReader",
    "SEGDWriter",
    "CorpusScanner",
    "SchemaManager",
    "TraceFillPlan",
    "SegD"
]
