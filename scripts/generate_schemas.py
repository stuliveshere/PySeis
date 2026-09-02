"""Script to generate initial schema templates from maps.py."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import yaml
from pathlib import Path
from pathlib import Path

# Define internal schema fields based on maps.py targets
# Grouping them logically as they appear in SEGY_TO_SEISDATA values

SOURCE_COLS = [
    "source_id", "source_index", "source_x", "source_y", "source_z", 
    "uphole_time"
]

RECEIVER_COLS = [
    "receiver_id", "receiver_index", "receiver_x", "receiver_y", "receiver_z"
]

TRACE_HEADER_COLS = [
    "trace_id", "trace_sequence_number", "offset", "total_static", 
    "trace_identification_code", "num_samples", "sample_rate", 
    "recording_delay", "coordinate_scalar", "elevation_scalar"
]

def generate_schemas():
    output_dir = Path("src/pyseis/templates/schemas")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Source Schema
    source_schema = {
        'version': '1.0',
        'description': 'Source attributes schema',
        'columns': {k: 'int32' for k in SOURCE_COLS} # Defaulting to int32
    }
    with open(output_dir / "source_v1.0.yaml", 'w') as f:
        yaml.dump(source_schema, f, sort_keys=False)
        
    # 2. Receiver Schema
    recv_schema = {
        'version': '1.0',
        'description': 'Receiver attributes schema',
        'columns': {k: 'int32' for k in RECEIVER_COLS}
    }
    with open(output_dir / "receiver_v1.0.yaml", 'w') as f:
        yaml.dump(recv_schema, f, sort_keys=False)
        
    # 3. Trace Header Schema
    trace_schema = {
        'version': '1.0',
        'description': 'Trace header attributes schema',
        'columns': {k: 'int32' for k in TRACE_HEADER_COLS}
    }
    with open(output_dir / "trace_header_v1.0.yaml", 'w') as f:
        yaml.dump(trace_schema, f, sort_keys=False)
        
    # 4. Trace Data Schema
    trace_data_schema = {
        'version': '1.0',
        'description': 'Trace data array structure',
        'dtype': 'float32',
        'dimension_names': ['traces', 'samples']
    }
    with open(output_dir / "trace_data_v1.0.yaml", 'w') as f:
        yaml.dump(trace_data_schema, f, sort_keys=False)
        
    # 5. Layout Schema
    layout_schema = {
        'layout_version': '1.0',
        'description': 'Directory layout version',
        'generator': 'pyseis'
    }
    with open(output_dir / "layout_v1.0.yaml", 'w') as f:
        yaml.dump(layout_schema, f, sort_keys=False)
        
    print(f"Generated 5 schema templates in {output_dir}")

if __name__ == "__main__":
    generate_schemas()
