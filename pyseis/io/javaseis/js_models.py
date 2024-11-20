"""
JavaSeis format definitions using construct library.
Handles binary trace and header data structures.
Metadata is handled directly via XML in the main JavaSeis class.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)

from construct import *
import numpy as np
from math import floor
from pyseis.io.javaseis.xml_models import FileProperties, TraceProperties


class CompressedInt16Adapter(Adapter):
    """Adapter for JavaSeis COMPRESSED_INT16 format.
    
    Each trace is divided into windows. For each window:
    - Calculate scale factor based on max absolute value
    - Scale values to fit in int16 range [-32768, 32767]
    - Store scale factor (float32) and scaled values (int16)
    """
    def __init__(self, nsamples, byte_order='little'):
        self.windowln = 100  # Window length for compression
        self.nsamples = nsamples
        self.nwindows = floor((nsamples - 1.0) / self.windowln) + 1
        self.byte_order = '<' if byte_order == 'little' else '>'
        
        # Calculate trace length (padded to even number of samples)
        if nsamples % 2 == 0:
            self.trclen = 4 * self.nwindows + 2 * self.nsamples
        else:
            self.trclen = 4 * self.nwindows + 2 * (self.nsamples + 1)
            
        # Create subcon for the compressed data structure
        subcon = Struct(
            "scalars" / Array(self.nwindows, Float32l if byte_order == 'little' else Float32b),
            "samples" / Array(self.nsamples, Int16ul if byte_order == 'little' else Int16ub)
        )
        super().__init__(subcon)
    
    def _decode(self, obj, context, path):
        """Convert compressed int16 to float32 trace data"""
        trace = np.zeros(self.nsamples, dtype=np.float32)
        k1, k2 = 0, 0
        
        for i in range(self.nwindows):
            k1 = k2
            k2 = min(k1 + self.windowln, self.nsamples)
            
            scalar = float(obj.scalars[i])
            if scalar > 0.0:
                scalar = 1.0 / scalar
            
            # Convert samples to int16 and handle scaling properly
            # First create as uint16 since that's how it's stored
            window = np.array(obj.samples[k1:k2], dtype=np.uint16)
            # Convert to signed by subtracting offset
            window = window.astype(np.int32) - 32767  # Use int32 to avoid overflow
            # Now convert to float32 and apply scaling
            trace[k1:k2] = scalar * window.astype(np.float32)
        
        return trace
    
    def _encode(self, obj, context, path):
        """Convert float32 trace data to compressed int16"""
        if not isinstance(obj, np.ndarray):
            obj = np.array(obj, dtype=np.float32)
            
        scalars = np.zeros(self.nwindows, dtype=np.float32)
        samples = np.zeros(self.nsamples, dtype=np.uint16)
        k1, k2 = 0, 0
        
        for i in range(self.nwindows):
            k1 = k2
            k2 = min(k1 + self.windowln, self.nsamples)
            
            window = obj[k1:k2]
            maxval = np.max(np.abs(window))
            
            if maxval > 0:
                scalar = 32766.0 / maxval
                scalars[i] = scalar
                
                # Scale and shift to unsigned range
                scaled = (scalar * window).astype(np.float32)
                samples[k1:k2] = (scaled + 32767).clip(0, 65535).astype(np.uint16)
            else:
                scalars[i] = 0.0
                samples[k1:k2] = 32767
        
        return Container(
            scalars=scalars,
            samples=samples
        )

def build_trace_struct(file_properties: FileProperties) -> Struct:
    """Build trace struct for COMPRESSED_INT16 format
    
    Args:
        file_properties: FileProperties instance containing trace format info
        
    Returns:
        Struct: Construct struct for parsing traces
    """
    # Get number of samples from axis lengths
    nsamples = file_properties.AxisLengths[0]  # TIME axis is first
    byte_order = 'little' if file_properties.ByteOrder == 'LITTLE_ENDIAN' else 'big'
    
    return CompressedInt16Adapter(nsamples, byte_order)

def build_header_struct(trace_properties: TraceProperties) -> Struct:
    """Build header struct from trace header definitions
    
    Args:
        trace_properties: TraceProperties instance containing header definitions
        
    Returns:
        Struct: Construct struct for parsing headers
    """
    subcons = {}
    
    # Map JavaSeis types to Construct types
    type_map = {
        'INTEGER': Int32ul,
        'FLOAT': Float32l,
        'DOUBLE': Float64l,
        'LONG': Int64ul,
        'SHORT': Int16ul,
        'BYTE': Int8ul
    }
    # Process each header entry
    for entry in trace_properties.entries:
        # Get field type and add to struct
        field_type = type_map.get(entry.format)
        if field_type:
            subcons[entry.label] = field_type
    
    return Struct(**subcons)



