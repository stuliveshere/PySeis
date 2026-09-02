"""
Binary SEG-D Writer.
Serializes general headers (GH1, GH2), channel set descriptors (CSD), demux trace headers (TH),
trace extension blocks, and encodes sample arrays into SEG-D format streams.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np

from .decoders import get_encoder

class SEGDWriter:
    """Binary serializer and writer for SEG-D files."""

    def __init__(
        self,
        target: Union[str, Path, io.BytesIO],
        format_code: int = 0x8058,
        revision: str = "2.1",
        manufacturer_code: int = 0x61, # SmartSolo default
        sample_interval_us: int = 2000,
        gather_type: str = "SG"
    ):
        self.target = target
        self.format_code = format_code
        self.revision = revision
        self.manufacturer_code = manufacturer_code
        self.sample_interval_us = sample_interval_us
        self.gather_type = gather_type.upper()

    def _build_gh1(self, num_csd: int = 1) -> bytes:
        """Construct 32-byte General Header 1 (GH1)."""
        gh1 = bytearray(32)
        # Bytes 1-2: File number BCD (default 1)
        gh1[0] = 0x00
        gh1[1] = 0x01
        # Bytes 3-4: Format code BCD (8058 = IEEE float)
        fmt = self.format_code
        if fmt == 0x8058 or fmt == 8058:
            gh1[2] = 0x80
            gh1[3] = 0x58
        elif fmt == 0x8038 or fmt == 8038:
            gh1[2] = 0x80
            gh1[3] = 0x38
        elif fmt == 0x8048 or fmt == 8048:
            gh1[2] = 0x80
            gh1[3] = 0x48
        elif fmt == 0x8036 or fmt == 8036:
            gh1[2] = 0x80
            gh1[3] = 0x36
        else:
            gh1[2] = 0x80
            gh1[3] = 0x58

        # Byte 12: Additional GH blocks (high nibble = 1 for GH2)
        gh1[11] = 0x10
        # Byte 17: Manufacturer code (0x61 = SmartSolo)
        gh1[16] = self.manufacturer_code & 0xFF
        # Byte 23 (idx 22): Base scan interval in 1/16th ms units (e.g. 16 = 1ms, 32 = 2ms)
        gh1[22] = int((self.sample_interval_us / 1000.0) * 16) & 0xFF

        # Byte 28: Scan types per record (1)
        gh1[27] = 0x01
        # Byte 29: Channel sets per scan type
        gh1[28] = num_csd & 0xFF
        return bytes(gh1)

    def _build_gh2(self, num_traces: int) -> bytes:
        """Construct 32-byte General Header 2 (GH2)."""
        gh2 = bytearray(32)
        # Bytes 11-12: SEG-D revision (0x0210 for Rev 2.1)
        gh2[10] = 0x02
        gh2[11] = 0x10
        # Bytes 1-3: Expanded file number
        gh2[0] = 0x00
        gh2[1] = 0x00
        gh2[2] = 0x01
        # Bytes 4-6: Extended trace count
        gh2[3] = (num_traces >> 16) & 0xFF
        gh2[4] = (num_traces >> 8) & 0xFF
        gh2[5] = num_traces & 0xFF
        return bytes(gh2)

    def _build_csd(self, num_channels: int, samples_per_trace: int, sample_interval_us: int) -> bytes:
        """Construct 32-byte Channel Set Descriptor (CSD)."""
        csd = bytearray(32)
        # Byte 1: Scan type (1)
        csd[0] = 0x01
        # Byte 2: Channel set (1)
        csd[1] = 0x01
        # Bytes 5-6 (idx 4-5): Channel set end time from time zero in 2-ms increments
        dt_ms = max(1, sample_interval_us // 1000)
        end_time_ms = samples_per_trace * dt_ms
        end_time_2ms = end_time_ms // 2
        csd[4] = (end_time_2ms >> 8) & 0xFF
        csd[5] = end_time_2ms & 0xFF
        # Bytes 17-18 (idx 16-17): Number of channels in channel set
        csd[16] = (num_channels >> 8) & 0xFF
        csd[17] = num_channels & 0xFF
        # Byte 23: Sample interval (ms fraction)
        csd[22] = max(1, sample_interval_us // 1000)
        return bytes(csd)

    def _build_trace_header(self, trace_num: int, ext_blocks: int = 1) -> bytes:
        """Construct 20-byte Demux Trace Header (TH)."""
        th = bytearray(20)
        # Bytes 1-2: File number
        th[0] = 0x00
        th[1] = 0x01
        # Bytes 3-4: Scan type & channel set (1 & 1)
        th[2] = 0x01
        th[3] = 0x01
        # Bytes 5-6: Trace number in channel set
        th[4] = (trace_num >> 8) & 0xFF
        th[5] = trace_num & 0xFF
        # Byte 10: Extension blocks count
        th[9] = ext_blocks & 0x0F
        return bytes(th)

    def _build_trace_extension(self, trace_num: int, n_samples: int = 0, header_dict: Optional[Dict[str, Any]] = None) -> bytes:
        """Construct 32-byte Trace Extension block carrying coordinates/geometry and samples_per_trace."""
        ext = bytearray(32)
        if header_dict:
            # Encode REC_X (bytes 0-2), REC_Y (bytes 3-5), SOU_X (bytes 10-12), SOU_Y (bytes 15-17)
            rec_x = int(header_dict.get("REC_X", 0)) & 0xFFFFFF
            rec_y = int(header_dict.get("REC_Y", 0)) & 0xFFFFFF
            sou_x = int(header_dict.get("SOU_X", 0)) & 0xFFFFFF
            sou_y = int(header_dict.get("SOU_Y", 0)) & 0xFFFFFF

            ext[0:3] = rec_x.to_bytes(3, byteorder='big')
            ext[3:6] = rec_y.to_bytes(3, byteorder='big')
            ext[10:13] = sou_x.to_bytes(3, byteorder='big')
            ext[15:18] = sou_y.to_bytes(3, byteorder='big')

        if n_samples > 0:
            # Bytes 8-10 (offset 7, length 3): samples_per_trace
            ext[7:10] = n_samples.to_bytes(3, byteorder='big')

        return bytes(ext)

    def write(self, samples: np.ndarray, headers: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Write trace sample array (2D: n_traces x n_samples) and optional header dicts to target.
        """
        if samples.ndim != 2:
            raise ValueError(f"Samples array must be 2D (n_traces, n_samples), got shape {samples.shape}")

        n_traces, n_samples = samples.shape
        encoder = get_encoder(self.format_code)

        # Build Headers
        gh1_b = self._build_gh1(num_csd=1)
        gh2_b = self._build_gh2(num_traces=n_traces)
        csd_b = self._build_csd(num_channels=n_traces, samples_per_trace=n_samples, sample_interval_us=self.sample_interval_us)

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
            # Write General Headers & CSD
            stream.write(gh1_b)
            stream.write(gh2_b)
            stream.write(csd_b)

            # Write Traces
            for i in range(n_traces):
                hdr_dict = headers[i] if (headers and i < len(headers)) else None
                th_b = self._build_trace_header(trace_num=i + 1, ext_blocks=1)
                ext_b = self._build_trace_extension(trace_num=i + 1, n_samples=n_samples, header_dict=hdr_dict)

                sample_data = samples[i, :]
                sample_bytes = encoder(sample_data)

                stream.write(th_b)
                stream.write(ext_b)
                stream.write(sample_bytes)

            stream.flush()
        finally:
            if should_close:
                stream.close()
