"""
JavaSeis format definitions using construct library.
Handles binary trace and header data structures.
Metadata (XML, properties) is handled by the main JavaSeis class.
"""

from construct import (
    Struct, Array, Int16ul, Int16ub, Int32ul, Int32ub, Int64ul, Int64ub,
    Float32l, Float32b, Float64l, Float64b,
    Adapter, Container, Padding, this
)
import numpy as np
from math import floor
from collections import OrderedDict

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
        trace = np.zeros(self.nsamples, dtype='float32')
        k1, k2 = 0, 0
        
        for i in range(self.nwindows):
            k1 = k2
            k2 = min(k1 + self.windowln, self.nsamples)
            
            scalar = obj.scalars[i]
            if scalar > 0.0:
                scalar = 1.0 / scalar
            
            window = np.array(obj.samples[k1:k2], dtype='uint16')
            window = window.astype('int32') - 32767
            trace[k1:k2] = scalar * window.astype('float32')
        
        return trace
    
    def _encode(self, obj, context, path):
        """Convert float32 trace data to compressed int16"""
        if not isinstance(obj, np.ndarray):
            obj = np.array(obj, dtype='float32')
            
        scalars = np.zeros(self.nwindows, dtype='float32')
        samples = np.zeros(self.nsamples, dtype='uint16')
        k1, k2 = 0, 0
        
        for i in range(self.nwindows):
            k1 = k2
            k2 = min(k1 + self.windowln, self.nsamples)
            
            window = obj[k1:k2]
            maxval = np.max(np.abs(window))
            scalar = 32766.0 / maxval if maxval > 0 else 0.0
            scalars[i] = scalar
            
            compressed = (scalar * window + 32767)
            samples[k1:k2] = compressed.clip(0, 65535).astype('uint16')
        
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


def parse_file_properties(root):
    """Parse JavaSeis FileProperties.xml
    
    Args:
        root: XML root element from FileProperties.xml
    
    Returns:
        tuple: (file_properties dict, trace_headers list, custom_properties dict)
    """
    file_properties = {}
    trace_headers = []
    custom_properties = {}
    
    # Parse FileProperties section
    file_props = root.find(".//parset[@name='FileProperties']")
    if file_props is not None:
        for par in file_props.findall("par"):
            name = par.get('name')
            value = par.text.strip() if par.text else ""
            file_properties[name] = value
    
    # Parse TraceProperties section
    trace_props = root.find(".//parset[@name='TraceProperties']")
    if trace_props is not None:
        for entry in trace_props.findall("parset"):
            header = {}
            for par in entry.findall("par"):
                name = par.get('name')
                value = par.text.strip() if par.text else ""
                if name == 'label':
                    header['name'] = value
                elif name == 'description':
                    header['description'] = value.strip('"')
                elif name == 'format':
                    header['type'] = value
                elif name == 'byteOffset':
                    header['offset'] = int(value)
            
            if 'name' in header:
                trace_headers.append(header)
    
    # Parse CustomProperties section
    custom_props = root.find(".//parset[@name='CustomProperties']")
    if custom_props is not None:
        # Parse direct parameters
        for par in custom_props.findall("par"):
            name = par.get('name')
            value = par.text.strip() if par.text else ""
            value_type = par.get('type')
            
            # Convert value based on type
            if value_type == 'boolean':
                value = value.lower() == 'true'
            elif value_type == 'int':
                value = int(value)
            elif value_type == 'float':
                value = float(value)
            
            custom_properties[name] = value
            
        # Parse nested parsets (FieldInstruments, Geometry, etc)
        for parset in custom_props.findall("parset"):
            section_name = parset.get('name')
            section_data = {}
            
            for par in parset.findall("par"):
                name = par.get('name')
                value = par.text.strip() if par.text else ""
                value_type = par.get('type')
                
                # Convert value based on type
                if value_type == 'boolean':
                    value = value.lower() == 'true'
                elif value_type == 'int':
                    value = int(value)
                elif value_type == 'float':
                    value = float(value)
                elif value_type == 'double':
                    value = float(value)  # Python float handles double precision
                
                section_data[name] = value
            
            custom_properties[section_name] = section_data
    
    return file_properties, trace_headers, custom_properties

def build_header_struct(trace_headers, byte_order='little'):
    """Build header struct from trace header definitions"""
    # Map JavaSeis types to construct types
    type_map = {
        'INTEGER': Int32ul if byte_order == 'little' else Int32ub,
        'LONG': Int64ul if byte_order == 'little' else Int64ub,
        'FLOAT': Float32l if byte_order == 'little' else Float32b,
        'DOUBLE': Float64l if byte_order == 'little' else Float64b
    }
    
    # Sort headers by offset
    sorted_headers = sorted(trace_headers, key=lambda x: x['offset'])
    subcons = {}
    current_offset = 0
    
    for header in sorted_headers:
        # Add padding if needed
        if header['offset'] > current_offset:
            padding = header['offset'] - current_offset
            subcons[f"_pad_{current_offset}"] = Padding(padding)
        
        # Get field type
        field_type = type_map.get(header['type'])
        if not field_type:
            raise ValueError(f"Unsupported header type: {header['type']}")
            
        # Add field with name
        subcons[header['name']] = field_type
        current_offset = header['offset'] + field_type.sizeof()
    
    return Struct(**subcons)




