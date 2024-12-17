# javaseis.py

import os
import io as _io
import sys
import warnings
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import os.path as osp
from collections import OrderedDict
import numpy as np
import shutil
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
from math import floor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)

from pyseis.io.javaseis.xml_io import JavaSeisXML
from pyseis.io.javaseis.templates import *  # Import all templates
from pyseis.io.javaseis.templates import FilePropertiesTemplate, VirtualFoldersTemplate, TraceHeadersTemplate, TraceFileTemplate
from pyseis.io.javaseis.js_models import build_header_struct, build_trace_struct
class ExtentManager:
    """Manages reading from multiple extent files"""
    def __init__(self, extent_paths, struct, trace_file_tree, trace_size=None):
        self.extent_paths = extent_paths
        self.struct = struct
        self.trace_file_tree = trace_file_tree  # Single ElementTree for TraceFile
        self.trace_size = trace_size
        self._cache = {}
            
    def __del__(self):
        """Clean up file handles"""
        for handle in self._cache.values():
            handle.close()
            
    def _get_extent_and_offset(self, index):
        """Calculate which extent file and offset contains the requested index"""
        if not self.trace_size:
            self.trace_size = self.struct.sizeof()
            
        # Get VFIO_MAXPOS with safety checks
        traces_per_extent = JavaSeisXML.get(self.trace_file_tree, "VFIO_MAXPOS", "0")
        traces_per_extent = int(traces_per_extent)
        
        if traces_per_extent <= 0:
            raise ValueError("Invalid VFIO_MAXPOS value: must be greater than 0")
            
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
        """Read a range of traces/headers from extents"""
        results = []
        
        for i in range(start_index, start_index + count):
            extent_index, offset = self._get_extent_and_offset(i)
            handle = self._get_file_handle(extent_index)
            handle.seek(offset)
            data = handle.read(self.trace_size)
            
            if data:
                parsed = self.struct.parse(data)
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
    
    def __init__(self):
        """Initialize JavaSeis dataset."""
        self.xml = None
        self.header_manager = None
        self.trace_manager = None

    def load(self, path: str) -> None:
        """Load existing JavaSeis dataset."""
        self.path = Path(path)
        logger.info(f"Loading JavaSeis dataset from: {self.path}")
        self._validate_js_dir()
        
        # Load XML files
        self.xml = {}
        for key in js_xml.keys():
            xml_path = self.path / f"{key}.xml"
            logger.debug(f"Loading XML file: {xml_path}")
            self.xml[key] = JavaSeisXML.load(xml_path)
        
        # Build header and trace structs
        logger.debug("Building header struct from FileProperties.xml")
        self.header_struct = build_header_struct(self.xml["FileProperties"])
        
        logger.debug("Building trace struct from FileProperties.xml")
        self.trace_struct = build_trace_struct(self.xml["FileProperties"])
        
        # Map extents
        logger.debug("Mapping extents")
        self.map_extents()

    def create_new(self, samples: int = 1000, traces: int = 1000, frames: int = 100, volumes: int = None) -> None:
        """Create a new JavaSeis dataset."""
        # Initialize XML structures from templates
        self.xml = {}
        template_map = {
            'FileProperties': FilePropertiesTemplate,
            'VirtualFolders': VirtualFoldersTemplate,
            'TraceHeaders': TraceHeadersTemplate,
            'TraceFile': TraceFileTemplate
        }
        
        for key, template in template_map.items():
            self.xml[key] = JavaSeisXML.create(template)

        # Set basic properties using JavaSeisXML helper
        fp_tree = self.xml["FileProperties"]
        
        # Set dimensions
        JavaSeisXML.set(fp_tree, "DataDimensions", "3")
        
        # Set axis properties using multi-line formatting
        JavaSeisXML.set(fp_tree, "AxisLabels", ["TIME", "CROSSLINE", "INLINE"], "string")
        JavaSeisXML.set(fp_tree, "AxisUnits", ["milliseconds", "meters", "meters"], "string")
        JavaSeisXML.set(fp_tree, "AxisDomains", ["time", "space", "space"], "string")
        JavaSeisXML.set(fp_tree, "AxisLengths", [samples, traces, frames], "long")
        JavaSeisXML.set(fp_tree, "LogicalOrigins", [0, 1, 1], "long")
        JavaSeisXML.set(fp_tree, "LogicalDeltas", [1, 1, 1], "long")
        JavaSeisXML.set(fp_tree, "PhysicalOrigins", [0.0, 0.0, 0.0], "double")
        JavaSeisXML.set(fp_tree, "PhysicalDeltas", [1.0, 1.0, 1.0], "double")
        
        # Set other properties
        JavaSeisXML.set(fp_tree, "DataType", "UNSTACKED")
        JavaSeisXML.set(fp_tree, "TraceFormat", "COMPRESSED_INT16")
        JavaSeisXML.set(fp_tree, "ByteOrder", "LITTLE_ENDIAN")
        
        # Calculate total number of traces
        volumes = volumes or 1
        total_traces = volumes * frames * traces
        
        # Update TraceFile and TraceHeaders XML
        for xml_name in ['TraceFile', 'TraceHeaders']:
            tree = self.xml[xml_name]
            JavaSeisXML.set(tree, "VFIO_MAXFILE", "1")  # Single extent file
            
            # Calculate and set extent size
            if xml_name == 'TraceFile':
                # Calculate compression overhead
                samples_padded = samples + (samples % 2)  # Pad to even number
                windows = (samples - 1) // 100 + 1  # 100 samples per window
                
                # Size per trace:
                # - 4 bytes per window scalar
                # - 2 bytes per sample (padded to even)
                bytes_per_trace = (4 * windows) + (2 * samples_padded)
                
                # Total size for all traces
                extent_size = bytes_per_trace * traces * frames * volumes
            else:
                # For headers: header length * total traces
                header_length = int(JavaSeisXML.get(fp_tree, "HeaderLengthBytes", "0"))
                extent_size = header_length * traces
                
            JavaSeisXML.set(tree, "VFIO_EXTSIZE", str(extent_size))
            JavaSeisXML.set(tree, "VFIO_MAXPOS", str(extent_size))  # Total traces
        
        # Build header and trace structs
        self.header_struct = build_header_struct(self.xml["FileProperties"])
        self.trace_struct = build_trace_struct(self.xml["FileProperties"])

    def map_extents(self) -> None:
        """Map trace headers and data extents."""
        # Get dimensions and axis lengths from FileProperties
        fp_tree = self.xml["FileProperties"]
        logger.debug("Reading dimensions from FileProperties")
        self.dimensions = int(JavaSeisXML.get(fp_tree, "DataDimensions"))
        logger.debug(f"Dimensions: {self.dimensions}")
        
        axis_lengths = JavaSeisXML.get(fp_tree, "AxisLengths")
        logger.debug(f"Raw AxisLengths: {axis_lengths}")
        self.axis_lengths = [int(x) for x in axis_lengths.split()]
        logger.debug(f"Parsed AxisLengths: {self.axis_lengths}")
        
        # Get paths to extent files
        header_extents = []
        trace_extents = []
        max_files = int(JavaSeisXML.get(self.xml["TraceHeaders"], "VFIO_MAXFILE"))
        for i in range(max_files):
            header_extents.append(self.path / f"TraceHeaders{i}")
            trace_extents.append(self.path / f"TraceFile{i}")
            
        # Create extent managers with specific XML trees
        self.header_manager = ExtentManager(
            extent_paths=header_extents,
            struct=self.header_struct,
            trace_file_tree=self.xml["TraceHeaders"]  # Pass specific tree
        )
        
        self.trace_manager = ExtentManager(
            extent_paths=trace_extents,
            struct=self.trace_struct,
            trace_file_tree=self.xml["TraceFile"]  # Pass specific tree
        )

    def _validate_js_dir(self) -> None:
        """Check that the directory contains required JavaSeis files."""
        required_files = [a+".xml" for a in js_xml.keys()]
        print(required_files)
   
        for fname in required_files:
            if not osp.exists(osp.join(self.path, fname)):
                raise ValueError(f"Missing required file: {fname}")

    def get_headers(self, start: int, count: int) -> List:
        """Get a range of trace headers"""
        return self.header_manager.read_range(start, count)
        
    def get_traces(self, start: int, count: int) -> List:
        """Get a range of traces"""
        return self.trace_manager.read_range(start, count)

    def add_header(self, label: str, description: str, format: str, 
                  element_count: int = 1, byte_offset: int = None) -> None:
        """Add a new header to FileProperties.xml and TraceHeaders.xml
        
        Args:
            label: Header label (e.g., 'FFID')
            description: Header description
            format: Data format ('INTEGER', 'FLOAT', 'DOUBLE', 'LONG')
            element_count: Number of elements (default 1)
            byte_offset: Byte offset in trace header (calculated if None)
        """
        if self.xml is None or 'FileProperties' not in self.xml:
            raise ValueError("FileProperties not initialized. Call create_new() first")
            
        # Update FileProperties.xml
        fp_tree = self.xml['FileProperties']
        trace_props = fp_tree.find(".//parset[@name='TraceProperties']")
        
        if trace_props is None:
            raise ValueError("No TraceProperties section found in FileProperties")
            
        # Calculate byte offset and entry number
        props = trace_props.findall("parset")
        if props:
            # Find max entry number
            entry_num = max(int(p.get("name").split("_")[1]) for p in props if p.get("name").startswith("entry_")) + 1
            # Find max offset + size of last property
            last_offset = max(int(JavaSeisXML.get(p, "byteOffset", "0")) for p in props)
            last_prop = max(props, key=lambda p: int(JavaSeisXML.get(p, "byteOffset", "0")))
            last_size = 4  # Default size
            if JavaSeisXML.get(last_prop, "format") == "DOUBLE":
                last_size = 8
            byte_offset = last_offset + last_size
        else:
            entry_num = 1
            byte_offset = 0
                
        # Create new property as parset under TraceProperties
        new_prop = ET.SubElement(trace_props, "parset")
        new_prop.set("name", f"entry_{entry_num}")
        
        # Add parameters as par elements
        for name, value in [
            ("label", label),
            ("description", description),
            ("format", format),
            ("elementCount", str(element_count)),
            ("byteOffset", str(byte_offset))
        ]:
            par = ET.SubElement(new_prop, "par")
            par.set("name", name)
            par.set("type", "string" if name in ["label", "description", "format"] else "int")
            par.text = value
        
        # Update HeaderLengthBytes in FileProperties
        format_sizes = {"INTEGER": 4, "FLOAT": 4, "DOUBLE": 8, "LONG": 8}
        header_length = byte_offset + format_sizes[format] * element_count
        JavaSeisXML.set(fp_tree, "HeaderLengthBytes", str(header_length))
        
        # Update TraceHeaders.xml
        th_tree = self.xml["TraceHeaders"]
        # Update VFIO_EXTSIZE to match total header size * number of traces
        axis_lengths = [int(x) for x in JavaSeisXML.get(fp_tree, "AxisLengths").split()]
        total_traces = axis_lengths[1] * axis_lengths[2]  # traces * frames
        total_header_size = header_length * total_traces
        JavaSeisXML.set(th_tree, "VFIO_EXTSIZE", str(total_header_size))
        JavaSeisXML.set(th_tree, "VFIO_MAXPOS", str(total_header_size))
        
        # Rebuild header struct after adding new header
        self.header_struct = build_header_struct(self.xml["FileProperties"])

    def save(self, path: str = None) -> None:
        """Save/overwrite JavaSeis XML files.
        
        Args:
            path: Optional path to save to. If None, uses self.path
        """
        if path is not None:
            self.path = Path(path)
        
        # Create directory if it doesn't exist
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Save XML files
        for key, xml_tree in self.xml.items():
            xml_path = self.path / f"{key}.xml"
            logger.debug(f"Saving XML file: {xml_path}")
            JavaSeisXML.save(xml_tree, xml_path)
        
        # Create trace map file
        logger.debug("Creating trace map file")
        self.create_map()
        
        # Create extent files first
        logger.debug("Creating extent files")
        trace_file_path = self.path / "TraceFile0"
        header_file_path = self.path / "TraceHeaders0"
        
        # Calculate sizes from XML
        trace_size = self.trace_struct.sizeof()
        header_size = self.header_struct.sizeof()
        total_traces = int(JavaSeisXML.get(self.xml["TraceFile"], "VFIO_MAXPOS"))
        
        # Pre-allocate files with correct sizes
        with open(trace_file_path, 'wb') as f:
            f.truncate(trace_size * total_traces)
        with open(header_file_path, 'wb') as f:
            f.truncate(header_size * total_traces)
        
        # Map extents after creating files
        logger.debug("Mapping extents")
        self.map_extents()

    def create_map(self):
        """Create and initialize the TraceMap file.
        
        The TraceMap is a binary file containing int32 values representing
        the number of traces (fold) for each frame. For a new dataset, all frames 
        are initialized with full fold. The file is organized as sequential volumes,
        where each volume's frames are stored contiguously.
        
        File structure:
        - Each frame's fold is stored as a 4-byte integer
        - Frames are stored sequentially within each volume
        - Volumes are stored sequentially in the file
        - File position = (volume_index * nframes * 4) + (frame_index * 4)
        """
        trace_map_path = self.path / "TraceMap"
        
        # Get dimensions from FileProperties XML
        fp_tree = self.xml["FileProperties"]
        axis_lengths = [int(x) for x in JavaSeisXML.get(fp_tree, "AxisLengths").split()]
        
        # Calculate dimensions
        nframes = axis_lengths[2]  # Frames per volume
        nvolumes = np.prod(axis_lengths[3:]) if len(axis_lengths) > 3 else 1
        
        # Always initialize with full fold for new datasets
        fold = axis_lengths[1]
        
        # Create array for all volumes
        total_frames = nframes * nvolumes
        array = np.full(total_frames, fold, dtype=np.int32)  # Must be int32 for 4-byte integers
        
        # Write to file in native byte order
        logger.debug(f"Creating TraceMap with {total_frames} frames ({nframes} frames x {nvolumes} volumes)")
        array.tofile(trace_map_path)

        # Create Status.properties
        status_path = self.path / "Status.properties"
        with open(status_path, 'w') as f:
            f.write("#pySeis - JavaSeis File Properties 2006.3\n")
            f.write(f"#UTC {datetime.now(pytz.utc)}\n")
            f.write("HasTraces=true\n")

        # Create Name.properties
        name_path = self.path / "Name.properties"
        description = self.path.stem  # Use filename without extension as description
        with open(name_path, 'w') as f:
            f.write("#pySeis - JavaSeis File Properties 2006.3\n")
            f.write(f"#UTC {datetime.now(pytz.utc)}\n")
            f.write(f"DescriptiveName={description}\n")

    def write_trace(self, trace_data: np.ndarray, headers: dict, trace_file, header_file):
        """Write a single trace and its headers to files using Construct.
        
        Args:
            trace_data: Numpy array of trace samples
            headers: Dictionary of header values
            trace_file: Open file handle for trace data
            header_file: Open file handle for headers
        """
        # Write header using the header struct
        header_bytes = self.header_struct.build(headers)
        header_file.write(header_bytes)
        
        # Build trace data using the trace struct
        compressed = self.trace_struct._encode(trace_data, None, None)
        
        # Calculate expected sizes
        windowln = 100
        nsamples = len(trace_data)
        nwindows = floor((nsamples - 1.0) / windowln) + 1
        
        # Write scalars (ensure little-endian float32)
        scalars = compressed.scalars.astype('<f4')  # float32 little-endian
        trace_file.write(scalars.tobytes())
        
        # Write samples (ensure little-endian uint16 and padding)
        samples = compressed.samples.astype('<u2')  # uint16 little-endian
        if len(trace_data) % 2 != 0:
            # Pad with an extra sample for odd lengths
            samples = np.append(samples, np.uint16(32767))
        
        trace_file.write(samples.tobytes())

    