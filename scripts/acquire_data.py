"""
acquire_data.py

Programmatically acquire raw data for the IS 477 final project.

This script downloads two raw datasets:

1. Federal Funds Effective Rate (FRED series ID: DFF)
   - Source: Federal Reserve Bank of St. Louis / FRED API
   - Output:
     - data/raw/fred_dff_raw.json
     - data/raw/fred_dff.csv

2. S&P 500 Index (^GSPC)
   - Source: Yahoo Finance through the yfinance Python package
   - Output:
     - data/raw/sp500_raw.csv

The script also generates:
- data/raw/CHECKSUMS.sha256
- data/raw/acquisition_metadata.json

Two data acquisition modes are supported:

1. frozen mode (default)
   - Uses a fixed end date for reproducibility.
   - This is the recommended mode for the final project submission.

2. live mode
   - Retrieves the latest available data.
   - Useful for updating the project, but results may differ from the submitted report.

Usage from repository root:

    python scripts/acquire_data.py

Optional environment variables:

    export DATA_MODE=frozen
    export DATA_MODE=live

    export FRED_API_KEY=your_fred_api_key_here

If FRED_API_KEY is not set, the script will look for a local file named
apikey.txt in the repository root. The apikey.txt file should NOT be committed
to GitHub.

Expected outputs:
- data/raw/fred_dff_raw.json
- data/raw/fred_dff.csv
- data/raw/sp500_raw.csv
- data/raw/CHECKSUMS.sha256
- data/raw/acquisition_metadata.json
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
from typing import Iterable

import pandas as pd
import requests
import yfinance as yf


# -----------------------------------------------------------------------------
# Project paths
# -----------------------------------------------------------------------------

def find_project_root() -> Path:
    """
    Return the repository root.

    This function allows the script to work whether it is stored in the
    repository root or inside a scripts/ folder.
    """
    current_file = Path(__file__).resolve()

    # If the script is in scripts/, use its parent directory's parent.
    if current_file.parent.name == "scripts":
        return current_file.parent.parent

    # Otherwise, assume the script is already in the repository root.
    return current_file.parent


PROJECT_ROOT = find_project_root()
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

FRED_API_KEY_FILE = PROJECT_ROOT / "apikey.txt"
FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

FRED_SERIES_ID = "DFF"
YAHOO_TICKER = "^GSPC"

VALID_DATA_MODES = {"frozen", "live"}
DATA_MODE = os.getenv("DATA_MODE", "frozen").strip().lower()

# Fixed reproducible cutoff date used for the submitted project.
# FRED includes observations through this date when observation_end is supplied.
# yfinance treats the end date as exclusive, but because 2026-03-22 is a Sunday,
# the latest market observation before this cutoff is 2026-03-20.
FROZEN_END_DATE = "2026-03-22"

SP500_START_DATE = "1927-01-01"


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------

def validate_data_mode(mode: str) -> None:
    """Validate DATA_MODE."""
    if mode not in VALID_DATA_MODES:
        allowed = ", ".join(sorted(VALID_DATA_MODES))
        raise ValueError(
            f"Invalid DATA_MODE={mode!r}. Expected one of: {allowed}."
        )


def utc_now_iso() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    """Compute the SHA-256 checksum for a file."""
    h = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            h.update(chunk)

    return h.hexdigest()


def write_checksums(paths: Iterable[Path], output_file: Path) -> None:
    """
    Write SHA-256 checksums for the given files.

    Format follows the common sha256sum convention:

        <checksum>  <relative/path/to/file>
    """
    lines: list[str] = []

    for path in paths:
        checksum = sha256_file(path)
        relative_path = path.relative_to(PROJECT_ROOT)
        lines.append(f"{checksum}  {relative_path.as_posix()}")

    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    """Read a JSON file as a dictionary."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(data: dict, path: Path) -> None:
    """Write a dictionary to a JSON file."""
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_fred_api_key() -> str:
    """
    Load the FRED API key.

    Preferred method:
        FRED_API_KEY environment variable

    Fallback method:
        apikey.txt in the repository root

    The apikey.txt file should not be committed to GitHub.
    """
    env_key = os.getenv("FRED_API_KEY")

    if env_key and env_key.strip():
        return env_key.strip()

    if FRED_API_KEY_FILE.exists():
        file_key = FRED_API_KEY_FILE.read_text(encoding="utf-8").strip()
        if file_key:
            return file_key

    raise RuntimeError(
        "FRED API key not found.\n\n"
        "Set the FRED_API_KEY environment variable, for example:\n"
        "    export FRED_API_KEY=your_fred_api_key_here\n\n"
        "Or create a local apikey.txt file in the repository root.\n"
        "Do not commit apikey.txt to GitHub."
    )


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names for raw CSV output.

    This function keeps raw data recognizable while avoiding spaces and
    inconsistent capitalization.
    """
    renamed = {
        column: str(column).strip().lower().replace(" ", "_")
        for column in df.columns
    }
    return df.rename(columns=renamed)


def flatten_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flatten yfinance MultiIndex columns if present.

    Some versions of yfinance return a MultiIndex even for a single ticker.
    This converts those columns into simple names.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join(str(level) for level in column if str(level))
            for column in df.columns
        ]

    return df


# -----------------------------------------------------------------------------
# FRED acquisition
# -----------------------------------------------------------------------------

def acquire_fred_dff(api_key: str, mode: str) -> tuple[Path, Path, dict]:
    """
    Download Federal Funds Effective Rate data from FRED.

    Returns:
        raw_json_path, csv_path, metadata
    """
    params = {
        "series_id": FRED_SERIES_ID,
        "api_key": api_key,
        "file_type": "json",
    }

    if mode == "frozen":
        params["observation_end"] = FROZEN_END_DATE

    response = requests.get(FRED_URL, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()

    if "observations" not in data:
        raise RuntimeError(
            "Unexpected FRED API response: missing 'observations' field."
        )

    raw_json_path = RAW_DIR / "fred_dff_raw.json"
    write_json(data, raw_json_path)

    fred_df = pd.DataFrame(data["observations"])

    # These conversions are used only to make the raw CSV easier to inspect.
    # The formal cleaning script will perform the final cleaning operations.
    if "date" in fred_df.columns:
        fred_df["date"] = pd.to_datetime(fred_df["date"], errors="coerce").dt.date

    if "value" in fred_df.columns:
        fred_df["value"] = pd.to_numeric(fred_df["value"], errors="coerce")

    fred_df = standardize_columns(fred_df)

    csv_path = RAW_DIR / "fred_dff.csv"
    fred_df.to_csv(csv_path, index=False)

    metadata = {
        "dataset": "Federal Funds Effective Rate",
        "source": "Federal Reserve Bank of St. Louis FRED API",
        "series_id": FRED_SERIES_ID,
        "url": FRED_URL,
        "mode": mode,
        "frozen_end_date": FROZEN_END_DATE if mode == "frozen" else None,
        "row_count": int(len(fred_df)),
        "columns": list(fred_df.columns),
        "output_files": [
            raw_json_path.relative_to(PROJECT_ROOT).as_posix(),
            csv_path.relative_to(PROJECT_ROOT).as_posix(),
        ],
    }

    return raw_json_path, csv_path, metadata


# -----------------------------------------------------------------------------
# S&P 500 acquisition
# -----------------------------------------------------------------------------

def acquire_sp500(mode: str) -> tuple[Path, dict]:
    """
    Download S&P 500 data from Yahoo Finance using yfinance.

    Returns:
        csv_path, metadata
    """
    if mode == "frozen":
        sp500_df = yf.download(
            YAHOO_TICKER,
            start=SP500_START_DATE,
            end=FROZEN_END_DATE,
            progress=False,
            auto_adjust=False,
        )
    else:
        sp500_df = yf.download(
            YAHOO_TICKER,
            period="max",
            progress=False,
            auto_adjust=False,
        )

    if sp500_df.empty:
        raise RuntimeError(
            "Downloaded S&P 500 dataset is empty. "
            "Check internet connection or yfinance availability."
        )

    sp500_df = flatten_yfinance_columns(sp500_df)
    sp500_df = sp500_df.reset_index()
    sp500_df = standardize_columns(sp500_df)

    # If yfinance returns ticker-suffixed columns such as close_^gspc,
    # simplify them to close, open, high, low, etc.
    simplified_columns = {}
    for column in sp500_df.columns:
        if column.endswith("_^gspc"):
            simplified_columns[column] = column.replace("_^gspc", "")
    sp500_df = sp500_df.rename(columns=simplified_columns)

    if "date" in sp500_df.columns:
        sp500_df["date"] = pd.to_datetime(sp500_df["date"], errors="coerce").dt.date

    csv_path = RAW_DIR / "sp500_raw.csv"
    sp500_df.to_csv(csv_path, index=False)

    metadata = {
        "dataset": "S&P 500 Index",
        "source": "Yahoo Finance via yfinance",
        "ticker": YAHOO_TICKER,
        "mode": mode,
        "start_date": SP500_START_DATE if mode == "frozen" else "max",
        "frozen_end_date": FROZEN_END_DATE if mode == "frozen" else None,
        "row_count": int(len(sp500_df)),
        "columns": list(sp500_df.columns),
        "output_files": [
            csv_path.relative_to(PROJECT_ROOT).as_posix(),
        ],
    }

    return csv_path, metadata


# -----------------------------------------------------------------------------
# Acquisition metadata
# -----------------------------------------------------------------------------

def write_acquisition_metadata(
    fred_metadata: dict,
    sp500_metadata: dict,
    checksum_path: Path,
    output_file: Path,
) -> None:
    """Write project-level acquisition metadata."""
    metadata = {
        "project": "Federal Funds Rate and S&P 500 Market Performance",
        "script": "scripts/acquire_data.py",
        "generated_at_utc": utc_now_iso(),
        "data_mode": DATA_MODE,
        "raw_data_directory": RAW_DIR.relative_to(PROJECT_ROOT).as_posix(),
        "datasets": [
            fred_metadata,
            sp500_metadata,
        ],
        "checksum_file": checksum_path.relative_to(PROJECT_ROOT).as_posix(),
        "notes": [
            "Frozen mode uses a fixed end date to support reproducibility.",
            "Live mode retrieves the latest available observations and may produce different results.",
            "Formal cleaning, quality assessment, integration, and analysis are performed by downstream scripts.",
            "The FRED API key is intentionally not stored in the repository.",
        ],
    }

    write_json(metadata, output_file)


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def main() -> None:
    """Run the raw data acquisition workflow."""
    validate_data_mode(DATA_MODE)

    print("=" * 72)
    print("IS 477 Final Project: Raw Data Acquisition")
    print("=" * 72)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Raw data directory: {RAW_DIR}")
    print(f"Data mode: {DATA_MODE}")

    if DATA_MODE == "frozen":
        print(f"Frozen end date: {FROZEN_END_DATE}")

    print("\nLoading FRED API key...")
    fred_api_key = load_fred_api_key()

    print("\nDownloading FRED DFF data...")
    fred_json_path, fred_csv_path, fred_metadata = acquire_fred_dff(
        api_key=fred_api_key,
        mode=DATA_MODE,
    )
    print(f"FRED rows downloaded: {fred_metadata['row_count']}")
    print(f"Saved: {fred_json_path.relative_to(PROJECT_ROOT)}")
    print(f"Saved: {fred_csv_path.relative_to(PROJECT_ROOT)}")

    print("\nDownloading S&P 500 data...")
    sp500_csv_path, sp500_metadata = acquire_sp500(mode=DATA_MODE)
    print(f"S&P 500 rows downloaded: {sp500_metadata['row_count']}")
    print(f"Saved: {sp500_csv_path.relative_to(PROJECT_ROOT)}")

    print("\nGenerating SHA-256 checksums...")
    checksum_path = RAW_DIR / "CHECKSUMS.sha256"
    files_to_hash = [
        fred_json_path,
        fred_csv_path,
        sp500_csv_path,
    ]
    write_checksums(files_to_hash, checksum_path)
    print(f"Saved: {checksum_path.relative_to(PROJECT_ROOT)}")

    print("\nWriting acquisition metadata...")
    metadata_path = RAW_DIR / "acquisition_metadata.json"
    write_acquisition_metadata(
        fred_metadata=fred_metadata,
        sp500_metadata=sp500_metadata,
        checksum_path=checksum_path,
        output_file=metadata_path,
    )
    print(f"Saved: {metadata_path.relative_to(PROJECT_ROOT)}")

    print("\nAcquisition complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()