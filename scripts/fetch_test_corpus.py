"""
PySeis Test Corpus Fetcher & Validator
Reads data/corpus_manifest.yaml to fetch, verify, and validate SEG-Y and SEG-D open datasets.
"""

import argparse
import hashlib
import os
import sys
import urllib.request
from pathlib import Path
from typing import Dict, Any

import yaml

# Add src to path for pyseis imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA256 hash of a file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()

def download_file(url: str, dest_path: Path) -> bool:
    """Download a remote file over HTTPS with progress tracking."""
    print(f"  Downloading: {url} -> {dest_path.name}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PySeis-Corpus-Fetcher/2.0 (SEG Wiki Open Data)"}
    )
    try:
        with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            block_size = 65536
            
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    sys.stdout.write(f"\r    Progress: {downloaded}/{total_size} bytes ({percent:.1f}%)")
                    sys.stdout.flush()
        print("\n    [OK] Download complete.")
        return True
    except Exception as e:
        print(f"\n    [ERROR] Download failed: {e}")
        if dest_path.exists() and dest_path.stat().st_size == 0:
            dest_path.unlink()
        return False

def validate_dataset_with_pyseis(entry: Dict[str, Any], file_path: Path) -> bool:
    """Validate downloaded SEG-Y or SEG-D dataset with PySeis."""
    fmt = entry.get("format", "").lower()
    print(f"  Validating {file_path.name} with PySeis ({fmt})...")
    
    try:
        import pyseis as ps
        import io
        
        if fmt == "segy":
            importer = ps.SEGYImporter(file_path)
            sd = importer.import_data(io.BytesIO())
            print(f"    [OK] SEG-Y Dataset Validated | Traces: {sd.n_traces}, Samples: {sd.n_samples}, Rate: {sd.sample_rate}s")
            return True
        elif fmt == "segd":
            importer = ps.SEGDImporter(file_path)
            sd = importer.import_data(io.BytesIO())
            print(f"    [OK] SEG-D Dataset Validated | Traces: {sd.n_traces}, Samples: {sd.n_samples}, Rate: {sd.sample_rate}s")
            return True
        else:
            print(f"    [SKIP] Unhandled format: {fmt}")
            return False
    except Exception as e:
        print(f"    [NOTICE] PySeis inspection note for {file_path.name}: {e}")
        return False

def process_manifest(manifest_path: Path, verify_only: bool = False, force: bool = False) -> None:
    """Process SEG-Y and SEG-D datasets listed in data/corpus_manifest.yaml."""
    if not manifest_path.exists():
        print(f"Error: Manifest file '{manifest_path}' not found.")
        sys.exit(1)
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
        
    datasets = manifest.get("datasets", [])
    print(f"Loaded SEG Open Data Manifest '{manifest_path}' (v{manifest.get('version', '2.0')})")
    print(f"Total Dataset Entries: {len(datasets)}\n")
    
    success_count = 0
    
    for idx, entry in enumerate(datasets, 1):
        item_id = entry.get("id", f"item_{idx}")
        name = entry.get("name", item_id)
        fmt = entry.get("format", "").upper()
        data_type = entry.get("data_type", "")
        file_name = entry.get("file_name", "")
        target_dir = PROJECT_ROOT / entry.get("target_dir", "data")
        dest_path = target_dir / file_name
        download_url = entry.get("download_url", "")
        expected_sha = entry.get("sha256", "")
        wiki_page = entry.get("seg_wiki_page", "")
        
        print(f"[{idx}/{len(datasets)}] {name} ({fmt} - {data_type})")
        print(f"  SEG Wiki Source: {wiki_page}")
        print(f"  Target Path: {dest_path}")
        
        if verify_only:
            if dest_path.exists():
                sha = calculate_sha256(dest_path)
                print(f"  [EXISTS] SHA256: {sha}")
                if validate_dataset_with_pyseis(entry, dest_path):
                    success_count += 1
            else:
                print(f"  [MISSING] File not downloaded locally.")
            continue
            
        # Download file if missing or forced
        if not dest_path.exists() or force:
            if not download_url:
                print(f"  [SKIP] Manifest entry awaiting URL registration.")
                continue
            if not download_file(download_url, dest_path):
                continue
        else:
            print(f"  [EXISTS] Local dataset file present.")
            
        # Verify SHA256 if present in manifest
        sha = calculate_sha256(dest_path)
        print(f"  SHA256 Checksum: {sha}")
        if expected_sha and sha != expected_sha:
            print(f"  [WARNING] SHA256 mismatch! Expected: {expected_sha}")
            
        if validate_dataset_with_pyseis(entry, dest_path):
            success_count += 1
            
    print(f"\nManifest Execution Summary: {success_count}/{len(datasets)} SEG-Y/SEG-D datasets validated.")

def main():
    parser = argparse.ArgumentParser(description="Fetch and validate PySeis SEG-Y/SEG-D test corpus from SEG Wiki Open Data.")
    parser.add_argument("--manifest", default="data/corpus_manifest.yaml", help="Path to YAML corpus manifest")
    parser.add_argument("--verify-only", action="store_true", help="Verify existing local dataset files without downloading")
    parser.add_argument("--force", action="store_true", help="Force re-download of dataset files")
    
    args = parser.parse_args()
    manifest_path = PROJECT_ROOT / args.manifest
    process_manifest(manifest_path, verify_only=args.verify_only, force=args.force)

if __name__ == "__main__":
    main()
