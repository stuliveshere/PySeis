from typing import Union, List, Optional
import pandas as pd
from pyseis_io.core.dataset import SeismicData

def export_headers_to_gis(
    data: Union[SeismicData, pd.DataFrame],
    filename: str,
    format: str = 'gpkg',
    crs: str = "EPSG:4326",
    geometry_cols: List[str] = ["source_x", "source_y"]
) -> None:
    """
    Export seismic headers to a GIS format (e.g., GeoPackage).

    Args:
        data: SeismicData object or pandas DataFrame containing headers.
        filename: Output filename.
        format: GIS format driver (default 'gpkg' for GeoPackage).
        crs: Coordinate Reference System (default "EPSG:4326").
        geometry_cols: List of column names to use for geometry [x, y].
    
    Raises:
        ImportError: If geopandas is not installed.
        ValueError: If geometry columns are missing.
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        raise ImportError("geopandas is required for GIS export. Please install it with 'pip install geopandas'.")

    # Extract headers if SeismicData
    if isinstance(data, SeismicData):
        df = data.headers
    elif isinstance(data, pd.DataFrame):
        df = data
    else:
        raise TypeError("data must be SeismicData or pandas DataFrame")

    # Check geometry columns
    if len(geometry_cols) != 2:
        raise ValueError("geometry_cols must contain exactly two column names [x, y]")
    
    x_col, y_col = geometry_cols
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Geometry columns {geometry_cols} not found in headers")

    # Create geometry
    geometry = [Point(xy) for xy in zip(df[x_col], df[y_col])]
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)
    
    # Export
    gdf.to_file(filename, driver="GPKG" if format == 'gpkg' else format)
