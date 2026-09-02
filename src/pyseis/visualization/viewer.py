
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from pathlib import Path

from pyseis.core.dataset import SeismicData

class SeismicViewer:
    """
    A simple matplotlib-based viewer for SeismicData datasets.
    """
    def __init__(self, dataset_path, group_by='source_id', show=True):
        """
        Initialize the viewer.
        
        Args:
            dataset_path (str): Path to the .seis dataset (Zarr/Parquet).
            group_by (str): Header key to group constant gathers by (e.g. 'fldr', 'source_id', 'cdp'). Default 'source_id'.
            show (bool): Whether to call plt.show() immediately (blocking). Default True.
        """
        self.dataset_path = Path(dataset_path)
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
            
        print(f"Loading dataset: {dataset_path}...")
        self.sd = SeismicData.open(self.dataset_path)
        
        # Group headers
        print(f"Grouping traces by '{group_by}'...")
        if group_by not in self.sd.headers.columns:
            avail = list(self.sd.headers.columns)
            raise ValueError(f"Header '{group_by}' not found. Available headers: {avail}")
            
        # Grouping
        # We need to map group keys to indices.
        # A simple groupby on dataframe is efficient enough for headers < 1M rows.
        self.groups = self.sd.headers.groupby(group_by).groups
        # self.groups is a dict {key: index_array}
        
        self.keys = sorted(list(self.groups.keys()))
        if not self.keys:
            raise ValueError("No gathers found.")
            
        print(f"Found {len(self.keys)} gathers.")
        
        self.current_idx = 0
        self.group_by = group_by
        
        # Setup Figure
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.im = None
        
        # Add Widgets
        # [left, bottom, width, height]
        ax_prev = plt.axes([0.7, 0.01, 0.1, 0.05])
        ax_next = plt.axes([0.81, 0.01, 0.1, 0.05])
        self.bprev = Button(ax_prev, 'Previous')
        self.bnext = Button(ax_next, 'Next')
        self.bprev.on_clicked(self.prev)
        self.bnext.on_clicked(self.next)
        
        self.update()
        
        if show:
            # Connect close event to cleanup resources
            self.fig.canvas.mpl_connect('close_event', self.on_close)
            plt.show()

    def on_close(self, event):
        """Handle window close event."""
        self.close()

    def close(self):
        """Explicitly close resources."""
        if hasattr(self, 'sd') and self.sd:
            print("Closing SeismicData resources...")
            self.sd.close()
            self.sd = None


    def update(self):
        """Update display for current gather index."""
        key = self.keys[self.current_idx]
        indices = self.groups[key]
        
        # Read Data
        # indices might not be sorted or contiguous in file, but dask handles list.
        # Ideally, they are chunk-aligned.
        # To display as image: (Time, Trace), so transpose typical (Trace, Time)
        
        # Optimization: indices is a pandas Index or array.
        # self.sd.data is dask array.
        # Using dask slicing: sd.data[list(indices)]
        
        # Grab data as numpy
        # Note: indices can be Int64Index.
        trace_data = self.sd.data[indices].compute()
        
        # Transpose for plotting: (Time on Y, Traces on X)
        img_data = trace_data.T 
        
        # Determine robust scaling range (e.g. 98th percentile)
        # Doing this per gather might be jittery. but good for contrast.
        # Or fixed? Let's do simple symmetric scaling based on max abs
        vm = np.percentile(np.abs(img_data), 98) 
        if vm == 0: vm = 1.0
        
        self.ax.clear()
        # extent=[left, right, bottom, top]
        # x-axis: 0 to N traces
        # y-axis: 0 to Time (ns * dt)
        
        # Get sample rate and ns
        # self.sd.sample_rate is in microseconds
        ns = img_data.shape[0]
        sr = getattr(self.sd, 'sample_rate', 0.004)
        # Heuristic: if > 1, assume micros (legacy/default), else seconds
        if sr > 1:
            dt = sr / 1_000_000.0
        else:
            dt = sr
            
        max_time = ns * dt
        
        self.ax.imshow(img_data, cmap='seismic', aspect='auto', vmin=-vm, vmax=vm,
                       extent=[0, img_data.shape[1], max_time, 0])
                       
        self.ax.set_title(f"Gather: {self.group_by}={key} ({self.current_idx + 1}/{len(self.keys)})")
        self.ax.set_xlabel("Trace Index (within gather)")
        self.ax.set_ylabel("Time (s)")
        
        self.fig.canvas.draw()

    def next(self, event):
        if self.current_idx < len(self.keys) - 1:
            self.current_idx += 1
            self.update()

    def prev(self, event):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.update()

def main():
    parser = argparse.ArgumentParser(description="PySeis-IO Dataset Viewer")
    parser.add_argument("path", help="Path to .seis dataset directory")
    parser.add_argument("--group-by", "-g", default="fldr", help="Header key to group by (default: fldr)")
    
    args = parser.parse_args()
    
    try:
        SeismicViewer(args.path, group_by=args.group_by)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
