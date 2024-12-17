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

    def convert_to_seisdata(self, schema_file: str = None) -> 'SeisData':
        """Convert SEG-D data to SeisData format.
        
        Args:
            schema_file: Path to SeisData schema file. If None, uses default schema.
            
        Returns:
            SeisData: Converted data in SeisData format
        """
        from pyseis.io.seisdata.seisdata import SeisData
        import os
        
        # Use default schema if none provided
        if schema_file is None:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            schema_file = os.path.join(current_dir, "seisdata", "seisdata_schema.yaml")
        
        # Initialize SeisData instance
        seisdata = SeisData(schema_file=schema_file)
        
        # Add source information
        source_info = {
            'source_id': str(self.data.data.general_header1.file_number),
            'file_number': int(self.data.data.general_header1.file_number),
            'source_index': 1,  # Default if not available
            'datetime': f"{self.data.data.general_header1.year:02d}-{self.data.data.general_header1.day:03d} "
                       f"{self.data.data.general_header1.hour:02d}:{self.data.data.general_header1.minute:02d}:"
                       f"{self.data.data.general_header1.second:02d}",
            'num_channels': self.data.data.total_traces
        }
        
        # Add source point information if available in general_headers_n
        if hasattr(self.data.data, 'general_headers_n') and self.data.data.general_headers_n:
            gh_n = self.data.data.general_headers_n[0]  # Use first extended header
            source_info.update({
                'source_line': gh_n.source_line_number_int + gh_n.source_line_number_frac,
                'source_point_number': gh_n.source_point_number_int + gh_n.source_point_number_frac,
                'source_point_index': gh_n.source_point_index
            })
        
        seisdata.add_source(source_info)
        
        # Process each trace
        for i, trace in enumerate(self.data.data.traces):
            ext = trace.trace_header_extensions.ext1
            
            # Add receiver information
            receiver_info = {
                'receiver_id': str(ext.receiver_line_number),
                'receiver_index': i,
                'receiver_line': ext.receiver_line_number,
                'receiver_station': ext.receiver_point_number,
                'num_samples': ext.samples_per_trace,
                'sample_rate': 2.0,  # Default sample rate in ms
                'sensor_type': ext.sensor_type_description
            }
            
            # Add extended receiver information if available
            receiver_info.update({
                'receiver_x': float(ext.extended_receiver_line_number_int + ext.extended_receiver_line_number_frac),
                'receiver_y': float(ext.extended_receiver_point_number_int + ext.extended_receiver_point_number_frac)
            })
            
            seisdata.add_receiver(receiver_info)
            
            # Add trace information
            trace_info = {
                'trace_id': i,
                'source_id': source_info['source_id'],
                'receiver_id': receiver_info['receiver_id'],
                'cdp_id': f"{source_info['source_id']}_{receiver_info['receiver_id']}",
                'trace_data': np.array(trace.trace_data)
            }
            seisdata.add_trace(trace_info)
        
        # Add instrument metadata
        seisdata.set_common_metadata('instrument', {
            'instrument_type': 'SEGD',
            'instrument_manufacturer': f"Code {self.data.data.general_header1.manufacturer_code}",
            'serial_number': str(self.data.data.general_header1.manufacturer_serial),
            'sensor_type': 'Mixed',  # Could be refined based on channel set headers
            'ADC_resolution': f"{self.data.data.general_header1.format_description}"
        })
        
        return seisdata

    def save_to_hdf5(self, output_file: str, schema_file: str = None) -> None:
        """Convert to SeisData and save as HDF5 file.
        
        Args:
            output_file: Path to output HDF5 file
            schema_file: Optional path to SeisData schema file
        """
        seisdata = self.convert_to_seisdata(schema_file)
        
        # Save to HDF5
        store = pd.HDFStore(output_file, mode='w')
        store['sources'] = seisdata.sources
        store['receivers'] = seisdata.receivers
        store['trace_headers'] = seisdata.trace_headers
        store['trace_data'] = seisdata.trace_data
        store['instrument'] = seisdata.instrument
        store.close()
        
        print(f"Saved to {output_file}")



