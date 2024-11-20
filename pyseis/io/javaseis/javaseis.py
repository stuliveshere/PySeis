# javaseis.py

import os
import io as _io
import sys
import warnings
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import os.path as osp
from collections import OrderedDict

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)

from pyseis.io.javaseis.js_models import build_header_struct, build_trace_struct
from pyseis.io.javaseis.xml_models import (
    TraceHeaders, TraceFile, FileProperties, 
    TraceProperties, CustomProperties, VirtualFolders
)

class ExtentManager:
    """Manages reading from multiple extent files"""
    def __init__(self, extent_paths, struct, trace_file, trace_size=None):
        self.extent_paths = extent_paths
        self.struct = struct
        self.trace_file = trace_file
        self.trace_size = trace_size
        self._cache = {}  # Cache for open file handles
        
    def __del__(self):
        """Clean up file handles"""
        for handle in self._cache.values():
            handle.close()
            
    def _get_extent_and_offset(self, index):
        """Calculate which extent file and offset contains the requested index"""
        if not self.trace_size:
            self.trace_size = self.struct.sizeof()
            
        # Calculate which extent and position within extent
        traces_per_extent = self.trace_file.VFIO_MAXPOS
        extent_index = index // traces_per_extent
        offset = (index % traces_per_extent) * self.trace_size
        
        return extent_index, offset
        
    def _get_file_handle(self, extent_index):
        """Get or create file handle for extent"""
        if extent_index not in self._cache:
            if extent_index >= len(self.extent_paths):
                raise ValueError(f"Extent index {extent_index} out of range")
            self._cache[extent_index] = open(self.extent_paths[extent_index], 'rb')
        return self._cache[extent_index]
        
    def read_range(self, start_index, count):
        """Read a range of traces/headers from extents
        
        Args:
            start_index: Starting trace/header index
            count: Number of traces/headers to read
            
        Returns:
            List of parsed traces/headers with sorted keys, excluding BytesIO fields
        """
        results = []
        
        for i in range(start_index, start_index + count):
            extent_index, offset = self._get_extent_and_offset(i)
            handle = self._get_file_handle(extent_index)
            
            # Seek to correct position and read
            handle.seek(offset)
            data = handle.read(self.trace_size)
            if data:
                parsed = self.struct.parse(data)
                # Filter out BytesIO objects and sort keys
                if isinstance(parsed, dict):
                    filtered = OrderedDict()
                    for k in sorted(parsed.keys()):
                        if not isinstance(parsed[k], _io.BytesIO):
                            filtered[k] = parsed[k]
                    results.append(filtered)
                else:
                    results.append(parsed)
                
        return results

class JavaSeis:
    """JavaSeis dataset reader/writer."""
    
    def __init__(self, path: Optional[str] = None):
        """Initialize JavaSeis dataset."""
        self.path = Path(path) if path else None
        
        # Initialize all configuration objects
        self.trace_headers: Optional[TraceHeaders] = None
        self.trace_file: Optional[TraceFile] = None
        self.file_properties: Optional[FileProperties] = None
        self.custom_properties: Optional[CustomProperties] = None
        self.trace_properties: Optional[TraceProperties] = None
        self.virtual_folders: Optional[VirtualFolders] = None

        self.header_manager = None
        self.trace_manager = None
        
        if path is not None:
            self.load_existing()
        
    def load_existing(self) -> None:
        """Load existing JavaSeis dataset."""
        self._validate_js_dir()
        self._load_xmls()
        self.header_struct = build_header_struct(self.trace_properties)
        self.trace_struct = build_trace_struct(self.file_properties)
        self.map_extents()
    
    def map_extents(self) -> None:
        """Map trace headers and data extents."""
        self.dimensions = self.file_properties.DataDimensions
        self.axis_lengths = self.file_properties.AxisLengths
        
        # Get paths to extent files
        header_extents = []
        trace_extents = []
        for i in range(self.trace_headers.VFIO_MAXFILE):
            header_extents.append(self.path / f"TraceHeaders{i}")
        for i in range(self.trace_file.VFIO_MAXFILE):
            trace_extents.append(self.path / f"TraceFile{i}")
        
        # Calculate trace sizes
        header_size = self.header_struct.sizeof()
        trace_size = self.trace_struct.sizeof()
            
        # Create extent managers
        self.header_manager = ExtentManager(
            extent_paths=header_extents,
            struct=self.header_struct,
            trace_file=self.trace_headers,
            trace_size=header_size
        )
        
        self.trace_manager = ExtentManager(
            extent_paths=trace_extents,
            struct=self.trace_struct,
            trace_file=self.trace_file,
            trace_size=trace_size
        )
        
    def get_headers(self, start: int, count: int) -> List:
        """Get a range of trace headers
        
        Args:
            start: Starting header index
            count: Number of headers to read
            
        Returns:
            List of parsed headers
        """
        return self.header_manager.read_range(start, count)
        
    def get_traces(self, start: int, count: int) -> List:
        """Get a range of traces
        
        Args:
            start: Starting trace index
            count: Number of traces to read
            
        Returns:
            List of parsed traces
        """
        return self.trace_manager.read_range(start, count)

    def _validate_js_dir(self) -> None:
        """Check that the directory contains required JavaSeis files."""
        required_files = [
            'FileProperties.xml',
            'TraceFile.xml',
            'TraceHeaders.xml',
            'VirtualFolders.xml',
            'Name.properties',
            'Status.properties'
        ]
    
        for fname in required_files:
            if not osp.exists(osp.join(self.path, fname)):
                raise ValueError(f"Missing required file: {fname}")

    def _load_xmls(self) -> None:
        """Load all JavaSeis configurations."""
        try:
            # Load file properties (which contains trace properties)
            self.file_properties = FileProperties()
            self.file_properties.from_xml(self.path / "FileProperties.xml")
            
            # Load custom properties
            self.custom_properties = CustomProperties()
            self.custom_properties.from_xml(self.path / "FileProperties.xml")
            
            # Load trace properties
            self.trace_properties = TraceProperties()
            self.trace_properties.from_xml(self.path / "FileProperties.xml")
            
            # Load extent managers
            self.trace_headers = TraceHeaders()
            self.trace_headers.from_xml(self.path / "TraceHeaders.xml")
            
            self.trace_file = TraceFile()
            self.trace_file.from_xml(self.path / "TraceFile.xml")
            
            # Load virtual folders
            self.virtual_folders = VirtualFolders()
            self.virtual_folders.from_xml(self.path / "VirtualFolders.xml")
            

            
        except Exception as e:
            raise ValueError(f"Error loading configurations: {str(e)}")

    def save_configurations(self) -> None:
        """Save all JavaSeis configurations."""
        if not self.path:
            raise ValueError("No path set for JavaSeis dataset")
            
        # Save file properties
        if self.file_properties:
            self.file_properties.to_xml(self.path / "FileProperties.xml")
            
        # Update custom properties in FileProperties.xml
        if self.custom_properties:
            self.custom_properties.update_xml(self.path / "FileProperties.xml")
            
        # Update trace properties in FileProperties.xml
        if self.trace_properties:
            self.trace_properties.update_xml(self.path / "FileProperties.xml")
            
        # Save extent managers
        if self.trace_headers:
            self.trace_headers.to_xml(self.path / "TraceHeaders.xml")
            
        if self.trace_file:
            self.trace_file.to_xml(self.path / "TraceFile.xml")
            
        # Save virtual folders
        if self.virtual_folders:
            self.virtual_folders.to_xml(self.path / "VirtualFolders.xml")

    def update_trace_header(self, label: str, **kwargs) -> None:
        """Update a trace header entry
        
        Args:
            label: Header entry label to update
            **kwargs: Header attributes to update
        """
        if not self.trace_properties:
            raise ValueError("No trace properties loaded")
            
        entry = self.trace_properties.get_entry(label)
        if not entry:
            raise ValueError(f"No header entry found with label: {label}")
            
        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
                
        self.trace_properties.remap()



# Example usage
if __name__ == "__main__":
    js = JavaSeis("../../../data/javaseis")
    nsamples, ntraces, nframes = js.file_properties.AxisLengths
    headers = js.get_headers(0, ntraces*nframes)
    for header in headers:
        if all(int(value) == 0 for value in header.values()):
            continue
        for key, value in header.items():
            if value != 0:
                print(f"{key}: {value}")
        #wait for user input
        input("Press Enter to continue...")
    