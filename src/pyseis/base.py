from abc import ABC, abstractmethod
from typing import Union, Optional, TYPE_CHECKING
from pathlib import Path
import pandas as pd

if TYPE_CHECKING:
    from pyseis.core.dataset import SeismicData

class SeismicImporter(ABC):
    """
    Abstract base class for importing external seismic formats to pyseis internal format.
    """
    
    @abstractmethod
    def __init__(self, path: Union[str, Path], **kwargs):
        """
        Initialize the importer.
        
        Args:
            path: Path to the external file.
        """
        pass
    
    @abstractmethod
    def scan(self) -> pd.DataFrame:
        """
        Quickly scan headers without full import.
        
        Returns:
            pd.DataFrame: A DataFrame containing the headers.
        """
        pass
        
    @abstractmethod
    def import_data(self, output_path: Union[str, Path], chunk_size: int = 1000, **kwargs) -> 'SeismicData':
        """
        Convert external format to internal .seis format.
        
        Args:
            output_path: Destination path for the internal dataset.
            chunk_size: Number of traces to process at a time.
            
        Returns:
            SeismicData: The opened internal dataset.
        """
        pass

class SeismicExporter(ABC):
    """
    Abstract base class for exporting pyseis internal format to external formats.
    """
    
    @abstractmethod
    def __init__(self, seismic_data: Union['SeismicData', str, Path], **kwargs):
        """
        Initialize the exporter.
        
        Args:
            seismic_data: SeismicData object or path to .seis dataset.
        """
        pass
    
    @abstractmethod
    def export(self, output_path: Union[str, Path], **kwargs) -> None:
        """
        Export internal data to external format.
        
        Args:
            output_path: Destination path for the external file.
        """
        pass
