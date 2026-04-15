"""
acquire_data.py

Programmatically acquire raw data for the project.

Supports two modes:
- frozen (default): reproducible dataset with fixed end date (2026-03-22)
- live: fetch latest available data

Outputs:
- data/raw/fred_dff_raw.json
- data/raw/fred_dff.csv
- data/raw/sp500_raw.csv
- data/raw/CHECKSUMS.sha256

Control mode via environment variable:
    export DATA_MODE=frozen   # default
    export DATA_MODE=live
"""

from pathlib import Path
import hashlib
import json
import os
import requests
import pandas as pd
import yfinance as yf


# -----------------------------
# Configuration
# -----------------------------
PROJECT_ROOT = Path(".")
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

FRED_API_KEY_FILE = PROJECT_ROOT / "apikey.txt"
FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

FRED_SERIES_ID = "DFF"
YAHOO_TICKER = "^GSPC"

# Mode control
DATA_MODE = os.getenv("DATA_MODE", "frozen")  # default frozen

# Fixed reproducible cutoff date
FROZEN_END_DATE = "2026-03-22"


# -----------------------------
# Utility functions
# -----------------------------
def sha256_file(path: Path) -> str:
    """Compute SHA-256 checksum for a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_checksums(paths: list[Path], output_file: Path) -> None:
    """Write SHA-256 checksums."""
    lines = []
    for path in paths:
        checksum = sha256_file(path)
        lines.append(f"{checksum}  {path.as_posix()}")
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


# -----------------------------
# FRED acquisition
# -----------------------------
def load_api_key(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError("Missing apikey.txt")
    return path.read_text().strip()


def acquire_fred(api_key: str) -> tuple[Path, Path]:
    """Download FRED DFF data."""
    params = {
        "series_id": FRED_SERIES_ID,
        "api_key": api_key,
        "file_type": "json",
    }

    if DATA_MODE == "frozen":
        params["observation_end"] = FROZEN_END_DATE

    response = requests.get(FRED_URL, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    # Save raw JSON
    raw_json_path = RAW_DIR / "fred_dff_raw.json"
    with open(raw_json_path, "w") as f:
        json.dump(data, f, indent=2)

    # Convert to DataFrame
    df = pd.DataFrame(data["observations"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    csv_path = RAW_DIR / "fred_dff.csv"
    df.to_csv(csv_path, index=False)

    print(f"FRED rows: {len(df)}")
    return raw_json_path, csv_path


# -----------------------------
# Yahoo Finance acquisition
# -----------------------------
def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    return df


def acquire_sp500() -> Path:
    """Download S&P 500 data."""
    if DATA_MODE == "frozen":
        df = yf.download(
            YAHOO_TICKER,
            start="1927-01-01",
            end=FROZEN_END_DATE,
            progress=False,
        )
    else:
        df = yf.download(
            YAHOO_TICKER,
            period="max",
            progress=False,
        )

    df = flatten_columns(df)
    df = df.reset_index()

    csv_path = RAW_DIR / "sp500_raw.csv"
    df.to_csv(csv_path, index=False)

    print(f"S&P 500 rows: {len(df)}")
    return csv_path


# -----------------------------
# Main workflow
# -----------------------------
def main():
    print(f"Running in {DATA_MODE} mode")

    api_key = load_api_key(FRED_API_KEY_FILE)

    fred_json, fred_csv = acquire_fred(api_key)
    sp500_csv = acquire_sp500()

    checksum_path = RAW_DIR / "CHECKSUMS.sha256"
    write_checksums(
        [fred_json, fred_csv, sp500_csv],
        checksum_path
    )

    print("Acquisition complete")
    print(f"Checksums written to: {checksum_path}")


if __name__ == "__main__":
    main()