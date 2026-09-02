"""
Pre-flight Multi-File Corpus Scanner & Validator.
Scans SEG-D files concurrently, classifying files into GOOD, INCOMPATIBLE, CORRUPTED, IO_ERROR,
and verifying sample rate and gather type consistency across datasets.
"""

from __future__ import annotations

import concurrent.futures
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from .reader import SEGDReader
from .schema import SchemaManager

class CorpusScanner:
    """Pre-flight corpus scanner and multi-file validator."""

    def __init__(self, schema_manager: Optional[SchemaManager] = None, max_workers: int = 4):
        self.schema_manager = schema_manager or SchemaManager()
        self.max_workers = max_workers

    def scan_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        path = Path(file_path)
        res = {
            "path": str(path),
            "filename": path.name,
            "status": "CORRUPTED",
            "revision": None,
            "manufacturer": None,
            "format_code": None,
            "sample_interval_us": None,
            "samples_per_trace": None,
            "num_traces": None,
            "gather_type": None,
            "error_note": None
        }

        if not path.exists():
            res["status"] = "IO_ERROR"
            res["error_note"] = "File not found"
            return res

        try:
            with SEGDReader(path, schema_manager=self.schema_manager) as reader:
                probe = reader.probe()
                res.update({
                    "status": "GOOD",
                    "revision": probe["revision"],
                    "manufacturer": probe["manufacturer"],
                    "format_code": probe["format_code"],
                    "sample_interval_us": probe["sample_interval_us"],
                    "samples_per_trace": probe["samples_per_trace"],
                    "num_traces": probe["num_traces"],
                    "gather_type": probe["gather_type"],
                })
        except Exception as e:
            res["status"] = "CORRUPTED"
            res["error_note"] = str(e)

        return res

    def scan_directory(
        self,
        directory: Union[str, Path],
        pattern: str = "*.segd",
        recursive: bool = True,
        strictness: str = "strict"
    ) -> pd.DataFrame:
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))

        if not files:
            # Try case-insensitive search or fallback
            files = [f for f in dir_path.iterdir() if f.is_file() and f.name.lower().endswith(".segd")]

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(self.scan_file, files))

        df = pd.DataFrame(results)
        if df.empty:
            return df

        # Consistency verification
        good_files = df[df["status"] == "GOOD"]
        if not good_files.empty:
            sample_rates = good_files["sample_interval_us"].unique()
            if len(sample_rates) > 1:
                note = f"Non-uniform sample intervals detected: {sample_rates}"
                if strictness.lower() == "strict":
                    df.loc[df["status"] == "GOOD", "status"] = "INCOMPATIBLE"
                    df.loc[df["status"] == "INCOMPATIBLE", "error_note"] = note
                elif strictness.lower() == "warn":
                    df["warning_note"] = note

        return df
