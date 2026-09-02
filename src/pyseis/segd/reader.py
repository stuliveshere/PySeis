"""
Memory-mapped SEG-D Reader.
Inspects binary record layouts, channel set descriptors, demux trace headers,
and trace sample payloads.
"""

from __future__ import annotations

import io
import mmap
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from .schema import SchemaManager, EffectiveSchema, bcd_digits, bcd_nibble, bcd_to_hex
from .decoders import get_decoder

class SEGDRecordInfo:
    """Parsed metadata for a single SEG-D record file."""
    def __init__(
        self,
        revision: str,
        manufacturer: str,
        format_code: int,
        sample_interval_us: int,
        samples_per_trace: int,
        num_channel_sets: int,
        num_traces: int,
        trace_headers_size: int,
        extended_header_size: int,
        external_header_size: int,
        gh_blocks_count: int,
        first_trace_offset: int,
        gather_type: str = "SG"
    ):
        self.revision = revision
        self.manufacturer = manufacturer
        self.format_code = format_code
        self.sample_interval_us = sample_interval_us
        self.samples_per_trace = samples_per_trace
        self.num_channel_sets = num_channel_sets
        self.num_traces = num_traces
        self.trace_headers_size = trace_headers_size
        self.extended_header_size = extended_header_size
        self.external_header_size = external_header_size
        self.gh_blocks_count = gh_blocks_count
        self.first_trace_offset = first_trace_offset
        self.gather_type = gather_type


class SEGDReader:
    """Memory-mapped binary reader for SEG-D format files."""

    def __init__(self, source: Union[str, Path, bytes, io.BytesIO], schema: Optional[EffectiveSchema] = None, schema_manager: Optional[SchemaManager] = None):
        self.source = source
        self.schema_manager = schema_manager or SchemaManager()
        self._file_handle: Optional[io.BufferedReader] = None
        self._mmap_obj: Optional[mmap.mmap] = None
        self._buffer: memoryview
        self._trace_map: List[Dict[str, Any]] = []

        if isinstance(source, (str, Path)):
            self.path = Path(source)
            if not self.path.exists():
                raise FileNotFoundError(f"SEG-D file not found: {source}")
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

        if len(self._buffer) < 32:
            raise ValueError("Buffer too small to be a valid SEG-D file")

        # Auto-detect or load schema
        self.schema = schema or self.schema_manager.auto_detect_schema(bytes(self._buffer[:64]))
        self.record_info = self._parse_record_info()
        self._build_trace_map()

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

    def __enter__(self) -> SEGDReader:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _parse_record_info(self) -> SEGDRecordInfo:
        buf = bytes(self._buffer[:64])
        
        # 1. Parse fields using YAML Schema blocks if available
        gh1_block = self.schema.get_block_by_role("general_header_1")
        gh1_fields = gh1_block.parse_fields(buf[:32]) if gh1_block else {}

        fmt_code = gh1_fields.get("format_code", bcd_digits(buf, 2, 2))
        if not fmt_code:
            fmt_code = 0x8058

        gh_blocks = gh1_fields.get("additional_gh_blocks", (buf[11] >> 4) & 0x0F)
        if not gh_blocks:
            gh_blocks = 1
        total_gh_bytes = (gh_blocks + 1) * 32

        num_csd = gh1_fields.get("channel_sets_per_scan", buf[28] if len(buf) > 28 else 1)
        if num_csd == 0xFF or num_csd == 255 or num_csd == 0:
            num_csd = buf[28] if len(buf) > 28 else 1
        csd_total_bytes = num_csd * 32

        ext_hdr_blocks = gh1_fields.get("extended_header_blocks", bcd_digits(buf, 30, 1))
        ext_file_blocks = gh1_fields.get("external_header_blocks", bcd_digits(buf, 31, 1))

        first_trace_offset = total_gh_bytes + csd_total_bytes + (ext_hdr_blocks * 32) + (ext_file_blocks * 32)

        # Sample rate / interval
        sample_interval = 2000 # default 2000 us (2ms)
        base_interval_16ths = gh1_fields.get("base_scan_interval", buf[22])
        if base_interval_16ths > 0:
            sample_interval = int((base_interval_16ths / 16.0) * 1000)

        # Gather type detection
        gather_type = "SG"
        gt_nibble = buf[22] & 0x0F
        if gt_nibble == 1:
            gather_type = "RG"
        elif gt_nibble == 2:
            gather_type = "CG"

        # Determine global samples_per_trace from extended or external headers if available
        global_samples_per_trace = 0
        offset = total_gh_bytes + csd_total_bytes
        
        ext_hdr_size = ext_hdr_blocks * 32
        if ext_hdr_size > 0:
            ext_buf = self._buffer[offset:offset+ext_hdr_size]
            ext_block = self.schema.get_block_by_role("file_extended_header")
            if ext_block:
                ext_fields = ext_block.parse_fields(ext_buf)
                if "samples_per_trace" in ext_fields:
                    global_samples_per_trace = ext_fields["samples_per_trace"]
            offset += ext_hdr_size
            
        external_hdr_size = ext_file_blocks * 32
        if external_hdr_size > 0 and global_samples_per_trace == 0:
            external_buf = self._buffer[offset:offset+external_hdr_size]
            external_block = self.schema.get_block_by_role("external_header")
            if external_block:
                external_fields = external_block.parse_fields(external_buf)
                if "samples_per_trace" in external_fields:
                    global_samples_per_trace = external_fields["samples_per_trace"]

        return SEGDRecordInfo(
            revision=self.schema.revision,
            manufacturer=self.schema.manufacturer,
            format_code=fmt_code,
            sample_interval_us=sample_interval,
            samples_per_trace=global_samples_per_trace,
            num_channel_sets=num_csd,
            num_traces=0,
            trace_headers_size=32,
            extended_header_size=ext_hdr_blocks * 32,
            external_header_size=ext_file_blocks * 32,
            gh_blocks_count=self.record_info.gh_blocks_count if hasattr(self, 'record_info') else gh_blocks,
            first_trace_offset=first_trace_offset,
            gather_type=gather_type
        )

    def _build_trace_map(self) -> None:
        """Sequentially scan buffer to map every trace record's offset, header size, and sample count."""
        buf_len = len(self._buffer)
        curr_off = self.record_info.first_trace_offset

        # Extended record length in ms from GH2 (bytes 15-17: index 14-16 in GH2 block at offset 32)
        ext_rec_len_ms = 0
        if buf_len >= 64:
            gh2_buf = bytes(self._buffer[32:64])
            ext_rec_len_ms = (gh2_buf[14] << 16) | (gh2_buf[15] << 8) | gh2_buf[16]

        dt_ms = max(1, self.record_info.sample_interval_us // 1000)

        # Parse Channel Set Descriptors
        total_gh_bytes = (self.record_info.gh_blocks_count + 1) * 32
        csd_info: Dict[int, Dict[str, Any]] = {}
        csd_block = self.schema.get_block_by_role("channel_set_descriptor")

        for i in range(self.record_info.num_channel_sets):
            csd_off = total_gh_bytes + (i * 32)
            if csd_off + 32 <= buf_len:
                csd_b = bytes(self._buffer[csd_off:csd_off + 32])
                cs_num = csd_b[1]
                
                # Parse CSD via YAML schema
                csd_fields = csd_block.parse_fields(csd_b) if csd_block else {}
                
                # Derive sample count from channel set end time
                end_time = csd_fields.get("channel_set_end_time", 0)
                if end_time > 0:
                    ns_csd = ((end_time * 2) // dt_ms) + 1
                else:
                    ns_csd = (ext_rec_len_ms // dt_ms) + 1 if ext_rec_len_ms > 0 else 1000

                fmt_csd = csd_fields.get("channel_type_format", csd_fields.get("format_code", 0))
                # Some variants put format in CSD byte 7-8, others rely on GH1
                if fmt_csd == 0:
                    fmt_csd = (csd_b[6] << 8) | csd_b[7]
                
                csd_info[cs_num] = {
                    "ns": ns_csd if ns_csd > 0 else 1000,
                    "fmt": fmt_csd if fmt_csd != 0 else self.record_info.format_code
                }

        self._trace_map = []
        default_fmt = self.record_info.format_code

        # SEG-D demux trace header is 20 bytes; each trace header extension is 32 bytes.
        DMUX_SIZE = 20
        TH_EXT_SIZE = 32

        while curr_off + DMUX_SIZE <= buf_len:
            th = bytes(self._buffer[curr_off:curr_off + DMUX_SIZE])
            if not any(x != 0 for x in th) or th[0] == 0xFF:
                curr_off += DMUX_SIZE
                continue

            cs_num = th[3]
            t_num = bcd_digits(th, 4, 2)
            th_ext = th[9] & 0x0F
            th_size = DMUX_SIZE + (th_ext * TH_EXT_SIZE)

            info = csd_info.get(cs_num, {"ns": 0, "fmt": default_fmt})
            fmt = info["fmt"] if info["fmt"] != 0 else default_fmt
            
            # Extract samples_per_trace from trace extension block 1 if available
            ns = 0
            if th_ext > 0:
                ext_block = self.schema.get_block_by_role("receiver_geometry")
                if ext_block:
                    th1_ext_off = curr_off + DMUX_SIZE
                    th1_ext = bytes(self._buffer[th1_ext_off : th1_ext_off + TH_EXT_SIZE])
                    ext_fields = ext_block.parse_fields(th1_ext)
                    ns = ext_fields.get("samples_per_trace", 0)

            # Fallback to global samples_per_trace
            if ns == 0:
                ns = self.record_info.samples_per_trace

            # Fallback to CSD time window
            if ns == 0:
                ns = info["ns"] if info["ns"] > 0 else 1000

            bytes_per_sample = 4
            if fmt in (0x8048, 8048):
                bytes_per_sample = 2
            elif fmt in (0x8036, 8036):
                bytes_per_sample = 3

            self._trace_map.append({
                "offset": curr_off,
                "th_size": th_size,
                "cs_num": cs_num,
                "t_num": t_num,
                "ns": ns,
                "fmt": fmt,
                "bytes_per_sample": bytes_per_sample
            })

            curr_off += th_size + (ns * bytes_per_sample)

        self.record_info.num_traces = len(self._trace_map)
        if self._trace_map:
            # Set representative samples per trace for seismic channels
            seis_t = next((t for t in self._trace_map if t["cs_num"] != 1), self._trace_map[0])
            self.record_info.samples_per_trace = seis_t["ns"]

    def probe(self) -> Dict[str, Any]:
        """Fast metadata probe returning dataset summary without reading trace arrays."""
        return {
            "revision": self.record_info.revision,
            "manufacturer": self.record_info.manufacturer,
            "format_code": self.record_info.format_code,
            "sample_interval_us": self.record_info.sample_interval_us,
            "samples_per_trace": self.record_info.samples_per_trace,
            "num_traces": self.record_info.num_traces,
            "num_channel_sets": self.record_info.num_channel_sets,
            "gather_type": self.record_info.gather_type,
            "variant_id": self.schema.variant_id
        }

    def read_trace(self, trace_idx: int) -> Tuple[bytes, np.ndarray]:
        """Read header bytes and sample payload for a specific trace index."""
        if trace_idx < 0 or trace_idx >= len(self._trace_map):
            raise IndexError(f"Trace index {trace_idx} out of bounds (0-{len(self._trace_map) - 1})")

        t_info = self._trace_map[trace_idx]
        offset = t_info["offset"]
        th_size = t_info["th_size"]
        ns = t_info["ns"]
        fmt = t_info["fmt"]
        bytes_per_sample = t_info["bytes_per_sample"]

        hdr_bytes = bytes(self._buffer[offset:offset + th_size])
        data_offset = offset + th_size
        raw_data = bytes(self._buffer[data_offset:data_offset + (ns * bytes_per_sample)])

        decoder = get_decoder(fmt)
        samples = decoder(raw_data, ns)

        return hdr_bytes, samples

    def read_all_traces(self, channel_set: Optional[int] = None) -> Tuple[List[bytes], np.ndarray]:
        """Read trace headers and trace sample arrays in bulk, optionally filtered by channel set."""
        if channel_set is not None:
            target_indices = [i for i, t in enumerate(self._trace_map) if t["cs_num"] == channel_set]
        else:
            # Default to seismic channels (excluding aux channel set 1 if multiple exist)
            seis_indices = [i for i, t in enumerate(self._trace_map) if t["cs_num"] != 1]
            target_indices = seis_indices if seis_indices else list(range(len(self._trace_map)))

        if not target_indices:
            target_indices = list(range(len(self._trace_map)))

        n_traces = len(target_indices)
        ns = self._trace_map[target_indices[0]]["ns"] if target_indices else 1000

        hdr_list = []
        samples_arr = np.zeros((n_traces, ns), dtype=np.float32)

        for out_idx, src_idx in enumerate(target_indices):
            hdr_b, samples = self.read_trace(src_idx)
            hdr_list.append(hdr_b)
            n_copy = min(len(samples), ns)
            samples_arr[out_idx, :n_copy] = samples[:n_copy]

        # Clean NaN/Inf values if present
        samples_arr = np.nan_to_num(samples_arr)

        return hdr_list, samples_arr
