"""
Interactive Matplotlib Viewer for scraped SEG-D files in data/segd.
Loads files directly into RAM via BytesIO buffer and provides Next/Previous buttons to step through gathers.
"""

import io
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# Add src to path using absolute resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pyseis.segd import SEGDReader, TraceFillPlan
from pyseis.segd.schema import bcd_digits

# Channel type code to description mapping (SEG-D standard + Sercel extensions)
CHANNEL_TYPE_MAP = {
    0: "Undefined",
    1: "Seis",
    2: "Time counter",
    3: "External data",
    4: "Stacked data",
    5: "Signature/unfiltered",
    6: "Signature/filtered",
    7: "Auxiliary data",
    8: "Vibrator",
    9: "Signature/filtered",  # Sercel uses 9 for signature channels
    0xC: "Aux (SEG-D)",
}


def print_structural_report(reader, filepath):
    """Print a segdsee-style structural report to stdout."""
    buf = reader._buffer
    probe = reader.probe()

    # ── FFID ──
    # GH1 BCD bytes 0-1, then check GH2 for expanded_file_number
    ffid = bcd_digits(bytes(buf[:32]), 0, 2)
    gh2_block = reader.schema.get_block_by_role("general_header_2")
    if gh2_block:
        gh2_fields = gh2_block.parse_fields(bytes(buf[32:64]))
        expanded = gh2_fields.get("expanded_file_number", 0)
        if expanded and expanded > 0 and expanded != 0xFFFFFF:
            ffid = expanded

    # ── SP (source point) — in GH3 for Sercel ──
    sp = "N/A"
    gh3_block = reader.schema.get_block_by_role("general_header_3")
    if gh3_block:
        gh3_fields = gh3_block.parse_fields(bytes(buf[64:96]))
        sp_val = gh3_fields.get("source_point_int", gh3_fields.get("source_point_number", 0))
        if sp_val and sp_val > 0:
            sp = str(sp_val)

    # ── Format code description ──
    fmt = reader.record_info.format_code
    fmt_desc = {
        8058: "8058 - 32 bit IEEE demultiplexed",
        8015: "8015 - 20 bit binary exponent demultiplexed",
        8048: "8048 - 16 bit fixed point demultiplexed",
        8036: "8036 - 24 bit 2's complement demultiplexed",
    }.get(fmt, str(fmt))

    dt_ms = probe['sample_interval_us'] / 1000.0

    # ── Parse Channel Set Descriptors directly ──
    total_gh_bytes = (reader.record_info.gh_blocks_count + 1) * 32
    csd_block = reader.schema.get_block_by_role("channel_set_descriptor")

    channel_sets = []
    for i in range(reader.record_info.num_channel_sets):
        csd_off = total_gh_bytes + (i * 32)
        if csd_off + 32 <= len(buf):
            csd_b = bytes(buf[csd_off:csd_off + 32])
            csd_fields = csd_block.parse_fields(csd_b) if csd_block else {}

            st = csd_fields.get("scan_type_number", csd_b[0])
            csn = csd_fields.get("channel_set_number", csd_b[1])
            ch_count = csd_fields.get("channel_count", 0)
            ch_type_code = csd_fields.get("channel_type", 0)
            ch_type = CHANNEL_TYPE_MAP.get(ch_type_code, f"Unknown ({ch_type_code})")
            start_ms = csd_fields.get("channel_set_start_time", 0) * 2
            end_ms = csd_fields.get("channel_set_end_time", 0) * 2

            if ch_count > 0 and end_ms > 0:
                ns = int((end_ms - start_ms) / dt_ms) + 1
            else:
                ns = "N/A"

            channel_sets.append({
                "st": st, "csn": csn, "type": ch_type,
                "nchan": ch_count, "ns": ns,
                "to": start_ms, "tn": end_ms, "si": dt_ms,
            })

    # ── Trace map summary (actual traces mapped) ──
    cs_trace_counts = {}
    for t in reader._trace_map:
        cs = t['cs_num']
        cs_trace_counts[cs] = cs_trace_counts.get(cs, 0) + 1

    # ── File structure sizes ──
    ext_hdr_size = reader.record_info.extended_header_size
    ext_file_size = reader.record_info.external_header_size
    csd_bytes = reader.record_info.num_channel_sets * 32
    file_size = len(buf)

    expected_header = reader.record_info.first_trace_offset
    total_data_bytes = sum(t['ns'] * t['bytes_per_sample'] for t in reader._trace_map)
    total_trace_hdr_bytes = sum(t['th_size'] for t in reader._trace_map)
    expected_file_size = expected_header + total_data_bytes + total_trace_hdr_bytes

    # ── Print ──
    print(f"\n{'='*80}")
    print("Common Information")
    print(f"{'='*80}")
    print(f"  File Format          : SEG-D {reader.schema.revision}")
    print(f"  File Name            : {filepath.name}")
    print(f"  FFID                 : {ffid}")
    print(f"  SP                   : {sp}")
    print(f"  Data Format          : {fmt_desc}")
    print(f"  Base Sample Interval : {dt_ms:g} ms")
    print(f"  Total traces #       : {probe['num_traces']}")
    print(f"  Samples per trace    : {reader.record_info.samples_per_trace}")
    print(f"  Manufacturer         : {reader.schema.manufacturer}")
    print(f"  Variant              : {reader.schema.variant_id}")

    print(f"\n{'-'*80}")
    print("File Structure")
    print(f"{'-'*80}")
    print(f"  General Headers      : {total_gh_bytes:>8d} bytes  ({reader.record_info.gh_blocks_count + 1} blocks)")
    print(f"  Channel Set Descs    : {csd_bytes:>8d} bytes  ({reader.record_info.num_channel_sets} CSDs)")
    print(f"  Extended Headers     : {ext_hdr_size:>8d} bytes  ({ext_hdr_size // 32} blocks)")
    print(f"  External Headers     : {ext_file_size:>8d} bytes  ({ext_file_size // 32} blocks)")
    print(f"  File Header Total    : {expected_header:>8d} bytes")
    print(f"  Trace Headers Total  : {total_trace_hdr_bytes:>8d} bytes")
    print(f"  Trace Data Total     : {total_data_bytes:>8d} bytes")
    print(f"  Calculated File Size : {expected_file_size:>8d} bytes")
    print(f"  Actual File Size     : {file_size:>8d} bytes")
    delta = file_size - expected_file_size
    match = "MATCH" if delta == 0 else f"MISMATCH ({delta:+d} bytes)"
    print(f"  Size Check           : {match}")

    print(f"\n{'-'*80}")
    print(f"Channel Sets ({reader.record_info.num_channel_sets}):")
    print(f"{'-'*80}")
    print(f"  {'st#':>3s}  {'cs#':>3s}  {'type':<25s} {'#chan':>5s}  {'#samples':>8s}  {'to(ms)':>7s} {'tn(ms)':>7s}  {'si(ms)':>7s}")
    for cs in channel_sets:
        ns_str = f"{cs['ns']}" if isinstance(cs['ns'], int) else cs['ns']
        print(f"  {cs['st']:>3d}  {cs['csn']:>3d}  {cs['type']:<25s} {cs['nchan']:>5d}  {ns_str:>8s}  {cs['to']:>7d} {cs['tn']:>7d}  {cs['si']:>7g}")

    print(f"\n{'-'*80}")
    print(f"Trace Map ({len(reader._trace_map)} traces mapped):")
    print(f"{'-'*80}")
    for cs_num, count in sorted(cs_trace_counts.items()):
        cs_match = [c for c in channel_sets if c['csn'] == cs_num]
        ch_type = cs_match[0]['type'] if cs_match else "?"
        sample_ns = [t['ns'] for t in reader._trace_map if t['cs_num'] == cs_num]
        ns_str = str(sample_ns[0]) if len(set(sample_ns)) == 1 else f"{min(sample_ns)}-{max(sample_ns)}"
        print(f"  CS {cs_num:>3d} ({ch_type:<20s}): {count:>5d} traces x {ns_str} samples")

    print(f"{'='*80}\n")


class SEGDViewer:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir.resolve()
        self.files = sorted([f for f in self.data_dir.iterdir() if f.is_file() and f.suffix.lower() in (".segd", ".sgd", ".raw", ".dat")])
        
        if not self.files:
            print(f"No SEG-D files found in '{self.data_dir}'")
            sys.exit(1)

        self.current_idx = 0
        
        self.fig, self.ax = plt.subplots(figsize=(11, 7))
        plt.subplots_adjust(bottom=0.15)

        # Setup Next and Previous buttons
        ax_prev = plt.axes([0.70, 0.03, 0.12, 0.06])
        ax_next = plt.axes([0.84, 0.03, 0.12, 0.06])

        self.btn_prev = Button(ax_prev, 'Previous')
        self.btn_next = Button(ax_next, 'Next')

        self.btn_prev.on_clicked(self.on_prev)
        self.btn_next.on_clicked(self.on_next)

        self.im = None
        self.load_and_plot_current()

    def load_current_file(self):
        filepath = self.files[self.current_idx]
        
        # Read file directly into RAM buffer
        with open(filepath, "rb") as f:
            ram_buffer = io.BytesIO(f.read())

        with SEGDReader(ram_buffer) as reader:
            probe = reader.probe()
            
            # Print structural report to stdout
            print_structural_report(reader, filepath)

            hdr_bytes_list, samples_arr = reader.read_all_traces()
            
            plan = TraceFillPlan(schema=reader.schema, gather_type=reader.record_info.gather_type)
            headers_df = plan.execute_bulk(hdr_bytes_list)

        return filepath, probe, headers_df, samples_arr

    def load_and_plot_current(self):
        filepath, probe, headers_df, samples_arr = self.load_current_file()
        
        self.ax.clear()
        
        n_traces, n_samples = samples_arr.shape
        dt_ms = probe["sample_interval_us"] / 1000.0

        if n_traces > 0 and n_samples > 0:
            # Normalize display scaling
            vmax = np.percentile(np.abs(samples_arr), 98)
            if vmax == 0:
                vmax = 1.0

            # Plot seismic gather (traces on x-axis, sample time on y-axis)
            self.im = self.ax.imshow(
                samples_arr.T,
                aspect='auto',
                cmap='seismic',
                extent=[1, n_traces, n_samples * dt_ms, 0],
                vmin=-vmax,
                vmax=vmax
            )
            self.ax.set_xlabel("Trace Number", fontsize=11)
            self.ax.set_ylabel("Time (ms)", fontsize=11)
        else:
            self.ax.text(0.5, 0.5, "Empty Trace Data", ha='center', va='center', transform=self.ax.transAxes)

        mfr = probe.get("manufacturer", "unknown").upper()
        g_type = probe.get("gather_type", "SG")
        title_str = f"[{self.current_idx + 1}/{len(self.files)}] {filepath.name}\n"
        title_str += f"Traces: {n_traces} | Samples: {n_samples} | dt: {dt_ms:.2f}ms | Mfr: {mfr} ({g_type})"
        self.ax.set_title(title_str, fontsize=12, fontweight='bold')
        
        self.fig.canvas.draw_idle()

    def on_next(self, event):
        if self.current_idx < len(self.files) - 1:
            self.current_idx += 1
            self.load_and_plot_current()

    def on_prev(self, event):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.load_and_plot_current()

    def show(self):
        plt.show()

if __name__ == "__main__":
    target_dir = Path(__file__).resolve().parent.parent / "data" / "segd"
    viewer = SEGDViewer(target_dir)
    viewer.show()
