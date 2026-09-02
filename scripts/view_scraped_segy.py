"""
Interactive Matplotlib Viewer for scraped SEG-Y files in data/segy.
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

from pyseis.segy import SEGYReader, SEGYFillPlan

class SEGYViewer:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir.resolve()
        self.files = sorted([f for f in self.data_dir.iterdir() if f.is_file() and f.suffix.lower() in (".segy", ".sgy")])
        
        if not self.files:
            print(f"No SEG-Y files found in '{self.data_dir}'")
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

        with SEGYReader(ram_buffer) as reader:
            probe = reader.probe()
            hdr_bytes_list, samples_arr = reader.read_all_traces()
            
            plan = SEGYFillPlan(schema=reader.schema)
            headers_df = plan.extract_headers_bulk(hdr_bytes_list)

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

        title_str = f"[{self.current_idx + 1}/{len(self.files)}] {filepath.name}\n"
        title_str += f"Traces: {n_traces} | Samples: {n_samples} | dt: {dt_ms:.2f}ms | Rev: {probe.get('revision', 'rev0')}"
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
    target_dir = Path(__file__).resolve().parent.parent / "data" / "segy"
    viewer = SEGYViewer(target_dir)
    viewer.show()
