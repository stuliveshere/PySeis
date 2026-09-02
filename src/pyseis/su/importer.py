import os
import io
import struct
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple

from pyseis.core.writer import InternalFormatWriter
from pyseis.base import SeismicImporter
from pyseis.core.format_parser import FormatParser

# Mapping SU headers to SeisData schema
# Key: SU header name (from su.yaml) -> Value: SeisData column name
class SUImporter(SeismicImporter):
    """
    Reader for Seismic Unix files that converts to pyseis internal format.
    Supports 'Scan -> Modify -> Convert' workflow.
    """
    
    def __init__(self, path: Union[str, Path], header_def: Optional[str] = None, mapping_path: Optional[str] = None):
        """
        Initialize the SU Converter.
        
        Args:
            path: Path to the SU file.
            header_def: Optional path to a YAML file defining the SU header structure.
                        Defaults to src/pyseis/su/su_format.yaml.
            mapping_path: Optional path to a YAML file defining SU->Core mapping.
                          Defaults to src/pyseis/su/header_mapping.yaml.
        """
        self.su_path = Path(path)
        if not self.su_path.exists():
            raise FileNotFoundError(f"SU file not found: {path}")
            
        # Load header definition
        if header_def:
            self.header_def_path = Path(header_def)
        else:
            self.header_def_path = Path(__file__).parent / "su_format.yaml"
            
        if not self.header_def_path.exists():
             raise FileNotFoundError(f"Header definition file not found: {self.header_def_path}")

        with open(self.header_def_path, 'r') as f:
            self.header_def = yaml.safe_load(f)
            
        if 'trace_header' not in self.header_def:
             raise ValueError("Invalid header definition format: missing 'trace_header'")
             
        # Extract fields, skipping metadata
        self.su_headers = {
            k: v for k, v in self.header_def['trace_header'].items() 
            if k not in ['block_label', 'block_offset', 'block_size']
        }
        
        self._header_size = self.header_def['trace_header'].get('block_size', 240)
        
        # Load Mapping
        if mapping_path:
             self.mapping_path = Path(mapping_path)
        else:
             self.mapping_path = Path(__file__).parent / "header_mapping.yaml"
             
        if not self.mapping_path.exists():
             raise FileNotFoundError(f"Mapping file not found: {self.mapping_path}")
             
        with open(self.mapping_path, 'r') as f:
             self.mapping = yaml.safe_load(f)

        # Internal state
        self._endian = None
        self._ns = None
        self._dt = None
        self._file_size = self.su_path.stat().st_size
        self.headers: Optional[pd.DataFrame] = None
        self._initial_trace_count = 0
        self._trace_stride = 0
        self.parser: Optional[FormatParser] = None

    def _detect_endianness(self, f) -> str:
        """
        Detect endianness by checking ns and dt sanity.
        """
        # Read first header
        f.seek(0)
        header_bytes = f.read(self._header_size)
        if len(header_bytes) < self._header_size:
             raise ValueError("File too short for header")
             
        # Definition for ns and dt
        # Helper to extract using simple offsets for detection
        # We assume ns/dt are standard simple integers
        
        defs = self.header_def['trace_header']
        ns_def = defs.get('ns')
        dt_def = defs.get('dt')
        
        if not ns_def or not dt_def:
             raise ValueError("ns and dt must be defined in header definition")
             
        # Helper to read value
        def read_val(bytes_data, def_, endian):
             start = def_['offset']
             n_bytes = int(def_['size']) # Ensure int for slicing
             fmt = self._get_fmt_char(def_['type'], n_bytes)
             return struct.unpack(f'{endian}{fmt}', bytes_data[start:start+n_bytes])[0]
             
        # Check Little Endian
        ns_le = read_val(header_bytes, ns_def, '<')
        dt_le = read_val(header_bytes, dt_def, '<')
        
        # Check Big Endian
        ns_be = read_val(header_bytes, ns_def, '>')
        dt_be = read_val(header_bytes, dt_def, '>')
        
        # Heuristics
        is_le_valid = 0 < ns_le < 100000 and 0 <= dt_le < 1000000
        is_be_valid = 0 < ns_be < 100000 and 0 <= dt_be < 1000000
        
        # refinement using file size
        file_size = self.su_path.stat().st_size
        
        if is_le_valid and is_be_valid:
             stride_le = self._header_size + ns_le * 4
             stride_be = self._header_size + ns_be * 4
             consistent_le = (file_size % stride_le == 0)
             consistent_be = (file_size % stride_be == 0)
             
             if consistent_le and not consistent_be: return '<'
             if consistent_be and not consistent_le: return '>'
             print("Warning: Endianness ambiguous, defaulting to Little Endian.")
             return '<'

        if is_le_valid: return '<'
        if is_be_valid: return '>'
             
        raise ValueError("Could not detect valid endianness.")

    def _get_fmt_char(self, fmt_type, n_bytes):
        """Map SU format/bytes to struct format character."""
        if fmt_type == 'uint':
            if n_bytes == 2: return 'H'
            if n_bytes == 4: return 'I'
        elif fmt_type == 'int':
            if n_bytes == 2: return 'h'
            if n_bytes == 4: return 'i'
        elif fmt_type == 'float':
            if n_bytes == 4: return 'f'
            if n_bytes == 8: return 'd'
        
        # Fallback
        if n_bytes == 2: return 'h'
        if n_bytes == 4: return 'i'
        return 'i' # Default

    def scan(self) -> pd.DataFrame:
        """
        Scan all headers from the SU file into a DataFrame.
        This reads ALL headers efficiently without reading trace data.
        
        Returns:
            pd.DataFrame: The headers dataframe (with SU column names).
        """
        with open(self.su_path, 'rb') as f:
            # 1. Detect Endianness & Geometry
            self._endian = self._detect_endianness(f)
            
            # Initialize Parser
            self.parser = FormatParser(self.header_def['trace_header'], endian=self._endian)
            
            # Read first header to get ns for stride (using parser logic implies reading via dtype, but stride calc needs it first)
            # Re-read basics manually for stride calc or use parser on small buffer
            f.seek(0)
            header_bytes = f.read(self._header_size)
            
            # we can use the same manual extract for ns/dt as they are needed for stride
            ns_def = self.header_def['trace_header']['ns']
            dt_def = self.header_def['trace_header']['dt']
            
            start_ns = ns_def['offset']
            fmt_ns = self._get_fmt_char(ns_def['type'], ns_def['size'])
            self._ns = struct.unpack(f'{self._endian}{fmt_ns}', header_bytes[start_ns:start_ns+int(ns_def['size'])])[0]
            
            start_dt = dt_def['offset']
            fmt_dt = self._get_fmt_char(dt_def['type'], dt_def['size'])
            self._dt = struct.unpack(f'{self._endian}{fmt_dt}', header_bytes[start_dt:start_dt+int(dt_def['size'])])[0]
            
            # Calculate stride
            self._trace_stride = self._header_size + self._ns * 4
            
            # Calculate number of traces
            if self._file_size % self._trace_stride != 0:
                print(f"Warning: File size {self._file_size} is not a multiple of trace stride {self._trace_stride}. Truncated/corrupt file?")
            
            self._initial_trace_count = self._file_size // self._trace_stride
            
            # 2. Build Read Dtype
            read_dtype = self.parser.build_read_dtype(fixed_size=self._header_size)
            
            # 3. Read Headers via Memory Map & Stride Tricks or simple memmap with offset
            # Using stride tricks allows skipping data blocks
            mmap = np.memmap(self.su_path, dtype='uint8', mode='r')
            cutoff = self._initial_trace_count * self._trace_stride
            if cutoff > len(mmap):
                 mmap = mmap[:cutoff]
            
            # We want to view the 'header' part of every stride as a structured array record
            full_dtype = np.dtype([
                ('header', read_dtype),
                ('data', f'V{self._ns * 4}')
            ])
            
            # Use memmap with structured dtype
            data_array = np.memmap(
                self.su_path,
                dtype=full_dtype,
                mode='r',
                shape=(self._initial_trace_count,)
            )

            # Extract header part
            headers_struct = data_array['header']
            
            # Convert to DataFrame
            # structured array to dataframe is zero-copy usually or efficient
            self.headers = pd.DataFrame(headers_struct)
            
            # 4. Post Processing
            self.headers = self.parser.process_dataframe(self.headers)
            
            # 5. Scale (Apply SU-specific scaling)
            self._apply_scalars_raw()
            
            return self.headers

    def _apply_scalars_raw(self):
        """Apply SU scalar logic to raw SU columns."""
        if self.headers is None: return
        
        df = self.headers
        
        # Coordinate Scalar (scalco)
        if 'scalco' in df.columns:
            # scalco applies to sx, sy, gx, gy
            coords = ['sx', 'sy', 'gx', 'gy']
            for col in coords:
                if col in df.columns:
                    df[col] = self._apply_scalar(df[col], df['scalco'])
                    
        # Elevation Scalar (scalel)
        if 'scalel' in df.columns:
            # scalel applies to gelev, selev, sdepth, gdel, sdel, swdep, gwdep
            elevs = ['gelev', 'selev', 'sdepth', 'gdel', 'sdel', 'swdep', 'gwdep']
            for col in elevs:
                if col in df.columns:
                    df[col] = self._apply_scalar(df[col], df['scalel'])

    def _apply_scalar(self, series, scalar_series):
        """Apply SU scalar logic."""
        # copy to float
        out = series.astype(float)
        
        # Mask for scal < 0 (divisor)
        mask_div = scalar_series < 0
        div_val = scalar_series.abs()
        # Avoid division by zero
        div_val[div_val == 0] = 1 
        
        out[mask_div] = out[mask_div] / div_val[mask_div]
        
        # Mask for scal > 0 (multiplier)
        mask_mul = scalar_series > 0
        out[mask_mul] = out[mask_mul] * scalar_series[mask_mul]
        
        return out


    def import_data(self, output_path: Union[str, Path, io.BytesIO], chunk_size: int = 1000, **kwargs) -> 'SeismicData':
        """
        Convert the SU file to single-Parquet internal dataset format.
        """
        if self.headers is None:
            raise RuntimeError("Headers not loaded. Call scan() first.")
            
        if len(self.headers) != self._initial_trace_count:
            raise ValueError(f"Header count mismatch: Expected {self._initial_trace_count}, got {len(self.headers)}.")
             
        sample_rate = self._dt / 1_000_000.0  # micros -> seconds
        mapped_headers = self.headers.rename(columns=self.mapping)
        
        all_traces = np.zeros((self._initial_trace_count, self._ns), dtype=np.float32)
        
        with open(self.su_path, 'rb') as f:
            for i in range(self._initial_trace_count):
                offset = i * self._trace_stride + self._header_size
                f.seek(offset)
                data_bytes = f.read(self._ns * 4)
                
                trace_data = np.frombuffer(data_bytes, dtype=np.float32)
                sys_endian = '<' if np.little_endian else '>'
                if self._endian != sys_endian:
                    trace_data = trace_data.byteswap()
                    
                all_traces[i, :] = trace_data
                
        writer = InternalFormatWriter(output_path, overwrite=True)
        writer.write(all_traces, mapped_headers, metadata={"sample_rate": sample_rate})
        
        from pyseis.core.dataset import SeismicData
        return SeismicData.open(output_path)
