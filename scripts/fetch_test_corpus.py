"""
Script to download, verify, and validate the PySeis testing corpus based on data/corpus_manifest.yaml.
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

def download_file(url: str, dest_path: Path) -> None:
    """Download a remote file over HTTPS with a progress indicator."""
    print(f"Downloading: {url} -> {dest_path.name}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PySeis-Corpus-Fetcher/1.0"}
    )
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
                sys.stdout.write(f"\r  Progress: {downloaded}/{total_size} bytes ({percent:.1f}%)")
                sys.stdout.flush()
    print("\n  Download complete.")

def validate_dataset_with_pyseis(entry: Dict[str, Any], file_path: Path) -> bool:
    """Attempt to open and validate the dataset using pyseis."""
    fmt = entry.get("format", "").lower()
    print(f"  Validating {file_path.name} using pyseis ({fmt})...")
    
    try:
        import pyseis as ps
        
        if fmt == "segy":
            importer = ps.SEGYImporter(file_path)
            sd = importer.read()
            print(f"    [OK] Traces: {sd.n_traces}, Samples: {sd.n_samples}, Rate: {sd.sample_rate}")
        elif fmt == "segd":
            importer = ps.SEGDImporter(file_path)
            sd = importer.read()
            print(f"    [OK] Traces: {sd.n_traces}, Samples: {sd.n_samples}, Rate: {sd.sample_rate}")
        elif fmt == "su":
            importer = ps.SUImporter(file_path)
            sd = importer.read()
            print(f"    [OK] Traces: {sd.n_traces}, Samples: {sd.n_samples}, Rate: {sd.sample_rate}")
        else:
            print(f"    [SKIP] Unknown format specification: {fmt}")
        return True
    except Exception as e:
        print(f"    [WARN] PySeis validation notice for {file_path.name}: {e}")
        return False

def process_manifest(manifest_path: Path, verify_only: bool = False, force: bool = False) -> None:
    """Process all datasets listed in the corpus manifest."""
    if not manifest_path.exists():
        print(f"Error: Manifest file '{manifest_path}' not found.")
        sys.exit(1)
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
        
    datasets = manifest.get("datasets", [])
    print(f"Loaded manifest '{manifest_path}' (v{manifest.get('version', '1.0')}): {len(datasets)} dataset entries found.\n")
    
    success_count = 0
    
    for idx, entry in enumerate(datasets, 1):
        item_id = entry.get("id", f"item_{idx}")
        name = entry.get("name", item_id)
        file_name = entry.get("file_name", "")
        target_dir = PROJECT_ROOT / entry.get("target_dir", "data")
        dest_path = target_dir / file_name
        download_url = entry.get("download_url", "")
        expected_sha = entry.get("sha256", "")
        
        print(f"[{idx}/{len(datasets)}] {name} ({item_id})")
        print(f"  Target File: {dest_path}")
        
        if verify_only:
            if dest_path.exists():
                sha = calculate_sha256(dest_path)
                print(f"  [FOUND] SHA256: {sha[:12]}...")
                validate_dataset_with_pyseis(entry, dest_path)
            else:
                print(f"  [MISSING] File does not exist locally.")
            continue
            
        # Download if missing or forced
        if not dest_path.exists() or force:
            if not download_url:
                print(f"  [SKIP] No download_url provided for {item_id}.")
                continue
            try:
                download_file(download_url, dest_path)
            except Exception as e:
                print(f"  [ERROR] Failed to download {download_url}: {e}")
                continue
        else:
            print(f"  [EXISTS] File already present.")
            
        # Check SHA256
        sha = calculate_sha256(dest_path)
        print(f"  Calculated SHA256: {sha}")
        if expected_sha and sha != expected_sha:
            print(f"  [WARNING] SHA256 mismatch! Expected: {expected_sha}")
        
        # Validate with PySeis
        if validate_dataset_with_pyseis(entry, dest_path):
            success_count += 1
            
    print(f"\nProcessing Complete: {success_count}/{len(datasets)} datasets validated.")

def main():
    parser = argparse.ArgumentParser(description="Fetch and validate PySeis testing corpus.")
    parser.add_argument("--manifest", default="data/corpus_manifest.yaml", help="Path to YAML corpus manifest")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing local files without downloading")
    parser.add_argument("--force", action="store_true", help="Force re-download of files even if present")
    
    args = parser.parse_args()
    manifest_path = PROJECT_ROOT / args.manifest
    process_manifest(manifest_path, verify_only=args.verify_only, force=args.force)

if __name__ == "__main__":
    main()
