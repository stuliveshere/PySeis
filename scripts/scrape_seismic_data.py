"""
Scraper script for sampling SEG-Y and SEG-D files from project directories on T:\\.
Finds directories containing SEG-Y and SEG-D files, selects 1 random file per format per directory,
and copies them into data/segy and data/segd for automated testing.
"""

import argparse
import hashlib
import os
import random
import shutil
import sys
from pathlib import Path
from typing import List, Set, Union, Optional

# Add src to path using absolute resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pyseis_io.segd.schema import bcd_digits

SEGY_EXTENSIONS: Set[str] = {".segy", ".sgy"}
SEGD_EXTENSIONS: Set[str] = {".segd", ".sgd", ".raw", ".dat"}

def get_dir_hash(dir_path: Path) -> str:
    """Generate a short unique 6-character hash for a directory path."""
    return hashlib.md5(str(dir_path).encode("utf-8")).hexdigest()[:6]

def is_segd_file(file_path: Path) -> bool:
    """Quick check if a file is a valid SEG-D file by inspecting the GH1 block header."""
    ext = file_path.suffix.lower()
    if ext in (".segd", ".sgd", ".raw"):
        return True
    if ext == ".dat":
        try:
            with open(file_path, "rb") as f:
                header_bytes = f.read(32)
                if len(header_bytes) < 32:
                    return False
                # Format code at bytes 3-4 (0-indexed 2-3)
                fmt_code = bcd_digits(header_bytes, 2, 2)
                return fmt_code > 0
        except Exception:
            return False
    return False

def scrape_seismic(
    source_dir: Union[str, Path] = "T:\\",
    target_segy: Union[str, Path] = "data/segy",
    target_segd: Union[str, Path] = "data/segd",
    max_dirs: Optional[int] = None,
    dry_run: bool = False
) -> None:
    source_path = Path(source_dir)
    segy_dest = Path(target_segy)
    segd_dest = Path(target_segd)

    if not dry_run:
        segy_dest.mkdir(parents=True, exist_ok=True)
        segd_dest.mkdir(parents=True, exist_ok=True)

    print(f"Scanning '{source_path}' for SEG-Y and SEG-D files...")
    
    dirs_processed = 0
    segy_copied = 0
    segd_copied = 0

    for root, _, files in os.walk(source_path):
        if not files:
            continue

        root_path = Path(root)
        segy_files: List[Path] = []
        segd_files: List[Path] = []

        for f in files:
            full_f = root_path / f
            ext = full_f.suffix.lower()
            if ext in SEGY_EXTENSIONS:
                segy_files.append(full_f)
            elif ext in SEGD_EXTENSIONS and is_segd_file(full_f):
                segd_files.append(full_f)

        if not segy_files and not segd_files:
            continue

        dirs_processed += 1
        d_hash = get_dir_hash(root_path)

        # Copy 1 random SEG-Y file from this directory
        if segy_files:
            chosen_segy = random.choice(segy_files)
            dest_file = segy_dest / f"{d_hash}_{chosen_segy.name}"
            if not dest_file.exists():
                print(f"  [SEG-Y] {chosen_segy} -> {dest_file}")
                if not dry_run:
                    try:
                        shutil.copy2(chosen_segy, dest_file)
                        segy_copied += 1
                    except Exception as e:
                        print(f"    Error copying {chosen_segy}: {e}")

        # Copy 1 random SEG-D file from this directory
        if segd_files:
            chosen_segd = random.choice(segd_files)
            dest_file = segd_dest / f"{d_hash}_{chosen_segd.name}"
            if not dest_file.exists():
                print(f"  [SEG-D] {chosen_segd} -> {dest_file}")
                if not dry_run:
                    try:
                        shutil.copy2(chosen_segd, dest_file)
                        segd_copied += 1
                    except Exception as e:
                        print(f"    Error copying {chosen_segd}: {e}")

        if max_dirs and dirs_processed >= max_dirs:
            print(f"Reached maximum directory limit ({max_dirs}). Stopping scan.")
            break

    print(f"\nScraping Complete!")
    print(f"Directories processed: {dirs_processed}")
    print(f"SEG-Y files copied: {segy_copied} to '{segy_dest}'")
    print(f"SEG-D files copied: {segd_copied} to '{segd_dest}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape SEG-Y and SEG-D sample files from T:\\ project directories.")
    parser.add_argument("--source", default="T:\\", help="Source directory to scan (default: T:\\)")
    parser.add_argument("--target-segy", default="data/segy", help="Destination folder for SEG-Y files (default: data/segy)")
    parser.add_argument("--target-segd", default="data/segd", help="Destination folder for SEG-D files (default: data/segd)")
    parser.add_argument("--max-dirs", type=int, default=None, help="Maximum number of directories to process")
    parser.add_argument("--dry-run", action="store_true", help="Perform scan without copying files")

    args = parser.parse_args()
    scrape_seismic(
        source_dir=args.source,
        target_segy=args.target_segy,
        target_segd=args.target_segd,
        max_dirs=args.max_dirs,
        dry_run=args.dry_run
    )
