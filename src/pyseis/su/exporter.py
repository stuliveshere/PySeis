"""
SU Writer for exporting pyseis internal format to Seismic Unix files.
"""

import os
import struct
"""
SU Writer for exporting pyseis internal format to Seismic Unix files.
"""

import os
import struct
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Union

from pyseis.core.dataset import SeismicData
from pyseis.core.writer import InternalFormatWriter
from pyseis.base import SeismicExporter
from pyseis.core.format_parser import FormatParser

class SUExporter(SeismicExporter):
    """
    Writer for exporting internal format to SU files.
    """
    
    def __init__(self, seismic_data: Union[SeismicData, str, Path], header_def: Optional[str] = None):
        """
        Initialize the SU Writer.
        
        Args:
            seismic_data: SeismicData object or path to the input pyseis dataset.
            header_def: Optional path to a YAML file defining the SU header structure.
                        Defaults to src/pyseis/su/su_format.yaml.
        """
        if isinstance(seismic_data, (str, Path)):
             self.seismic_data_path = Path(seismic_data)
             if not self.seismic_data_path.exists():
                 raise FileNotFoundError(f"Seismic dataset not found: {seismic_data}")
             self._sd_instance = None
        elif isinstance(seismic_data, SeismicData):
             self._sd_instance = seismic_data
             self.seismic_data_path = seismic_data.file_path
        else:
             raise ValueError("seismic_data must be a Path/str or SeismicData object")
            
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
        
        self._header_size = self.header_def['trace_header'].get('block_size', 240)
        
        # Initialize Parser (endian neutral until export)
        self.parser = FormatParser(self.header_def['trace_header'])
        self.su_headers = self.parser.fields # access stripped fields
        
        # Load Mapping
        mapping_path = Path(__file__).parent / "header_mapping.yaml"
        if not mapping_path.exists():
             raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
             
        with open(mapping_path, 'r') as f:
             self.mapping = yaml.safe_load(f)
             
        # Create reverse mapping: Core -> SU
        self.reverse_mapping = {v: k for k, v in self.mapping.items()}

    def export(self, output_path: Union[str, Path], endian: str = '<', **kwargs) -> None:
        """
        Export to SU file.
        
        Args:
            output_path: Path to the output SU file.
            endian: Endianness for output ('<' for little, '>' for big).
        """
        output_su_path = Path(output_path)
        
        # Open dataset if not already
        if self._sd_instance:
             sd = self._sd_instance
        else:
             sd = SeismicData.open(self.seismic_data_path)
        
        # Update parser endianness
        self.parser.endian = endian
        header_dtype = self.parser.build_read_dtype(fixed_size=self._header_size)
        
        # Data chunking
        chunk_size = 1000
        n_traces = sd.n_traces
        
        # Determine data dtype
        data_dtype_str = f'{endian}f4'
        ns = sd.n_samples
        
        # Composite dtype for vectorized write
        # (header, 240 bytes) + (data, ns*4 bytes)
        composite_dtype = np.dtype([
            ('header', header_dtype),
            ('data', (data_dtype_str, (ns,)))
        ])
        
        with open(output_su_path, 'wb') as f:
            for i in range(0, n_traces, chunk_size):
                end = min(i + chunk_size, n_traces)
                # Slice
                chunk_sd = sd[i:end]
                
                # Compute to get data and headers
                traces, headers = chunk_sd.compute()
                
                # 1. Process headers same as before
                su_headers_df = pd.DataFrame(index=headers.index)
                
                for seis_key, su_key in self.reverse_mapping.items():
                    if seis_key in headers.columns:
                        su_headers_df[su_key] = headers[seis_key]
                
                # Conversions & Sanitization
                # Fill missing keys with 0
                for key in self.su_headers:
                    if key not in su_headers_df.columns:
                        su_headers_df[key] = 0
                
                # Fill NaNs
                su_headers_df = su_headers_df.fillna(0)
                        
                # Type conversions
                # source_id, receiver_id etc.
                for su_key in ['fldr', 'tracr', 'cdp', 'corr']:
                    if su_key in su_headers_df.columns:
                         su_headers_df[su_key] = su_headers_df[su_key].astype(int)

                # Scalars logic (simplified from previous)
                # ... [Keep scalar logic] ...
                # Re-implementing scalar logic briefly
                coords = ['sx', 'sy', 'gx', 'gy']
                needs_scaling = False
                for c in coords:
                    if c in su_headers_df.columns and not pd.api.types.is_integer_dtype(su_headers_df[c]):
                        needs_scaling = True
                        break
                
                if needs_scaling:
                    scalar = -1000
                    su_headers_df['scalco'] = scalar
                    for c in coords:
                        if c in su_headers_df.columns:
                            su_headers_df[c] = (su_headers_df[c] * abs(scalar)).fillna(0).astype(int)
                else:
                    su_headers_df['scalco'] = 1

                elevs = ['gelev', 'selev', 'sdepth', 'gdel', 'sdel', 'swdep', 'gwdep']
                needs_elev_scaling = False
                for c in elevs:
                    if c in su_headers_df.columns and not pd.api.types.is_integer_dtype(su_headers_df[c]):
                        needs_elev_scaling = True
                        break
                if needs_elev_scaling:
                    scalar = -1000
                    su_headers_df['scalel'] = scalar
                    for c in elevs:
                        if c in su_headers_df.columns:
                            su_headers_df[c] = (su_headers_df[c] * abs(scalar)).fillna(0).astype(int)
                else:
                    su_headers_df['scalel'] = 1

                # Set ns, dt
                dt_micros = int(sd.sample_rate * 1_000_000)
                su_headers_df['ns'] = ns
                su_headers_df['dt'] = dt_micros
                
                # Pack DF (if needed)
                su_headers_df = self.parser.pack_dataframe(su_headers_df)
                
                # 2. Vectorized Write
                chunk_len = len(su_headers_df)
                buffer = np.zeros(chunk_len, dtype=composite_dtype)
                
                # Assign headers
                # We iterate fields in header_dtype to assign from df
                for name in header_dtype.names:
                    # format_parser handles _raw_ names if needed, but su_headers_df should have them if pack_dataframe worked.
                    # For SU std, names match directly.
                    if name in su_headers_df.columns:
                        buffer['header'][name] = su_headers_df[name].values
                
                # Assign traces
                # Traces shape (chunk, ns). Buffer['data'] shape (chunk, ns)
                # Ensure type matches
                buffer['data'] = traces.astype(data_dtype_str)
                
                # Write
                buffer.tofile(f)
                    
        print(f"Export complete: {output_su_path}")
