import os
import io
import struct
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Union

from pyseis_io.core.writer import InternalFormatWriter
from pyseis_io.base import SeismicImporter
from pyseis_io.core.format_parser import FormatParser
from pyseis_io.utils import ibm2ieee

class SEGYImporter(SeismicImporter):
    """
    Reader for SEG-Y files that converts to pyseis-io internal format.
    Supports IBM Float to IEEE Float conversion.
    """
    
    def __init__(self, path: Union[str, Path], header_def: Optional[str] = None, mapping_path: Optional[str] = None):
        """
        Initialize the SEGY Importer.
        
        Args:
            path: Path to the SEGY file.
            header_def: Optional path to a YAML file defining the SEGY header structure.
                        Defaults to src/pyseis_io/segy/segy_format.yaml.
            mapping_path: Optional path to a YAML file defining SEGY->Core mapping.
                          Defaults to src/pyseis_io/segy/header_mapping.yaml.
        """
        self.segy_path = Path(path)
        if not self.segy_path.exists():
            raise FileNotFoundError(f"SEGY file not found: {path}")
            
        # Load header definition
        if header_def:
            self.header_def_path = Path(header_def)
        else:
            self.header_def_path = Path(__file__).parent / "segy_format.yaml"
            
        if not self.header_def_path.exists():
             raise FileNotFoundError(f"Header definition file not found: {self.header_def_path}")

        with open(self.header_def_path, 'r') as f:
            self.header_def = yaml.safe_load(f)
            
        if 'trace_header' not in self.header_def:
             raise ValueError("Invalid header definition format: missing 'trace_header'")
        if 'binary_header' not in self.header_def:
             raise ValueError("Invalid header definition format: missing 'binary_header'")
             
        self._trace_header_size = self.header_def['trace_header'].get('block_size', 240)
        self._binary_header_size = self.header_def['binary_header'].get('block_size', 400)
        self._ebcdic_header_size = self.header_def['ebcdic_header'].get('block_size', 3200)
        
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
        self._endian = '>' # SEGY is always Big Endian
        self._ns = None
        self._dt = None
        self._format_code = None
        self._file_size = self.segy_path.stat().st_size
        self.headers: Optional[pd.DataFrame] = None
        self.binary_header: Dict[str, Any] = {}
        self._trace_count = 0
        self._trace_stride = 0
        self.parser: Optional[FormatParser] = None

    def _read_binary_header(self, f):
        """Read and parse the binary header."""
        f.seek(self._ebcdic_header_size)
        bin_parser = FormatParser(self.header_def['binary_header'], endian=self._endian)
        dtype = bin_parser.build_read_dtype(fixed_size=self._binary_header_size)
        
        raw_bin = np.frombuffer(f.read(self._binary_header_size), dtype=dtype)
        # Convert to dict via DataFrame for consistency with parser tools (or just direct access)
        df = pd.DataFrame(raw_bin)
        processed_df = bin_parser.process_dataframe(df)
        self.binary_header = processed_df.iloc[0].to_dict()
        
        # Extract critical values
        self._format_code = self.binary_header.get('format', 5) # Default IEEE
        self._ns = self.binary_header.get('hns', 0)
        self._dt = self.binary_header.get('hdt', 0)
        
        # If hns/hdt are zero, check first trace header later? 
        # For strict SEGY, they should be in binary header. We will assume they are here for now.

    def scan(self) -> pd.DataFrame:
        """
        Scan all headers from the SEGY file.
        """
        with open(self.segy_path, 'rb') as f:
            # 1. Read Binary Header
            self._read_binary_header(f)
            
            # Validation
            if self._ns == 0:
                # Try reading from first trace header
                f.seek(self._ebcdic_header_size + self._binary_header_size)
                # Quick parse of ns from trace header (offset 114, 2 bytes)
                f.seek(114, 1) # Skip 114
                ns_bytes = f.read(2)
                self._ns = struct.unpack('>H', ns_bytes)[0]
                if self._ns == 0:
                     raise ValueError("Number of samples (ns) is 0 in both binary and trace header.")
            
            # 2. Calculate Stride
            # Sample size depends on format code.
            # 1=IBM(4), 2=Int32(4), 3=Int16(2), 5=IEEE(4), 8=Int8(1)
            # We focus on 1 and 5 for now (4 bytes)
            sample_size = 4 
            if self._format_code == 3: sample_size = 2
            elif self._format_code == 8: sample_size = 1
            elif self._format_code == 6: sample_size = 8
            
            self._trace_stride = self._trace_header_size + self._ns * sample_size
            
            # 3. Calculate Trace Count
            data_start = self._ebcdic_header_size + self._binary_header_size
            data_len = self._file_size - data_start
            
            if data_len % self._trace_stride != 0:
                print(f"Warning: File size implies partial traces. Truncating count.")
            
            self._trace_count = data_len // self._trace_stride
            
            # 4. Setup Parser for Trace Headers
            self.parser = FormatParser(self.header_def['trace_header'], endian=self._endian)
            read_dtype = self.parser.build_read_dtype(fixed_size=self._trace_header_size)
            
            # 5. Memmap Read
            # Offset for memmap
            offset = data_start
            
            # Structured dtype for strided read
            full_dtype = np.dtype([
                ('header', read_dtype),
                ('data', f'V{self._ns * sample_size}')
            ])
            
            mmap = np.memmap(
                self.segy_path,
                dtype=full_dtype,
                mode='r',
                offset=offset,
                shape=(self._trace_count,)
            )
            
            headers_struct = mmap['header']
            self.headers = pd.DataFrame(headers_struct)
            self.headers = self.parser.process_dataframe(self.headers)
            
            # 6. Apply Scalars
            self._apply_scalars()
            
            return self.headers

    def _apply_scalars(self):
        """Apply scalel and scalco to headers."""
        if self.headers is None: return
        df = self.headers
        
        # Coordinate Scalar (scalco)
        if 'scalco' in df.columns:
            coords = ['sx', 'sy', 'gx', 'gy']
            for col in coords:
                if col in df.columns:
                     df[col] = self._apply_segy_scalar(df[col], df['scalco'])

        # Elevation Scalar (scalel)
        if 'scalel' in df.columns:
            elevs = ['gelev', 'selev', 'sdepth', 'gdel', 'sdel', 'swdep', 'gwdep']
            for col in elevs:
                 if col in df.columns:
                      df[col] = self._apply_segy_scalar(df[col], df['scalel'])

    def _apply_segy_scalar(self, series, scalar_series):
        """
        Apply SEGY scalar logic.
        Positive: multiplier. Negative: divisor. Zero: 1.
        """
        out = series.astype(float)
        scalar = scalar_series.fillna(0).astype(int)
        
        # Mask negative (divisor)
        mask_div = scalar < 0
        div_val = scalar.abs()
        div_val[div_val == 0] = 1
        out[mask_div] = out[mask_div] / div_val[mask_div]
        
        # Mask positive (multiplier)
        mask_mul = scalar > 0
        out[mask_mul] = out[mask_mul] * scalar[mask_mul]
        
        return out

    def import_data(self, output_path: Union[str, Path, io.BytesIO], chunk_size: int = 1000, **kwargs) -> 'SeismicData':
        """
        Convert SEGY to single-Parquet internal dataset format.
        """
        if self.headers is None:
            raise RuntimeError("Headers not loaded. Call scan() first.")
             
        # Metadata
        dt_micros = self._dt if self._dt > 0 else 1000  # default 1ms
        sample_rate = dt_micros / 1_000_000.0
        
        # Apply column mapping to headers
        mapped_headers = self.headers.rename(columns=self.mapping)
        
        # Read trace amplitude data
        data_start = self._ebcdic_header_size + self._binary_header_size
        
        sample_bytes = 4
        if self._format_code == 3: sample_bytes = 2
        elif self._format_code == 8: sample_bytes = 1
        elif self._format_code == 6: sample_bytes = 8

        all_traces = np.zeros((self._trace_count, self._ns), dtype=np.float32)

        with open(self.segy_path, 'rb') as f:
            for i in range(0, self._trace_count, chunk_size):
                count = min(chunk_size, self._trace_count - i)
                chunk_stride_bytes = count * self._trace_stride
                start_offset = data_start + i * self._trace_stride
                
                f.seek(start_offset)
                raw_chunk = f.read(chunk_stride_bytes)
                
                chunk_arr = np.frombuffer(raw_chunk, dtype='uint8')
                if len(chunk_arr) < chunk_stride_bytes:
                    actual_count = len(chunk_arr) // self._trace_stride
                    chunk_arr = chunk_arr[:actual_count * self._trace_stride]
                    chunk_arr = chunk_arr.reshape((actual_count, self._trace_stride))
                else:
                    chunk_arr = chunk_arr.reshape((count, self._trace_stride))
                
                data_part = chunk_arr[:, self._trace_header_size:]
                flat_bytes = data_part.flatten()
                
                if self._format_code == 1:  # IBM Float
                    u32 = flat_bytes.view('>u4')
                    traces = ibm2ieee(u32)
                elif self._format_code == 5:  # IEEE Float
                    traces = flat_bytes.view('>f4')
                elif self._format_code == 2:  # Int32
                    traces = flat_bytes.view('>i4').astype(np.float32)
                elif self._format_code == 3:  # Int16
                    traces = flat_bytes.view('>i2').astype(np.float32)
                elif self._format_code == 8:  # Int8
                    traces = flat_bytes.view('i1').astype(np.float32)
                else:
                    traces = flat_bytes.view('>f4')
                
                all_traces[i:i + count, :] = traces.reshape((count, self._ns))

        writer = InternalFormatWriter(output_path, overwrite=True)
        writer.write(all_traces, mapped_headers, metadata={"sample_rate": sample_rate})

        from pyseis_io.core.dataset import SeismicData
        return SeismicData.open(output_path)
