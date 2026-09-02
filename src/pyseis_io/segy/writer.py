"""
Binary SEG-Y Serializer and Writer.
Constructs 3200-byte EBCDIC textual headers, 400-byte binary headers, 240-byte trace headers,
and encodes sample arrays to SEG-Y binary streams.
"""

from __future__ import annotations

import io
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np

from .decoders import get_segy_encoder

def _safe_int32(val: Any) -> int:
    try:
        v = float(val)
        if np.isnan(v) or np.isinf(v):
            return 0
        return int(np.clip(v, -2147483648, 2147483647))
    except Exception:
        return 0

def _safe_int16(val: Any) -> int:
    try:
        v = float(val)
        if np.isnan(v) or np.isinf(v):
            return 0
        return int(np.clip(v, -32768, 32767))
    except Exception:
        return 0

class SEGYWriter:
    """Binary serializer and writer for SEG-Y files."""

    def __init__(
        self,
        target: Union[str, Path, io.BytesIO],
        format_code: int = 5, # IEEE float
        revision: str = "rev1",
        sample_interval_us: int = 2000,
        endian: str = ">"
    ):
        self.target = target
        self.format_code = format_code
        self.revision = revision
        self.sample_interval_us = sample_interval_us
        self.endian = endian

    def _build_ebcdic_header(self, text_lines: Optional[List[str]] = None) -> bytes:
        """Construct 3200-byte EBCDIC header."""
        lines = []
        if text_lines:
            lines = [f"C{idx+1:02d} {line[:76]}" for idx, line in enumerate(text_lines[:40])]
        
        while len(lines) < 40:
            idx = len(lines) + 1
            if idx == 1:
                lines.append(f"C{idx:02d} SEG-Y Output from pyseis-io")
            else:
                lines.append(f"C{idx:02d}")

        formatted_text = "".join(line.ljust(80) for line in lines)
        formatted_text = formatted_text[:3200].ljust(3200)

        try:
            return formatted_text.encode("cp500")
        except LookupError:
            return formatted_text.encode("ascii")

    def _build_binary_header(self, num_samples: int, num_traces: int = 0) -> bytes:
        """Construct 400-byte Binary Header."""
        bin_hdr = bytearray(400)
        e_char = ">" if self.endian == ">" else "<"

        struct.pack_into(f"{e_char}H", bin_hdr, 16, _safe_int16(self.sample_interval_us))
        struct.pack_into(f"{e_char}H", bin_hdr, 18, _safe_int16(self.sample_interval_us))
        struct.pack_into(f"{e_char}H", bin_hdr, 20, _safe_int16(num_samples))
        struct.pack_into(f"{e_char}H", bin_hdr, 22, _safe_int16(num_samples))
        struct.pack_into(f"{e_char}h", bin_hdr, 24, _safe_int16(self.format_code))
        struct.pack_into(f"{e_char}h", bin_hdr, 54, 1)
        rev_val = 0x0100 if self.revision == "rev1" else (0x0200 if self.revision == "rev2" else 0)
        struct.pack_into(f"{e_char}h", bin_hdr, 300, rev_val)
        struct.pack_into(f"{e_char}h", bin_hdr, 302, 1)
        struct.pack_into(f"{e_char}h", bin_hdr, 304, 0)

        return bytes(bin_hdr)

    def _build_trace_header(self, trace_idx: int, num_samples: int, header_dict: Optional[Dict[str, Any]] = None) -> bytes:
        """Construct 240-byte Trace Header."""
        th = bytearray(240)
        e_char = ">" if self.endian == ">" else "<"
        h = header_dict or {}

        tracl = _safe_int32(h.get("tracl", h.get("trace_number", trace_idx + 1)))
        fldr = _safe_int32(h.get("fldr", h.get("file_number", h.get("shot_number", 1))))
        tracf = _safe_int32(h.get("tracf", h.get("channel_number", trace_idx + 1)))
        cdp = _safe_int32(h.get("cdp", h.get("cdp_number", 1)))

        sx = _safe_int32(h.get("sx", h.get("source_x", h.get("SOU_X", 0))))
        sy = _safe_int32(h.get("sy", h.get("source_y", h.get("SOU_Y", 0))))
        gx = _safe_int32(h.get("gx", h.get("receiver_x", h.get("REC_X", 0))))
        gy = _safe_int32(h.get("gy", h.get("receiver_y", h.get("REC_Y", 0))))

        scalco = _safe_int16(h.get("scalco", h.get("coordinate_scalar", 1)))
        scalel = _safe_int16(h.get("scalel", h.get("elevation_scalar", 1)))

        raw_sx = h.get("sx", h.get("source_x", h.get("SOU_X", 0)))
        raw_sy = h.get("sy", h.get("source_y", h.get("SOU_Y", 0)))
        raw_gx = h.get("gx", h.get("receiver_x", h.get("REC_X", 0)))
        raw_gy = h.get("gy", h.get("receiver_y", h.get("REC_Y", 0)))

        if scalco < 0:
            mult_c = float(abs(scalco))
            sx = _safe_int32(float(raw_sx) * mult_c)
            sy = _safe_int32(float(raw_sy) * mult_c)
            gx = _safe_int32(float(raw_gx) * mult_c)
            gy = _safe_int32(float(raw_gy) * mult_c)
        elif scalco > 0:
            div_c = float(scalco)
            sx = _safe_int32(float(raw_sx) / div_c)
            sy = _safe_int32(float(raw_sy) / div_c)
            gx = _safe_int32(float(raw_gx) / div_c)
            gy = _safe_int32(float(raw_gy) / div_c)
        else:
            sx = _safe_int32(raw_sx)
            sy = _safe_int32(raw_sy)
            gx = _safe_int32(raw_gx)
            gy = _safe_int32(raw_gy)

        raw_gelev = h.get("gelev", h.get("receiver_elevation", 0))
        raw_selev = h.get("selev", h.get("source_elevation", 0))
        raw_sdepth = h.get("sdepth", h.get("source_depth", 0))

        if scalel < 0:
            mult_e = float(abs(scalel))
            gelev = _safe_int32(float(raw_gelev) * mult_e)
            selev = _safe_int32(float(raw_selev) * mult_e)
            sdepth = _safe_int32(float(raw_sdepth) * mult_e)
        elif scalel > 0:
            div_e = float(scalel)
            gelev = _safe_int32(float(raw_gelev) / div_e)
            selev = _safe_int32(float(raw_selev) / div_e)
            sdepth = _safe_int32(float(raw_sdepth) / div_e)
        else:
            gelev = _safe_int32(raw_gelev)
            selev = _safe_int32(raw_selev)
            sdepth = _safe_int32(raw_sdepth)

        # Pack trace fields
        struct.pack_into(f"{e_char}i", th, 0, tracl)     # tracl (0-3)
        struct.pack_into(f"{e_char}i", th, 4, tracl)     # tracr (4-7)
        struct.pack_into(f"{e_char}i", th, 8, fldr)      # fldr (8-11)
        struct.pack_into(f"{e_char}i", th, 12, tracf)    # tracf (12-15)
        struct.pack_into(f"{e_char}i", th, 20, cdp)      # cdp (20-23)
        struct.pack_into(f"{e_char}h", th, 28, 1)        # trid (28-29)

        struct.pack_into(f"{e_char}i", th, 40, gelev)    # gelev (40-43)
        struct.pack_into(f"{e_char}i", th, 44, selev)    # selev (44-47)
        struct.pack_into(f"{e_char}i", th, 48, sdepth)   # sdepth (48-51)

        struct.pack_into(f"{e_char}h", th, 68, scalel)   # scalel (68-69)
        struct.pack_into(f"{e_char}h", th, 72, scalco)   # scalco (72-73)

        struct.pack_into(f"{e_char}i", th, 76, sx)       # sx (76-79)
        struct.pack_into(f"{e_char}i", th, 80, sy)       # sy (80-83)
        struct.pack_into(f"{e_char}i", th, 84, gx)       # gx (84-87)
        struct.pack_into(f"{e_char}i", th, 88, gy)       # gy (88-91)

        struct.pack_into(f"{e_char}H", th, 114, _safe_int16(num_samples)) # ns (114-115)
        struct.pack_into(f"{e_char}H", th, 116, _safe_int16(self.sample_interval_us)) # dt (116-117)

        return bytes(th)

    def write(self, samples: np.ndarray, headers: Optional[List[Dict[str, Any]]] = None) -> None:
        """Write trace sample array (2D: n_traces x n_samples) and header dicts to target."""
        if samples.ndim != 2:
            raise ValueError(f"Samples array must be 2D (n_traces, n_samples), got shape {samples.shape}")

        n_traces, n_samples = samples.shape
        encoder = get_segy_encoder(self.format_code)

        ebcdic_b = self._build_ebcdic_header()
        binary_b = self._build_binary_header(num_samples=n_samples, num_traces=n_traces)

        stream: io.BufferedIOBase
        should_close = False

        if isinstance(self.target, (str, Path)):
            stream = open(self.target, "wb")
            should_close = True
        elif isinstance(self.target, io.BytesIO):
            stream = self.target
        else:
            raise TypeError("Target must be a file path or BytesIO stream")

        try:
            stream.write(ebcdic_b)
            stream.write(binary_b)

            for i in range(n_traces):
                hdr_dict = headers[i] if (headers and i < len(headers)) else None
                th_b = self._build_trace_header(trace_idx=i, num_samples=n_samples, header_dict=hdr_dict)
                sample_bytes = encoder(samples[i, :], self.endian)

                stream.write(th_b)
                stream.write(sample_bytes)

            stream.flush()
        finally:
            if should_close:
                stream.close()
