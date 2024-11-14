import os
import sys
# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, List, Any
import numpy as np
from pyseis.io.segd_format import headers_format, traces_format
from construct import Struct, If, Array, Container
from io import BytesIO

class SegDReader:
    def __init__(self, filename: str):
        self.headers_format = headers_format
        self.traces_format = traces_format
        self.filename = filename
        self.file_handle = open(filename, "rb")
        self.headers = self.read_headers()
        self.traces = self.read_traces()
        
    def __del__(self):
        """Ensure file is closed when object is destroyed"""
        if hasattr(self, 'file_handle'):
            self.file_handle.close()

    def read_headers(self):
        """Read general headers and return current file position"""
        data = self.file_handle.read()
        stream = BytesIO(data)
        headers = self.headers_format.parse_stream(stream)
        # Store the current position after headers
        self.data_start_pos = stream.tell()
        return headers

    def read_traces(self):
        """Read all traces starting from end of general headers"""
        self.file_handle.seek(self.data_start_pos)
        return self.traces_format.parse_stream(self.file_handle, headers=self.headers)
    
    def write(self, output_filename: str):
        """Write the SEG-D file to a new file"""
        with open(output_filename, "wb") as f:
            # Write headers
            f.write(self.headers_format.build(self.headers))
            
            # Write traces - pass headers for trace count calculation
            f.write(self.traces_format.build(self.traces, headers=self.headers))

if __name__ == "__main__":
    # Read example
    reader = SegDReader("../../data/00016239.segd")
    print("Headers:")
    print(reader.headers)
    print("\nTraces:")
    for i, trace in enumerate(reader.traces.traces):
        print(f"Trace {i+1}:")
        print(f"  Scan Type: {trace.demux_header.scan_type_number}")
        print(f"  Channel Set: {trace.demux_header.channel_set_number}")
        print(f"  Trace Number: {trace.demux_header.trace_number}")
        print(f"  Data shape: {trace.trace_data.shape}")
    print(reader.traces.traces[0].trace_data)
    
    # Write example
    reader.write("../../data/00016239_copy.segd")
