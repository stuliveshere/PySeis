import os
from typing import Dict, List, Any
import numpy as np
from io import BytesIO

from .base import SegD21Format

class SegD:
    """Main SEG-D reader/writer class that uses format-specific implementations."""
    
    def __init__(self, filename: str, manufacturer: str = 'segd21'):
        """Initialize SEG-D reader.
        
        Args:
            filename: Path to SEG-D file to read
            manufacturer: SEG-D format type ('segd21', 'smartsolo10', etc.)
        """
        self.filename = filename
        
        # Use SegD21Format to parse the SEG-D file
        self.data = SegD21Format(filename)
    
    @property
    def num_traces(self) -> int:
        """Get number of traces in file"""
        return len(self.traces)

    @property
    def samples_per_trace(self) -> int:
        """Get number of samples per trace"""
        if self.traces:
            return len(self.traces[0].trace_data)
        return 0

    def get_trace_data(self, index: int) -> np.ndarray:
        """Get trace data samples by index"""
        if 0 <= index < self.num_traces:
            return self.traces[index].trace_data
        raise IndexError(f"Trace index {index} out of range")

    def get_trace_header(self, index: int) -> Dict:
        """Get trace header by index"""
        if 0 <= index < self.num_traces:
            return self.traces[index].demux_header
        raise IndexError(f"Trace index {index} out of range")

    def get_trace_extensions(self, index: int) -> List:
        """Get trace header extensions by index"""
        if 0 <= index < self.num_traces:
            return self.traces[index].trace_header_extensions
        raise IndexError(f"Trace index {index} out of range")



