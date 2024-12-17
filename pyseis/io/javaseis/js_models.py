"""
JavaSeis format definitions using construct library.
Handles binary trace and header data structures.
"""

from construct import *
import numpy as np
from math import floor
import logging
from .xml_io import JavaSeisXML

logger = logging.getLogger(__name__)

class CompressedInt16Adapter(Adapter):
    """Adapter for JavaSeis COMPRESSED_INT16 format."""
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
            
            window = np.array(obj.samples[k1:k2], dtype=np.uint16)
            window = window.astype(np.int32) - 32767
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
                scaled = (scalar * window).astype(np.float32)
                samples[k1:k2] = (scaled + 32767).clip(0, 65535).astype(np.uint16)
            else:
                scalars[i] = 0.0
                samples[k1:k2] = 32767
        
        return Container(
            scalars=scalars,
            samples=samples
        )

def build_trace_struct(file_props_tree) -> Struct:
    """Build trace struct for COMPRESSED_INT16 format"""
    from pyseis.io.javaseis.xml_io import JavaSeisXML
    
    logger.debug("Getting AxisLengths from FileProperties")
    axis_lengths_str = JavaSeisXML.get(file_props_tree, "AxisLengths")
    logger.debug(f"Raw AxisLengths: {axis_lengths_str}")
    
    if axis_lengths_str is None:
        logger.error("AxisLengths not found in FileProperties XML")
        raise ValueError("AxisLengths not found in FileProperties XML")
        
    axis_lengths = [int(x) for x in axis_lengths_str.split()]
    logger.debug(f"Parsed AxisLengths: {axis_lengths}")
    
    nsamples = axis_lengths[0]  # TIME axis is first
    logger.debug(f"Number of samples: {nsamples}")
    
    byte_order = JavaSeisXML.get(file_props_tree, "ByteOrder")
    logger.debug(f"ByteOrder: {byte_order}")
    byte_order = 'little' if byte_order == 'LITTLE_ENDIAN' else 'big'
    
    return CompressedInt16Adapter(nsamples, byte_order)

# Map JavaSeis types to construct types
TYPE_MAP = {
    'INTEGER': lambda name: Int32ul(name),
    'FLOAT': lambda name: Float32l(name),
    'DOUBLE': lambda name: Float64l(name),
    'LONG': lambda name: Int64ul(name)
}

def build_header_struct(file_properties_tree):
    """Build header struct from TraceProperties in FileProperties.xml"""
    logger.debug("Building header struct from TraceProperties")
    
    # Get TraceProperties section
    trace_props = file_properties_tree.find(".//parset[@name='TraceProperties']")
    if trace_props is None:
        raise ValueError("No TraceProperties section found in FileProperties.xml")
        
    # Create struct fields with default values
    struct_def = {}
    default_values = {}  # Store default values for each field
    
    for entry in trace_props.findall("parset"):
        label = JavaSeisXML.get(entry, "label")
        fmt = JavaSeisXML.get(entry, "format")
        count = int(JavaSeisXML.get(entry, "elementCount"))
        offset = int(JavaSeisXML.get(entry, "byteOffset"))
        
        logger.debug(f"Adding header field: {label} ({fmt}) at offset {offset}")
        
        # Map format to construct type and set default value
        if fmt == "INTEGER":
            field = Int32ul
            default = 0
        elif fmt == "FLOAT":
            field = Float32l
            default = 0.0
        elif fmt == "DOUBLE":
            field = Float64l
            default = 0.0
        elif fmt == "LONG":
            field = Int64ul
            default = 0
        else:
            raise ValueError(f"Unknown format: {fmt}")
            
        if count > 1:
            struct_def[label] = Array(count, field)
            default_values[label] = [default] * count
        else:
            struct_def[label] = Default(field, default)
            default_values[label] = default
    
    return Struct(**struct_def)



