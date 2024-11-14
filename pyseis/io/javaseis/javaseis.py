# javaseis.py

import os
import sys
import warnings
import numpy as np
from lxml import etree
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import os.path as osp
from collections import OrderedDict

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)

from pyseis.io.javaseis.javaseis_format import build_header_struct, build_trace_struct
from pyseis.io.javaseis.xml_base import XMLHandler
from pyseis.io.javaseis.utils import _validate_js_dir

class JavaSeis:
    """JavaSeis dataset reader/writer."""
    
    def __init__(self, path=None):
        self.path = path
        # Add header label lookup map
        self._header_label_map = {}  # label -> entry_n mapping
        if path is not None:
            self.load_existing()

    def load_existing(self):
        """Load existing JavaSeis dataset."""
        _validate_js_dir(self.path)
        self._load_xml()
        self._build_header_label_map()

    def _load_xml(self):
        """Load XML trees and create handlers."""
        self.xml_data = {}
        
        # Load all required XML files
        required_xml = [
            'FileProperties',
            'TraceFile', 
            'TraceHeaders',
            'VirtualFolders'
        ]
        
        for xml_name in required_xml:
            xml_path = osp.join(self.path, f"{xml_name}.xml")
            if not osp.exists(xml_path):
                raise ValueError(f"Missing required XML file: {xml_path}")

            # Parse XML to OrderedDict
            tree = etree.parse(xml_path)
            self.xml_data[xml_name] = XMLHandler(tree)
            self.xml_data[xml_name].load()
        self.file_properties = self.xml_data['FileProperties'].data['FileProperties']
        self.trace_properties = self.xml_data['FileProperties'].data['TraceProperties']
        self.custom_properties = self.xml_data['FileProperties'].data['CustomProperties']

    def _build_header_label_map(self):
        """Build mapping of header labels to entry keys."""
        self._header_label_map = {}
        for entry_key, header_dict in self.trace_properties.items():
            if isinstance(header_dict, OrderedDict) and 'label' in header_dict:
                self._header_label_map[header_dict['label']] = entry_key

    def get_header(self, label: str) -> Optional[OrderedDict]:
        """Get header dictionary by label.
        
        Args:
            label: Header label to retrieve
            
        Returns:
            OrderedDict containing header properties or None if not found
        """
        if not self._header_label_map:
            self._build_header_label_map()
            
        entry_key = self._header_label_map.get(label)
        if entry_key:
            return self.trace_properties[entry_key]
        return None

    def set_header(self, label: str, header_dict: OrderedDict) -> None:
        """Update existing header dictionary.
        
        Args:
            label: Header label to update
            header_dict: New header properties
        
        Raises:
            ValueError: If header label doesn't exist
        """
        if not self._header_label_map:
            self._build_header_label_map()
            
        entry_key = self._header_label_map.get(label)
        if not entry_key:
            raise ValueError(f"Header '{label}' not found")
            
        self.trace_properties[entry_key] = header_dict

    def delete_header(self, label: str) -> None:
        """Delete header and update byte offsets.
        
        Args:
            label: Header label to delete
        
        Raises:
            ValueError: If header label doesn't exist
        """
        if not self._header_label_map:
            self._build_header_label_map()
            
        entry_key = self._header_label_map.get(label)
        if not entry_key:
            raise ValueError(f"Header '{label}' not found")
        
        # Get the byte length of header being deleted
        header_length = int(self.trace_properties[entry_key].get('byteOffset', 0))
        
        # Remove from properties and label map
        del self.trace_properties[entry_key]
        del self._header_label_map[label]
        
        # Update remaining byte offsets
        for key, header in self.trace_properties.items():
            if isinstance(header, OrderedDict) and 'byteOffset' in header:
                current_offset = int(header['byteOffset'])
                if current_offset > header_length:
                    header['byteOffset'] = str(current_offset - header_length)
        
        # Update total header length in file properties
        current_total = int(self.file_properties['HeaderLengthBytes'])
        self.file_properties['HeaderLengthBytes'] = str(current_total - header_length)

    def create_header(self, label: str, header_dict: OrderedDict) -> None:
        """Create new header at end of trace properties.
        
        Args:
            label: Header label for new header
            header_dict: Header properties dictionary
            
        Raises:
            ValueError: If header label already exists
        """
        if not self._header_label_map:
            self._build_header_label_map()
            
        if label in self._header_label_map:
            raise ValueError(f"Header '{label}' already exists")
        
        # Find next entry number
        entry_nums = [int(k.split('_')[1]) for k in self.trace_properties.keys() 
                     if k.startswith('entry_')]
        next_num = max(entry_nums) + 1 if entry_nums else 1
        new_entry_key = f'entry_{next_num}'
        
        # Calculate new byte offset
        last_header = None
        last_offset = 0
        for header in self.trace_properties.values():
            if isinstance(header, OrderedDict) and 'byteOffset' in header:
                last_header = header
                last_offset = int(header['byteOffset'])
        
        if last_header:
            new_offset = last_offset + int(last_header.get('byteLength', 0))
        else:
            new_offset = 0
            
        # Set byte offset in new header
        header_dict['byteOffset'] = str(new_offset)
        
        # Add new header
        self.trace_properties[new_entry_key] = header_dict
        self._header_label_map[label] = new_entry_key
        
        # Update total header length in file properties
        current_total = int(self.file_properties['HeaderLengthBytes'])
        header_length = int(header_dict.get('byteLength', 0))
        self.file_properties['HeaderLengthBytes'] = str(current_total + header_length)

        
    #     # Handle TraceProperties separately (it's inside FileProperties.xml)
    #     trace_props_tree = self.xml_trees['FileProperties'].find(".//parset[@name='TraceProperties']")
    #     if trace_props_tree is not None:
    #         self.xml_handlers['TraceProperties'] = create_xml_handler('TraceProperties', trace_props_tree)
    #     else:
    #         raise ValueError("No TraceProperties section found in FileProperties.xml")
        
    #     # Get key properties using handlers
    #     file_props = self.xml_handlers['FileProperties']
    #     self.trace_format = file_props.get_property("TraceFormat")
    #     self.byte_order = file_props.get_property("ByteOrder", default='LITTLE_ENDIAN')
    #     self.header_length = file_props.get_property("HeaderLengthBytes", cast_type=int)
    #     self.axis_lengths = file_props.get_property("AxisLengths", cast_type=int, multiple=True)
        
    #     # Build format structs
    #     self.header_struct = build_header_struct(
    #         self.xml_handlers['TraceProperties'].list_headers(),
    #         self.byte_order.lower()
    #     )
    #     self.trace_struct = build_trace_struct(
    #         self.axis_lengths[0],  # nsamples
    #         self.byte_order.lower()
    #     )
        
    #     # Initialize extent lists
    #     self.trace_extents = []
    #     self.header_extents = []
    #     self.check_extents()

    # @classmethod
    # def create(cls, path: str, axis_lengths: List[int], 
    #            trace_format: str = "COMPRESSED_INT16",
    #            byte_order: str = "LITTLE_ENDIAN",
    #            custom_headers: List[Dict] = None,
    #            template_path: str = None):
    #     """Create a new JavaSeis dataset.
        
    #     Args:
    #         path: Path to create dataset
    #         axis_lengths: List of axis lengths [nsamples, ntraces] or [nsamples, nxlines, ninlines]
    #         trace_format: Trace format (default: COMPRESSED_INT16)
    #         byte_order: Byte order (default: LITTLE_ENDIAN)
    #         custom_headers: List of custom header definitions [{'name', 'description', 'format'}, ...]
    #         template_path: Path to template XML file (default: use built-in template)
    #     """
    #     # Create directory
    #     os.makedirs(path, exist_ok=True)
        
    #     # Load and modify template
    #     if template_path is None:
    #         template_path = osp.join(osp.dirname(__file__), 'FileProperties_default.xml')
        
    #     tree = etree.parse(template_path)
    #     file_props = tree.find(".//parset[@name='FileProperties']")
        
    #     # Update key properties
    #     props_to_update = {
    #         "TraceFormat": trace_format,
    #         "ByteOrder": byte_order,
    #         "DataDimensions": str(len(axis_lengths)),
    #         "AxisLengths": " ".join(map(str, axis_lengths)),
    #         "HeaderLengthBytes": "72"  # From template
    #     }
        
    #     for name, value in props_to_update.items():
    #         elem = file_props.find(f".//par[@name='{name}']")
    #         if elem is not None:
    #             elem.text = value
        
    #     # Save modified FileProperties.xml
    #     filepath = osp.join(path, "FileProperties.xml")
    #     tree.write(filepath, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        
    #     # Create TraceFile.xml
    #     trace_file = etree.Element("properties")
    #     par = etree.SubElement(trace_file, "par")
    #     par.set("name", "VFIO_EXTNAME")
    #     par.text = "TraceFile"
        
    #     filepath = osp.join(path, "TraceFile.xml")
    #     etree.ElementTree(trace_file).write(filepath, pretty_print=True, 
    #                                       xml_declaration=True, encoding='UTF-8')
        
    #     # Create TraceHeaders.xml
    #     trace_headers = etree.Element("properties")
    #     par = etree.SubElement(trace_headers, "par")
    #     par.set("name", "VFIO_EXTNAME")
    #     par.text = "TraceHeaders"
        
    #     filepath = osp.join(path, "TraceHeaders.xml")
    #     etree.ElementTree(trace_headers).write(filepath, pretty_print=True, 
    #                                          xml_declaration=True, encoding='UTF-8')
        
    #     # Create empty property files
    #     for fname in ['Name.properties', 'Status.properties']:
    #         with open(osp.join(path, fname), 'w') as f:
    #             f.write('')
        
    #     # Initialize dataset
    #     js = cls(path)
        
    #     # Add custom headers if provided
    #     if custom_headers:
    #         for header in custom_headers:
    #             js.xml_handlers['TraceProperties'].add_header(**header)
    #         js.save_xml_file('FileProperties')
        
    #     # Create initial extent files
    #     js._create_extent_files()
        
    #     return js


    # def _create_extent_files(self):
    #     """Create initial empty extent files."""
    #     # Calculate total traces
    #     total_traces = self.axis_lengths[1]
    #     if len(self.axis_lengths) > 2:
    #         total_traces *= self.axis_lengths[2]
        
    #     # Calculate file sizes
    #     header_size = self.header_length * total_traces
    #     trace_size = self.trace_struct.trclen * total_traces
        
    #     # Create extent files
    #     trace_name = self.xml_handlers['TraceFile'].get_property("VFIO_EXTNAME")
    #     header_name = self.xml_handlers['TraceHeaders'].get_property("VFIO_EXTNAME")
        
    #     with open(osp.join(self.path, f"{trace_name}0"), 'wb') as f:
    #         f.truncate(trace_size)
        
    #     with open(osp.join(self.path, f"{header_name}0"), 'wb') as f:
    #         f.truncate(header_size)

    # def check_extents(self):
    #     """Check that the extents are valid and build extent lists."""
    #     # Get extent names from XML
    #     trace_name = self.xml_handlers['TraceFile'].get_property("VFIO_EXTNAME")
    #     header_name = self.xml_handlers['TraceHeaders'].get_property("VFIO_EXTNAME")
        
    #     # Parse VirtualFolders.xml for filesystem info
    #     vf_path = osp.join(self.path, "VirtualFolders.xml")
    #     if osp.exists(vf_path):
    #         vf_tree = etree.parse(vf_path)
    #         vf_handler = create_xml_handler('FileProperties', vf_tree)
    #         n_dirs = vf_handler.get_property("NDIR", cast_type=int)
            
    #         # Get filesystem paths
    #         paths = []
    #         for i in range(n_dirs):
    #             fs_path = vf_handler.get_property(f"FILESYSTEM-{i}")
    #             if fs_path:
    #                 path = fs_path.split(',')[0].strip()  # Split off the READ_WRITE part
    #                 if path == '.':
    #                     path = self.path
    #                 paths.append(path)
    #     else:
    #         paths = [self.path]
        
    #     # Find all extent files
    #     extent_num = 0
    #     while True:
    #         trace_found = header_found = False
            
    #         for path in paths:
    #             # Try both with and without the path prefix
    #             possible_paths = [
    #                 self.path,  # Try dataset path first
    #                 path,
    #                 osp.join(path, osp.basename(self.path)),
    #                 osp.dirname(self.path)
    #             ]
                
    #             for try_path in possible_paths:
    #                 trace_path = osp.join(try_path, f"{trace_name}{extent_num}")
    #                 header_path = osp.join(try_path, f"{header_name}{extent_num}")
                    
    #                 if osp.exists(trace_path):
    #                     self.trace_extents.append(trace_path)
    #                     trace_found = True
                        
    #                 if osp.exists(header_path):
    #                     self.header_extents.append(header_path)
    #                     header_found = True
                    
    #                 if trace_found and header_found:
    #                     break
                
    #             if trace_found and header_found:
    #                 break
            
    #         if not (trace_found and header_found):
    #             break
                
    #         extent_num += 1
        
    #     if not self.trace_extents:
    #         warnings.warn("No trace extents found")
    #     if not self.header_extents:
    #         warnings.warn("No header extents found")

    # def save_xml_file(self, section):
    #     """Save XML section to file."""
    #     handler = self.xml_handlers.get(section)
    #     if handler is not None:
    #         filepath = osp.join(self.path, f"{section}.xml")
    #         handler.save(filepath)

    # def reload_xml(self):
    #     """Reload all XML files from disk."""
    #     for section in self.xml_handlers:
    #         tree = etree.parse(osp.join(self.path, f"{section}.xml"))
    #         self.xml_trees[section] = tree
    #         self.xml_handlers[section] = create_xml_handler(section, tree)

    # def read_trace_header(self, extent_index: int, trace_index: int) -> Dict:
    #     """Read a single trace header."""
    #     extent = self.header_extents[extent_index]
    #     with open(extent, 'rb') as f:
    #         offset = trace_index * self.header_length
    #         f.seek(offset)
    #         return self.header_struct.parse_stream(f)

    # def write_trace_header(self, extent_index: int, trace_index: int, header_data: Dict):
    #     """Write a single trace header."""
    #     extent = self.header_extents[extent_index]
    #     with open(extent, 'rb+') as f:
    #         offset = trace_index * self.header_length
    #         f.seek(offset)
    #         self.header_struct.build_stream(header_data, f)

    # def read_trace(self, extent_index: int, trace_index: int) -> np.ndarray:
    #     """Read a single trace."""
    #     extent = self.trace_extents[extent_index]
    #     with open(extent, 'rb') as f:
    #         offset = trace_index * self.trace_struct.trclen
    #         f.seek(offset)
    #         return self.trace_struct.parse_stream(f)

    # def write_trace(self, extent_index: int, trace_index: int, trace_data: np.ndarray):
    #     """Write a single trace."""
    #     extent = self.trace_extents[extent_index]
    #     with open(extent, 'rb+') as f:
    #         offset = trace_index * self.trace_struct.trclen
    #         f.seek(offset)
    #         self.trace_struct.build_stream(trace_data, f)

    # def read_trace_and_header(self, extent_index: int, trace_index: int) -> Tuple[np.ndarray, Dict]:
    #     """Read both trace and header."""
    #     return (
    #         self.read_trace(extent_index, trace_index),
    #         self.read_trace_header(extent_index, trace_index)
    #     )

    # def read_frame(self, frame_index: int) -> Tuple[np.ndarray, List[Dict]]:
    #     """Read a complete frame of traces and headers."""
    #     if not self.trace_extents or not self.header_extents:
    #         raise ValueError("No extent files found")
        
    #     # Get data dimensions
    #     ndims = self.xml_handlers['FileProperties'].get_property("DataDimensions", cast_type=int)
    #     if ndims not in [2, 3]:
    #         raise ValueError(f"Unsupported data dimensions: {ndims}")
        
    #     # Handle 2D data
    #     if ndims == 2:
    #         if frame_index != 0:
    #             raise ValueError("2D data only has one frame (index must be 0)")
    #         ntraces = self.axis_lengths[1]  # All traces
    #         frame_size = ntraces
    #         frame_start = 0
            
    #     # Handle 3D data
    #     else:  # ndims == 3
    #         nxlines = self.axis_lengths[1]   # Crosslines per inline
    #         ninlines = self.axis_lengths[2]  # Total inlines
    #         if frame_index >= ninlines:
    #             raise ValueError(f"Frame (inline) index {frame_index} exceeds dataset size ({ninlines} inlines)")
    #         frame_size = nxlines
    #         frame_start = frame_index * nxlines
        
    #     traces = []
    #     headers = []
        
    #     # Calculate traces per extent
    #     traces_per_extent = os.path.getsize(self.trace_extents[0]) // self.trace_struct.trclen
        
    #     # Read all traces in the frame
    #     for i in range(frame_size):
    #         global_trace = frame_start + i
    #         extent_index = global_trace // traces_per_extent
    #         trace_index = global_trace % traces_per_extent
            
    #         if extent_index >= len(self.trace_extents):
    #             break
            
    #         trace = self.read_trace(extent_index, trace_index)
    #         header = self.read_trace_header(extent_index, trace_index)
    #         traces.append(trace)
    #         headers.append(header)
        
    #     if not traces:
    #         raise ValueError(f"No traces read for frame {frame_index}")
        
    #     # Convert traces list to numpy array
    #     traces = np.array(traces)
        
    #     return traces, headers

    # def read_live_frame(self, frame_index: int) -> Tuple[np.ndarray, List[Dict]]:
    #     """Read a frame and return only live traces (TRC_TYPE != 0)."""
    #     # Read full frame
    #     traces, headers = self.read_frame(frame_index)
        
    #     # Create mask for live traces, default to True if TRC_TYPE not found
    #     live_mask = np.array([header.get('TRC_TYPE', 1) != 0 for header in headers])
        
    #     # Filter traces and headers
    #     live_traces = traces[live_mask]
    #     live_headers = [h for h, m in zip(headers, live_mask) if m]
        
    #     return live_traces, live_headers

    # def write_frame(self, frame_index: int, traces: np.ndarray, headers: List[Dict]):
    #     """Write a complete frame of traces and headers.
        
    #     Args:
    #         frame_index: Frame index to write
    #         traces: Numpy array of trace data [ntraces x nsamples]
    #         headers: List of trace header dictionaries
    #     """
    #     if not self.trace_extents or not self.header_extents:
    #         raise ValueError("No extent files found")
            
    #     # Get frame dimensions
    #     ndims = self.xml_handlers['FileProperties'].get_property("DataDimensions", cast_type=int)
    #     if ndims not in [2, 3]:
    #         raise ValueError(f"Unsupported data dimensions: {ndims}")
            
    #     # Calculate frame size and start
    #     if ndims == 2:
    #         if frame_index != 0:
    #             raise ValueError("2D data only has one frame (index must be 0)")
    #         frame_size = self.axis_lengths[1]
    #         frame_start = 0
    #     else:
    #         frame_size = self.axis_lengths[1]
    #         frame_start = frame_index * self.axis_lengths[1]
            
    #     # Validate input dimensions
    #     if len(traces) != len(headers) or len(traces) > frame_size:
    #         raise ValueError("Mismatched traces/headers or too many traces for frame")
            
    #     # Calculate traces per extent
    #     traces_per_extent = os.path.getsize(self.trace_extents[0]) // self.trace_struct.trclen
        
    #     # Write traces and headers
    #     for i, (trace, header) in enumerate(zip(traces, headers)):
    #         global_trace = frame_start + i
    #         extent_index = global_trace // traces_per_extent
    #         trace_index = global_trace % traces_per_extent
            
    #         if extent_index >= len(self.trace_extents):
    #             break
                
    #         self.write_trace(extent_index, trace_index, trace)
    #         self.write_trace_header(extent_index, trace_index, header)


if __name__ == "__main__":
    js_path = "/misc/softwareStor/sfletcher/git/PySeis/data/javaseis"
    js = JavaSeis(js_path) 
    # # Read first frame (live traces only)
    # traces, headers = js.read_live_frame(1)
    
    # print("\nFrame summary:")
    # print(f"Total traces in dataset: {js.axis_lengths[1] * js.axis_lengths[2]}")
    # print(f"Live traces: {len(traces)}")
    # print(f"Trace shape: {traces.shape}")
    
    # print(dir(headers[0]))
    # print(f"\nFirst trace min/max:")
    # print(f"Min: {traces[0].min():.3f}")
    # print(f"Max: {traces[0].max():.3f}")
