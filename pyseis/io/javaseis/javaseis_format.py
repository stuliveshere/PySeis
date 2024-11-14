"""
JavaSeis format definitions using construct library.
Handles binary trace and header data structures.
Metadata is handled directly via XML in the main JavaSeis class.
"""

from construct import (
    Struct, Array, Int16ul, Int16ub, Int32ul, Int32ub, Int64ul, Int64ub,
    Float32l, Float32b, Float64l, Float64b,
    Adapter, Container, Padding, this
)
import numpy as np
from math import floor

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

def build_trace_struct(nsamples, byte_order='little'):
    """Build trace struct for COMPRESSED_INT16 format
    
    Args:
        nsamples: Number of samples per trace
        byte_order: Byte order ('little' or 'big')
    
    Returns:
        Struct: Construct struct for parsing traces
    """
    return CompressedInt16Adapter(nsamples, byte_order)

def build_header_struct(trace_headers, byte_order='little', header_length=360):
    """Build header struct from trace header definitions
    
    Args:
        trace_headers: List of header definitions from XML
        byte_order: Byte order ('little' or 'big')
        header_length: Total header length in bytes from FileProperties.xml
    
    Returns:
        Struct: Construct struct for parsing headers
    """
    # Map JavaSeis types to construct types
    type_map = {
        'INTEGER': Int32ul if byte_order == 'little' else Int32ub,
        'LONG': Int64ul if byte_order == 'little' else Int64ub,
        'FLOAT': Float32l if byte_order == 'little' else Float32b,
        'DOUBLE': Float64l if byte_order == 'little' else Float64b
    }
    
    # Sort headers by offset
    sorted_headers = sorted(trace_headers, key=lambda x: x.get('offset', 0))
    subcons = {}
    current_offset = 0
    
    for header in sorted_headers:
        # Add padding if needed
        header_offset = header.get('offset', current_offset)
        if header_offset > current_offset:
            padding = header_offset - current_offset
            subcons[f"_pad_{current_offset}"] = Padding(padding)
        
        # Get field type
        field_type = type_map.get(header.get('format', 'INTEGER'))
        if not field_type:
            raise ValueError(f"Unsupported header type: {header.get('format')}")
            
        # Add field with name
        name = header['name']
        subcons[name] = field_type
        current_offset = header_offset + field_type.sizeof()
    
    # Add final padding if needed to match header length
    if current_offset < header_length:
        subcons[f"_pad_{current_offset}"] = Padding(header_length - current_offset)
    
    return Struct(**subcons)




