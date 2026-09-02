"""GeoPackage (.gpkg) format support for seismic data export."""

from .writer import export_headers_to_gis

__all__ = ["export_headers_to_gis"]
