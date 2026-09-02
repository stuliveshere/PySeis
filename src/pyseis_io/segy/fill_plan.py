"""
SEG-Y Header Mapping Engine & Scalar Application Engine.
Applies scalco/scalel rules and coordinate reference subtractions across trace headers.
"""

from __future__ import annotations

import struct
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from .schema import SEGYEffectiveSchema

def apply_segy_scalar(values: np.ndarray, scalars: np.ndarray) -> np.ndarray:
    """
    Apply SEG-Y scalar logic.
    Positive scalar: multiplier. Negative scalar: divisor. Zero/NaN: 1.
    """
    out = values.astype(np.float64)
    sc = np.nan_to_num(scalars, nan=0).astype(np.int32)

    multiplier_mask = sc > 0
    divisor_mask = sc < 0

    if np.any(multiplier_mask):
        out[multiplier_mask] *= sc[multiplier_mask].astype(np.float64)

    if np.any(divisor_mask):
        out[divisor_mask] /= np.abs(sc[divisor_mask]).astype(np.float64)

    return out


class SEGYFillPlan:
    """Compiles SEG-Y header mapping rules and executes scalar application."""

    def __init__(
        self,
        schema: SEGYEffectiveSchema,
        mapping_file: Optional[Union[str, Path]] = None,
        custom_mappings: Optional[List[Dict[str, Any]]] = None,
        global_xref: float = 0.0,
        global_yref: float = 0.0
    ):
        self.schema = schema
        self.endian = schema.endian
        self.global_xref = global_xref
        self.global_yref = global_yref

        if mapping_file is None:
            mapping_file = Path(__file__).parent / "header_mapping.yaml"

        with open(mapping_file, "r", encoding="utf-8") as f:
            self.mapping_defs: Dict[str, str] = yaml.safe_load(f) or {}

        if custom_mappings:
            for cust in custom_mappings:
                segy_key = cust.get("segy_key")
                core_key = cust.get("header_name")
                if segy_key and core_key:
                    self.mapping_defs[segy_key] = core_key

    def extract_headers_bulk(self, raw_trace_headers: List[bytes]) -> pd.DataFrame:
        """Extract header fields from a list of 240-byte trace header buffers."""
        if not raw_trace_headers:
            return pd.DataFrame()

        n_traces = len(raw_trace_headers)
        e_char = ">" if self.endian == ">" else "<"
        
        # Build contiguous buffer for vector unpacking
        buf_concat = b"".join(raw_trace_headers)
        trace_dtype = np.dtype([
            ("tracl", f"{e_char}i4"),    # 0
            ("tracr", f"{e_char}i4"),    # 4
            ("fldr", f"{e_char}i4"),     # 8
            ("tracf", f"{e_char}i4"),    # 12
            ("ep", f"{e_char}i4"),       # 16
            ("cdp", f"{e_char}i4"),      # 20
            ("cdpt", f"{e_char}i4"),     # 24
            ("trid", f"{e_char}i2"),     # 28
            ("pad1", "V6"),
            ("offset", f"{e_char}i4"),   # 36
            ("gelev", f"{e_char}i4"),    # 40
            ("selev", f"{e_char}i4"),    # 44
            ("sdepth", f"{e_char}i4"),   # 48
            ("pad2", "V16"),
            ("scalel", f"{e_char}i2"),   # 68
            ("pad3", "V2"),
            ("scalco", f"{e_char}i2"),   # 72
            ("pad4", "V2"),
            ("sx", f"{e_char}i4"),       # 76
            ("sy", f"{e_char}i4"),       # 80
            ("gx", f"{e_char}i4"),       # 84
            ("gy", f"{e_char}i4"),       # 88
            ("counit", f"{e_char}i2"),   # 92
            ("pad5", "V20"),
            ("ns", f"{e_char}u2"),       # 114
            ("dt", f"{e_char}u2"),       # 116
            ("pad6", "V122")
        ])

        struct_arr = np.frombuffer(buf_concat, dtype=trace_dtype, count=n_traces)
        df_raw = pd.DataFrame(struct_arr)

        # Apply scalco to coordinates
        scalco = df_raw["scalco"].values
        for col in ("sx", "sy", "gx", "gy"):
            df_raw[col] = apply_segy_scalar(df_raw[col].values, scalco)

        # Apply scalel to elevations
        scalel = df_raw["scalel"].values
        for col in ("gelev", "selev", "sdepth"):
            df_raw[col] = apply_segy_scalar(df_raw[col].values, scalel)

        # Map to core internal column names
        df_out = pd.DataFrame(index=range(n_traces))
        df_out["tracl"] = np.arange(1, n_traces + 1)

        for segy_key, core_key in self.mapping_defs.items():
            if segy_key in df_raw.columns:
                arr = df_raw[segy_key].values
                if arr.dtype.byteorder not in ('=', '|'):
                    arr = arr.astype(arr.dtype.newbyteorder('='))
                df_out[core_key] = arr

        # Apply global coordinate reference subtractions
        for col in ("source_x", "receiver_x", "sx", "gx", "SOU_X", "REC_X"):
            if col in df_out.columns:
                df_out[col] = df_out[col].astype(np.float64) - self.global_xref

        for col in ("source_y", "receiver_y", "sy", "gy", "SOU_Y", "REC_Y"):
            if col in df_out.columns:
                df_out[col] = df_out[col].astype(np.float64) - self.global_yref

        # Ensure all columns in df_out have native byteorder
        for col in df_out.columns:
            if df_out[col].dtype.byteorder not in ('=', '|'):
                df_out[col] = df_out[col].values.astype(df_out[col].dtype.newbyteorder('='))

        return df_out
