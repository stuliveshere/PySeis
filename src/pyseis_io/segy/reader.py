"""
Memory-mapped SEG-Y Reader.
Inspects EBCDIC headers, Binary headers, Extended Textual headers, and Trace payloads.
"""

from __future__ import annotations

import io
import mmap
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from .schema import SEGYSchemaManager, SEGYEffectiveSchema
from .decoders import get_segy_decoder

class SEGYRecordInfo:
    def __init__(
        self,
        revision: str,
        endian: str,
        format_code: int,
        sample_interval_us: int,
        samples_per_trace: int,
        num_traces: int,
        extended_text_headers: int,
        binary_header_dict: Dict[str, Any]
    ):
        self.revision = revision
        self.endian = endian
        self.format_code = format_code
        self.sample_interval_us = sample_interval_us
        self.samples_per_trace = samples_per_trace
        self.num_traces = num_traces
        self.extended_text_headers = extended_text_headers
        self.binary_header_dict = binary_header_dict


class SEGYReader:
    """Memory-mapped binary reader for SEG-Y format files."""

    def __init__(
        self,
        source: Union[str, Path, bytes, io.BytesIO],
        schema: Optional[SEGYEffectiveSchema] = None,
        schema_manager: Optional[SEGYSchemaManager] = None
    ):
        self.source = source
        self.schema_manager = schema_manager or SEGYSchemaManager()
        self._file_handle: Optional[io.BufferedReader] = None
        self._mmap_obj: Optional[mmap.mmap] = None
        self._buffer: memoryview

        if isinstance(source, (str, Path)):
            self.path = Path(source)
            if not self.path.exists():
                raise FileNotFoundError(f"SEG-Y file not found: {source}")
            self._file_handle = open(self.path, "rb")
            self._mmap_obj = mmap.mmap(self._file_handle.fileno(), 0, access=mmap.ACCESS_READ)
            self._buffer = memoryview(self._mmap_obj)
        elif isinstance(source, bytes):
            self.path = None
            self._buffer = memoryview(source)
        elif isinstance(source, io.BytesIO):
            self.path = None
            self._buffer = memoryview(source.getvalue())
        else:
            raise TypeError("Source must be a file path, bytes, or BytesIO object")

        if len(self._buffer) < 3600:
            raise ValueError("Buffer too small to be a valid SEG-Y file (minimum 3600 bytes required)")

        # Auto-detect or load schema
        self.schema = schema or self.schema_manager.auto_detect(bytes(self._buffer[:3600]))
        self.record_info = self._parse_record_info()

    def close(self) -> None:
        if hasattr(self, "_buffer") and self._buffer is not None:
            if hasattr(self._buffer, "release"):
                try:
                    self._buffer.release()
                except Exception:
                    pass
            self._buffer = None
        if self._mmap_obj is not None:
            self._mmap_obj.close()
            self._mmap_obj = None
        if self._file_handle is not None:
            self._file_handle.close()
            self._file_handle = None

    def __enter__(self) -> SEGYReader:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _parse_record_info(self) -> SEGYRecordInfo:
        buf = bytes(self._buffer[:3600])
        endian = self.schema.endian
        e_char = ">" if endian == ">" else "<"

        # Binary Header fields at bytes 3200-3600
        # format at 3224 (2B), hdt at 3216 (2B), hns at 3220 (2B), numhdr at 3504 (2B)
        bin_buf = buf[3200:3600]

        hdt = struct.unpack(f"{e_char}H", bin_buf[16:18])[0]
        hns = struct.unpack(f"{e_char}H", bin_buf[20:22])[0]
        fmt_code = struct.unpack(f"{e_char}h", bin_buf[24:26])[0]
        numhdr = struct.unpack(f"{e_char}h", bin_buf[304:306])[0] if len(bin_buf) >= 306 else 0
        if numhdr < 0:
            numhdr = 0

        if fmt_code <= 0:
            fmt_code = 5 # Default IEEE Float

        # Fallback for hns/hdt if 0 in binary header (check first trace header at offset 3600 + numhdr*3200)
        data_start = 3600 + (numhdr * 3200)
        if (hns == 0 or hdt == 0) and len(self._buffer) >= data_start + 240:
            th_buf = bytes(self._buffer[data_start:data_start + 240])
            if hns == 0:
                hns = struct.unpack(f"{e_char}H", th_buf[114:116])[0]
            if hdt == 0:
                hdt = struct.unpack(f"{e_char}H", th_buf[116:118])[0]

        if hns == 0:
            hns = 1000 # default fallback
        if hdt == 0:
            hdt = 2000 # default 2ms (2000 µs)

        # Sample size
        bytes_per_sample = 4
        if fmt_code == 3:
            bytes_per_sample = 2
        elif fmt_code == 8:
            bytes_per_sample = 1
        elif fmt_code == 16:
            bytes_per_sample = 8

        trace_stride = 240 + (hns * bytes_per_sample)
        data_len = len(self._buffer) - data_start
        n_traces = max(0, data_len // trace_stride)

        bin_dict = {
            "hdt": hdt,
            "hns": hns,
            "format": fmt_code,
            "numhdr": numhdr,
            "segyrev": 256 if self.schema.revision == "rev1" else (512 if self.schema.revision == "rev2" else 0)
        }

        return SEGYRecordInfo(
            revision=self.schema.revision,
            endian=endian,
            format_code=fmt_code,
            sample_interval_us=hdt,
            samples_per_trace=hns,
            num_traces=n_traces,
            extended_text_headers=numhdr,
            binary_header_dict=bin_dict
        )

    def probe(self) -> Dict[str, Any]:
        """Fast metadata probe returning dataset summary."""
        return {
            "revision": self.record_info.revision,
            "endian": self.record_info.endian,
            "format_code": self.record_info.format_code,
            "sample_interval_us": self.record_info.sample_interval_us,
            "samples_per_trace": self.record_info.samples_per_trace,
            "num_traces": self.record_info.num_traces,
            "extended_text_headers": self.record_info.extended_text_headers
        }

    def read_trace(self, trace_idx: int) -> Tuple[bytes, np.ndarray]:
        """Read header bytes and sample array for a specific trace index."""
        if trace_idx < 0 or trace_idx >= self.record_info.num_traces:
            raise IndexError(f"Trace index {trace_idx} out of bounds (0-{self.record_info.num_traces - 1})")

        data_start = 3600 + (self.record_info.extended_text_headers * 3200)

        bytes_per_sample = 4
        if self.record_info.format_code == 3:
            bytes_per_sample = 2
        elif self.record_info.format_code == 8:
            bytes_per_sample = 1
        elif self.record_info.format_code == 16:
            bytes_per_sample = 8

        stride = 240 + (self.record_info.samples_per_trace * bytes_per_sample)
        trace_offset = data_start + (trace_idx * stride)

        hdr_bytes = bytes(self._buffer[trace_offset:trace_offset + 240])
        sample_bytes = bytes(self._buffer[trace_offset + 240:trace_offset + stride])

        decoder = get_segy_decoder(self.record_info.format_code)
        samples = decoder(sample_bytes, self.record_info.samples_per_trace, self.record_info.endian)

        return hdr_bytes, samples

    def read_all_traces(self) -> Tuple[List[bytes], np.ndarray]:
        """Read all trace headers and trace sample arrays in bulk."""
        n_traces = self.record_info.num_traces
        ns = self.record_info.samples_per_trace

        hdr_list = []
        samples_arr = np.zeros((n_traces, ns), dtype=np.float32)

        for i in range(n_traces):
            hdr_b, samples = self.read_trace(i)
            hdr_list.append(hdr_b)
            samples_arr[i, :len(samples)] = samples

        return hdr_list, samples_arr
