
import sys
import argparse
from pathlib import Path
import tempfile
import shutil

# Ensure pyseis is in path if running from source root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyseis.su.importer import SUImporter
from pyseis.visualization.viewer import SeismicViewer

def main():
    parser = argparse.ArgumentParser(description="Visualize an SU file using PySeis-IO")
    parser.add_argument("su_file", help="Path to input .su file")
    
    args = parser.parse_args()
    
    su_path = Path(args.su_file)
    if not su_path.exists():
        print(f"Error: File not found: {su_path}")
        sys.exit(1)
        
    print(f"Processing SU file: {su_path}")
    
    # Create a temporary directory for the converted .seis dataset
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        seis_path = temp_dir_path / "converted.seis"
        
        print("Scanning SU file...")
        importer = SUImporter(su_path)
        df = importer.scan()
        print(f"Scanned {len(df)} traces.")
        
        print(f"Converting to internal format at {seis_path}...")
        sd = importer.import_data(seis_path)
        
        print("Launching viewer...")
        print("Note: Dataset will be deleted when viewer closes.")
        
        try:
            # sd is already opened
            # from pyseis.core.dataset import SeismicData # No longer needed here
            print(sd.summary())
            sd.close() # Close to release for viewer (though viewer re-opens it)
            
            SeismicViewer(seis_path)
        except Exception as e:
            print(f"Viewer Error: {e}")

if __name__ == "__main__":
    main()
