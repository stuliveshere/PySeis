import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import shutil

from pyseis.su import SUImporter, SUExporter
from pyseis.segy import SEGYImporter, SEGYExporter

def main():
    # Setup paths
    base_dir = Path("example_data")
    base_dir.mkdir(exist_ok=True)
    
    su_input = base_dir / "input.su"
    segy_output = base_dir / "output.segy"
    su_restored = base_dir / "restored.su"
    
    print("1. Creating Synthetic SU Data...")
    # leveraging SUExporter to create a valid SU file from scratch via internal format for demo
    # Or just assume input.su exists? The prompt said "reading in a su". 
    # I'll create a dummy one first to make the script self-contained.
    from pyseis.core.writer import InternalFormatWriter
    from pyseis.core.dataset import SeismicData
    import pandas as pd
    
    temp_seis = base_dir / "temp_source.seis"
    if temp_seis.exists(): shutil.rmtree(temp_seis)
    
    n_traces = 50
    n_samples = 200
    
    writer = InternalFormatWriter(temp_seis, overwrite=True)
    writer.write_metadata({"sample_rate": 0.004})
    
    headers = pd.DataFrame({
        'trace_id': np.arange(n_traces),
        'file_number': np.ones(n_traces),
        'offset': np.arange(n_traces) * 25
    })
    writer.write_headers(headers)
    
    # Random data with a synthetic event
    data = np.random.normal(0, 0.1, (n_traces, n_samples)).astype(np.float32)
    # Event
    for i in range(n_traces):
        t = int(50 + i * 0.5)
        if t < n_samples:
             data[i, t:t+5] += 1.0
             
    writer.initialize_data(shape=data.shape, chunks=(10, n_samples), dtype=np.float32)
    writer.write_data_chunk(data, start_trace=0)
    
    sd_source = SeismicData.open(temp_seis)
    SUExporter(sd_source).export(su_input)
    print(f"   Created {su_input}")

    print("\n2. SU -> Internal -> SEGY")
    su_imp = SUImporter(su_input)
    su_imp.scan()
    # Import to temp internal
    su_temp_path = base_dir / "from_su.seis"
    sd1 = su_imp.import_data(su_temp_path)
    print(f"   Imported SU. Summary:\n{sd1.summary()}")
    
    SEGYExporter(sd1).export(segy_output)
    print(f"   Exported to {segy_output}")

    print("\n3. SEGY -> Internal -> SU")
    segy_imp = SEGYImporter(segy_output)
    segy_imp.scan()
    
    segy_temp_path = base_dir / "from_segy.seis"
    sd2 = segy_imp.import_data(segy_temp_path)
    print(f"   Imported SEGY. Summary:\n{sd2.summary()}")
    
    SUExporter(sd2).export(su_restored)
    print(f"   Exported to {su_restored}")

    print("\n4. Comparison & Histogram")
    # Histogram
    data1 = sd1.data[:].compute().flatten()
    data2 = sd2.data[:].compute().flatten()
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    axes[0].hist(data1, bins=10, color='blue', alpha=0.7)
    axes[0].set_title("Original SU Amplitudes")
    axes[0].set_xlabel("Amplitude")
    axes[0].set_ylabel("Count")
    
    axes[1].hist(data2, bins=10, color='green', alpha=0.7)
    axes[1].set_title("Restored SU Amplitudes")
    axes[1].set_xlabel("Amplitude")
    
    plot_path = base_dir / "amplitude_comparison.png"
    plt.tight_layout()
    plt.savefig(plot_path)
    print(f"   Saved histogram to {plot_path}")
    
    # Cleanup
    # shutil.rmtree(temp_seis)
    # shutil.rmtree(su_temp_path)
    # shutil.rmtree(segy_temp_path)

if __name__ == "__main__":
    main()
