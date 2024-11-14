# javaseis.py

import os
import sys
# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import os.path as osp
import struct
import warnings
import math
import numpy as np
from lxml import etree
from construct import StreamError
from pyseis.io.javaseis_format import *
from pathlib import Path

class JavaSeis:
    """JavaSeis dataset reader/writer.
    
    Handles both binary data (traces, headers) and metadata (XML, properties).
    Binary data is stored in extent files, metadata in XML and properties files.
    """
    def __init__(self, path):
        self.path = path
        self._validate_js_dir()

        # Initialize properties
        self.file_properties = {}
        self.trace_headers = []
        self.custom_properties = {}
        self._read_file_properties()

        # Initialize extent lists
        self.trace_extents = []
        self.header_extents = []
        self.check_extents()
        
        # Build binary structs
        byte_order = 'little' if self.byte_order == 'LITTLE_ENDIAN' else 'big'
        self.header_struct = build_header_struct(self.trace_headers, byte_order)
        self.trace_struct = build_trace_struct(self.nsamples, byte_order)

    def _validate_js_dir(self):
        required_files = [
            "FileProperties.xml",
            "TraceFile.xml",
            "TraceHeaders.xml",
            "Name.properties",
            "Status.properties"
        ]

        for fname in required_files:
            fpath = osp.join(self.path, fname)
            if not osp.isfile(fpath):
                raise FileNotFoundError(f"Required file '{fname}' not found in JavaSeis dataset.")

    def _read_file_properties(self):
        """Read and parse FileProperties.xml"""
        file_properties_path = osp.join(self.path, "FileProperties.xml")
        tree = etree.parse(file_properties_path)
        root = tree.getroot()
        
        # Parse all sections
        self.file_properties, self.trace_headers, self.custom_properties = parse_file_properties(root)
        
        # Set key properties
        self.trace_format = self.file_properties.get('TraceFormat')
        self.byte_order = self.file_properties.get('ByteOrder', 'LITTLE_ENDIAN')
        
        # Parse axis lengths
        axis_lengths = self.file_properties.get('AxisLengths', '').split()
        if not axis_lengths:
            raise ValueError("No axis lengths found")
        self.nsamples = int(axis_lengths[0])
        self.axis_lengths = [int(x) for x in axis_lengths]
        
        # Get header length
        self.header_length = int(self.file_properties.get('HeaderLengthBytes', 0))
        
        # Set mapped flag
        mapped_str = self.file_properties.get('Mapped', 'false').lower()
        self.is_mapped = mapped_str == 'true'

    def check_extents(self):
        """Check that the extents are valid and build extent lists."""
        # Parse TraceFile.xml and TraceHeaders.xml
        trace_file_path = osp.join(self.path, "TraceFile.xml")
        headers_file_path = osp.join(self.path, "TraceHeaders.xml")
        
        trace_root = etree.parse(trace_file_path).getroot()
        headers_root = etree.parse(headers_file_path).getroot()
        
        # Get extent names
        trace_name = trace_root.find(".//par[@name='VFIO_EXTNAME']").text.strip()
        header_name = headers_root.find(".//par[@name='VFIO_EXTNAME']").text.strip()
        
        # Parse VirtualFolders.xml for filesystem info
        vf_path = osp.join(self.path, "VirtualFolders.xml")
        if osp.exists(vf_path):
            vf_tree = etree.parse(vf_path)
            vf_root = vf_tree.getroot()
            n_dirs = int(vf_root.find(".//par[@name='NDIR']").text)
            
            # Get filesystem paths
            self.fs_paths = []
            for i in range(n_dirs):
                fs_info = vf_root.find(f".//par[@name='FILESYSTEM-{i}']").text
                path, mode = [x.strip() for x in fs_info.split(',')]
                if path == '.':
                    path = self.path
                self.fs_paths.append((path, mode))
        else:
            warnings.warn("VirtualFolders.xml not found, using dataset path only")
            self.fs_paths = [(self.path, 'READ_WRITE')]
        
        # Check for extent files
        extent_num = 0
        while True:
            trace_found = False
            header_found = False
            
            for fs_path, _ in self.fs_paths:
                trace_ext = osp.join(fs_path, f"{trace_name}{extent_num}")
                header_ext = osp.join(fs_path, f"{header_name}{extent_num}")
                
                if osp.exists(trace_ext):
                    trace_found = True
                    self.trace_extents.append(trace_ext)
                
                if osp.exists(header_ext):
                    header_found = True
                    self.header_extents.append(header_ext)
            
            # Stop if no more extents found
            if not (trace_found or header_found):
                break
                
            extent_num += 1
        
        # Check if any extents were found
        if not self.trace_extents:
            warnings.warn("No trace extents found")
        if not self.header_extents:
            warnings.warn("No header extents found")

    def read_trace_header(self, extent_index, trace_index):
        """Read a single trace header
        
        Args:
            extent_index: Index of extent file
            trace_index: Index of trace within extent
            
        Returns:
            dict: Header values
        """
        extent = self.header_extents[extent_index]
        with open(extent, 'rb') as f:
            offset = trace_index * self.header_length
            f.seek(offset)
            return self.header_struct.parse_stream(f)

    def write_trace_header(self, extent_index, trace_index, header_data):
        """Write a single trace header
        
        Args:
            extent_index: Index of extent file
            trace_index: Index of trace within extent
            header_data: Header values to write
        """
        extent = self.header_extents[extent_index]
        with open(extent, 'rb+') as f:
            offset = trace_index * self.header_length
            f.seek(offset)
            self.header_struct.build_stream(header_data, f)

    def read_trace(self, extent_index, trace_index):
        """Read a single trace
        
        Args:
            extent_index: Index of extent file
            trace_index: Index of trace within extent
            
        Returns:
            numpy.ndarray: Trace samples
        """
        extent = self.trace_extents[extent_index]
        with open(extent, 'rb') as f:
            offset = trace_index * self.trace_struct.trclen
            f.seek(offset)
            return self.trace_struct.parse_stream(f)

    def write_trace(self, extent_index, trace_index, trace_data):
        """Write a single trace
        
        Args:
            extent_index: Index of extent file
            trace_index: Index of trace within extent
            trace_data: Trace samples to write
        """
        extent = self.trace_extents[extent_index]
        with open(extent, 'rb+') as f:
            offset = trace_index * self.trace_struct.trclen
            f.seek(offset)
            self.trace_struct.build_stream(trace_data, f)

    def read_trace_and_header(self, extent_index, trace_index):
        """Read both trace and header
        
        Args:
            extent_index: Index of extent file
            trace_index: Index of trace within extent
            
        Returns:
            tuple: (trace samples, header values)
        """
        return (
            self.read_trace(extent_index, trace_index),
            self.read_trace_header(extent_index, trace_index)
        )

    def read_frame(self, frame_index):
        """Read a complete frame of traces and headers
        
        For 2D data:
            - Single frame containing all traces
            - frame_index must be 0
            
        For 3D data:
            - Frame is a single inline containing all crosslines
            - frame_index corresponds to inline number
            
        Args:
            frame_index: Index of frame to read
                - 2D: must be 0
                - 3D: inline number
            
        Returns:
            tuple: (traces array, headers list)
            - traces: numpy array of shape (ntraces, nsamples)
            - headers: list of header dictionaries for the frame
        """
        if not self.trace_extents or not self.header_extents:
            raise ValueError("No extent files found")
        
        # Get data dimensions
        ndims = int(self.file_properties.get('DataDimensions', 0))
        if ndims not in [2, 3]:
            raise ValueError(f"Unsupported data dimensions: {ndims}")
        
        # Handle 2D data
        if ndims == 2:
            if frame_index != 0:
                raise ValueError("2D data only has one frame (index must be 0)")
            ntraces = self.axis_lengths[1]  # All traces
            frame_size = ntraces
            frame_start = 0
            
        # Handle 3D data
        else:  # ndims == 3
            nxlines = self.axis_lengths[1]   # Crosslines per inline
            ninlines = self.axis_lengths[2]  # Total inlines
            if frame_index >= ninlines:
                raise ValueError(f"Frame (inline) index {frame_index} exceeds dataset size ({ninlines} inlines)")
            frame_size = nxlines
            frame_start = frame_index * nxlines
        
        traces = []
        headers = []
        
        # Calculate traces per extent
        traces_per_extent = os.path.getsize(self.trace_extents[0]) // self.trace_struct.trclen
        
        # Read all traces in the frame
        for i in range(frame_size):
            global_trace = frame_start + i
            extent_index = global_trace // traces_per_extent
            trace_index = global_trace % traces_per_extent
            
            if extent_index >= len(self.trace_extents):
                break
            
            trace = self.read_trace(extent_index, trace_index)
            header = self.read_trace_header(extent_index, trace_index)
            traces.append(trace)
            headers.append(header)
        
        if not traces:
            raise ValueError(f"No traces read for frame {frame_index}")
        
        # Convert traces list to numpy array
        traces = np.array(traces)
        
        return traces, headers

    def read_live_frame(self, frame_index):
        """Read a frame and return only live traces (TRC_TYPE != 0)
        
        Args:
            frame_index: Index of frame to read
            
        Returns:
            tuple: (traces array, headers list)
            - traces: numpy array of shape (n_live_traces, nsamples)
            - headers: list of header dictionaries for live traces
        """
        # Read full frame
        traces, headers = self.read_frame(frame_index)
        
        # Create mask for live traces
        live_mask = np.array([header['TRC_TYPE'] != 0 for header in headers])
        
        # Filter traces and headers
        live_traces = traces[live_mask]
        live_headers = [h for h, m in zip(headers, live_mask) if m]
        
        return live_traces, live_headers

# Example usage
if __name__ == "__main__":
    js_path = "/misc/softwareStor/sfletcher/git/PySeis/data/javaseis"
    js = JavaSeis(js_path) 

    print("Available extents:")
    print(f"Trace extents: {js.trace_extents}")
    print(f"Header extents: {js.header_extents}")

    # Read first frame (live traces only)
    traces, headers = js.read_live_frame(1)
    
    print("\nFrame summary:")
    print(f"Total traces in dataset: {js.axis_lengths[1] * js.axis_lengths[2]}")
    print(f"Live traces: {len(traces)}")
    print(f"Trace shape: {traces.shape}")
    
    # Sort and print first header
    if headers:
        print("\nFirst header (sorted):")
        for key in sorted(headers[0].keys()):
            print(f"{key}: {headers[0][key]}")
    
    print(f"\nFirst trace min/max:")
    print(f"Min: {traces[0].min():.3f}")
    print(f"Max: {traces[0].max():.3f}")
