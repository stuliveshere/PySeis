import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Union

class FormatParser:
    """
    Parses generic format definitions into efficient numpy dtypes and processing rules.
    """
    def __init__(self, format_dict: Dict[str, Any], endian: str = '<'):
        """
        Args:
            format_dict: Dictionary of field definitions {field_name: {offset, type, size}}.
            endian: '<' or '>'.
        """
        self.format = format_dict
        self.endian = endian
        self.fields = {}
        
        self.block_size = format_dict.get('block_size')
        
        # Filter out metadata
        for k, v in format_dict.items():
            if k not in ['block_label', 'block_offset', 'block_size']:
                self.fields[k] = v

    def build_read_dtype(self, fixed_size: Optional[int] = None) -> np.dtype:
        """
        Build a numpy structured dtype for reading the block.
        Handles standard types directly and complex types via containers.
        
        Args:
            fixed_size: If provided, enforces total itemsize of the dtype (padding added).
                        Defaults to stored block_size if available.
        """
        target_size = fixed_size if fixed_size is not None else self.block_size
        
        dtype_spec = {'names': [], 'formats': [], 'offsets': []}
        
        for name, field in self.fields.items():
            off = field['offset']
            size = field['size']
            ftype = field['type']
            
            # Check for native readability
            # Must be integer byte aligned and standard size
            is_native = (off % 1 == 0) and (size in [1, 2, 4, 8]) and (ftype in ['int', 'uint', 'float'])
            
            if is_native:
                dtype_spec['names'].append(name)
                dtype_spec['offsets'].append(int(off))
                
                fmt_char_map = {
                    'int': {1: 'i1', 2: 'i2', 4: 'i4', 8: 'i8'},
                    'uint': {1: 'u1', 2: 'u2', 4: 'u4', 8: 'u8'},
                    'float': {4: 'f4', 8: 'f8'}
                }
                
                # Handle types not in map (e.g. char?) - basic support only
                if ftype not in fmt_char_map:
                     # Fallback to uint container
                     is_native = False
                elif size not in fmt_char_map[ftype]:
                     is_native = False
                else:
                    endian_prefix = '>' if self.endian == '>' else '<'
                    # single byte integers don't usually care about endian unless specified, 
                    # but numpy handles checks. i1/u1 are endian neutral effectively, but syntax allows it.
                    base_fmt = fmt_char_map[ftype][size]
                    dtype_spec['formats'].append(f'{endian_prefix}{base_fmt}')

            if not is_native:
                # Container Strategy
                # 1. Determine covering bytes
                start_byte = int(np.floor(off))
                end_byte = int(np.ceil(off + size))
                n_bytes = end_byte - start_byte
                
                # 2. Pick smallest container (1, 2, 4, 8 bytes)
                container_size = 1
                for s in [1, 2, 4, 8]:
                    if s >= n_bytes:
                        container_size = s
                        break
                        
                # 3. Add to dtype with special name if not already covered
                # Optimisation: If multiple custom fields map to the same bytes, we only need to read once.
                # However, for simplicity now, we read containers for each field (overlapping read is fine in numpy).
                # We name it _raw_{name} so post-processor can find it.
                
                container_name = f"_raw_{name}"
                dtype_spec['names'].append(container_name)
                dtype_spec['offsets'].append(start_byte)
                dtype_spec['formats'].append(f'u{container_size}') # Always read as uint 

        if target_size is not None:
            dtype_spec['itemsize'] = target_size
            
        # Create dtype. Align=False allows packed structures.
        return np.dtype(dtype_spec) #, align=False? Defaults false usually for structured.

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Post-process the DataFrame to convert _raw fields to actual values.
        """
        # This implementation assumes generic processing logic will be added later.
        # For SU, mostly native reads, so identity.
        # But we could implement the masking/shifting here if we had the rules.
        
        # Example logic:
        # for col in df.columns:
        #    if col.startswith('_raw_'):
        #        real_name = col.replace('_raw_', '')
        #        field = self.fields[real_name]
        #        # do bit magic
        #        # df[real_name] = ...
        #        # df.drop(columns=[col], inplace=True)
        
        return df

    def pack_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reverse process: Pack real values into raw containers or prepare for writing.
        """
        # For writing, we likely need to construct the byte buffer manually or via a write-dtype.
        return df
