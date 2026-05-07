"""
data_quality.py

Profile and assess raw data quality for the IS 477 final project.

Important workflow note:
This script is intended to run BEFORE data cleaning and integration.

It reads only raw data files:
- data/raw/fred_dff.csv
- data/raw/sp500_raw.csv
- data/raw/CHECKSUMS.sha256

It does NOT depend on:
- data/processed/fred_dff_clean.csv
- data/processed/sp500_clean.csv
- data/processed/integrated_fred_sp500.csv

Outputs:
- results/data_quality_summary.csv
- results/missingness_summary.csv
- results/date_coverage_summary.csv
- results/schema_summary.csv
- results/temporal_alignment_profile.csv
- results/checksum_verification.csv
- docs/data_quality_profile.md

Purpose:
The script documents data quality issues before any cleaning decisions are
applied. The results should be used to justify the cleaning and integration
strategies in later workflow steps.

Usage from repository root:

    python scripts/data_quality.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import pandas as pd


# -----------------------------------------------------------------------------
# Project paths
# -----------------------------------------------------------------------------

def find_project_root() -> Path:
    """
    Return the repository root.

    This allows the script to work whether it is stored in the repository root
    or inside a scripts/ folder.
    """
    current_file = Path(__file__).resolve()

    if current_file.parent.name == "scripts":
        return current_file.parent.parent

    return current_file.parent


PROJECT_ROOT = find_project_root()

RAW_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_DIR = PROJECT_ROOT / "results"
DOCS_DIR = PROJECT_ROOT / "docs"

FRED_RAW_PATH = RAW_DIR / "fred_dff.csv"
SP500_RAW_PATH = RAW_DIR / "sp500_raw.csv"
CHECKSUMS_PATH = RAW_DIR / "CHECKSUMS.sha256"

DATA_QUALITY_SUMMARY_PATH = RESULTS_DIR / "data_quality_summary.csv"
MISSINGNESS_SUMMARY_PATH = RESULTS_DIR / "missingness_summary.csv"
DATE_COVERAGE_SUMMARY_PATH = RESULTS_DIR / "date_coverage_summary.csv"
SCHEMA_SUMMARY_PATH = RESULTS_DIR / "schema_summary.csv"
TEMPORAL_ALIGNMENT_PROFILE_PATH = RESULTS_DIR / "temporal_alignment_profile.csv"
CHECKSUM_VERIFICATION_PATH = RESULTS_DIR / "checksum_verification.csv"
DATA_QUALITY_PROFILE_DOC_PATH = DOCS_DIR / "data_quality_profile.md"


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------

def utc_now_iso() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def relative(path: Path) -> str:
    """Return a repository-relative POSIX path."""
    return path.relative_to(PROJECT_ROOT).as_posix()


def ensure_output_directories() -> None:
    """Create output directories if needed."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def require_file(path: Path) -> None:
    """Raise a clear error if an expected input file is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file is missing: {relative(path)}"
        )


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names for profiling only.

    This does not clean or overwrite raw data. It only makes profiling code
    robust across minor column-name differences.
    """
    rename_map = {
        column: (
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace(".", "_")
        )
        for column in df.columns
    }

    return df.rename(columns=rename_map)


def sha256_file(path: Path) -> str:
    """Compute SHA-256 checksum for a file."""
    h = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            h.update(chunk)

    return h.hexdigest()


def parse_checksum_file(path: Path) -> dict[str, str]:
    """
    Parse a CHECKSUMS.sha256 file.

    Expected format:
        <checksum>  <relative/path/to/file>
    """
    checksums: dict[str, str] = {}

    if not path.exists():
        return checksums

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) < 2:
            continue

        checksum = parts[0]
        file_path = parts[-1]
        checksums[file_path] = checksum

    return checksums


def safe_numeric(series: pd.Series) -> pd.Series:
    """Convert a series to numeric without raising errors."""
    return pd.to_numeric(series, errors="coerce")


def safe_dates(series: pd.Series) -> pd.Series:
    """Convert a series to datetime without raising errors."""
    return pd.to_datetime(series, errors="coerce")


def date_set_from_series(series: pd.Series) -> set:
    """Return a set of Python date objects from a date-like series."""
    parsed = safe_dates(series).dropna()
    return set(parsed.dt.date)


def count_missing_calendar_dates(dates: pd.Series) -> int:
    """
    Count missing calendar dates between min and max dates.

    For calendar-day data, this should often be zero.
    For trading-day data, this will usually be large because weekends and
    market holidays are expected gaps.
    """
    parsed = safe_dates(dates).dropna()

    if parsed.empty:
        return 0

    full_calendar = pd.date_range(parsed.min(), parsed.max(), freq="D")
    observed_dates = set(parsed.dt.date)
    full_dates = set(full_calendar.date)

    return len(full_dates - observed_dates)


def weekday_counts(dates: pd.Series) -> dict[str, int]:
    """Return weekday counts from a date-like series."""
    parsed = safe_dates(dates).dropna()

    if parsed.empty:
        return {
            "monday_rows": 0,
            "tuesday_rows": 0,
            "wednesday_rows": 0,
            "thursday_rows": 0,
            "friday_rows": 0,
            "saturday_rows": 0,
            "sunday_rows": 0,
        }

    counts = parsed.dt.day_name().value_counts().to_dict()

    return {
        "monday_rows": int(counts.get("Monday", 0)),
        "tuesday_rows": int(counts.get("Tuesday", 0)),
        "wednesday_rows": int(counts.get("Wednesday", 0)),
        "thursday_rows": int(counts.get("Thursday", 0)),
        "friday_rows": int(counts.get("Friday", 0)),
        "saturday_rows": int(counts.get("Saturday", 0)),
        "sunday_rows": int(counts.get("Sunday", 0)),
    }


def weekend_observation_count(dates: pd.Series) -> int:
    """Count Saturday and Sunday observations."""
    parsed = safe_dates(dates).dropna()

    if parsed.empty:
        return 0

    return int(parsed.dt.dayofweek.isin([5, 6]).sum())


# -----------------------------------------------------------------------------
# Load raw datasets
# -----------------------------------------------------------------------------

def load_raw_datasets() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and lightly standardize raw datasets for profiling."""
    require_file(FRED_RAW_PATH)
    require_file(SP500_RAW_PATH)

    fred_raw = pd.read_csv(FRED_RAW_PATH)
    sp500_raw = pd.read_csv(SP500_RAW_PATH)

    fred_profile = standardize_column_names(fred_raw)
    sp500_profile = standardize_column_names(sp500_raw)

    return fred_profile, sp500_profile


# -----------------------------------------------------------------------------
# Checksum verification
# -----------------------------------------------------------------------------

def verify_checksums() -> pd.DataFrame:
    """
    Verify raw file checksums against data/raw/CHECKSUMS.sha256.

    This step checks file integrity but does not modify files.
    """
    expected = parse_checksum_file(CHECKSUMS_PATH)

    target_files = [
        FRED_RAW_PATH,
        SP500_RAW_PATH,
    ]

    # Include the raw JSON file if present because it is usually hashed.
    fred_json_path = RAW_DIR / "fred_dff_raw.json"
    if fred_json_path.exists():
        target_files.insert(0, fred_json_path)

    rows = []

    for path in target_files:
        relative_path = relative(path)
        actual_checksum = sha256_file(path) if path.exists() else None
        expected_checksum = expected.get(relative_path)

        rows.append(
            {
                "file": relative_path,
                "exists": path.exists(),
                "expected_checksum_available": expected_checksum is not None,
                "expected_sha256": expected_checksum,
                "actual_sha256": actual_checksum,
                "matches_expected": (
                    expected_checksum == actual_checksum
                    if expected_checksum is not None and actual_checksum is not None
                    else None
                ),
            }
        )

    checksum_df = pd.DataFrame(rows)
    checksum_df.to_csv(CHECKSUM_VERIFICATION_PATH, index=False)

    return checksum_df


# -----------------------------------------------------------------------------
# Schema and missingness profiling
# -----------------------------------------------------------------------------

def build_schema_summary(
    dataset_name: str,
    source_file: Path,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Create a schema summary for one raw dataset."""
    rows = []

    for column in df.columns:
        non_missing = df[column].notna().sum()
        missing = df[column].isna().sum()

        rows.append(
            {
                "dataset": dataset_name,
                "source_file": relative(source_file),
                "column_name": column,
                "raw_dtype": str(df[column].dtype),
                "non_missing_count": int(non_missing),
                "missing_count": int(missing),
                "missing_percent": round(float(missing / len(df) * 100), 4)
                if len(df) > 0
                else 0.0,
                "example_value": (
                    str(df[column].dropna().iloc[0])
                    if non_missing > 0
                    else ""
                ),
            }
        )

    return pd.DataFrame(rows)


def build_missingness_summary(
    dataset_name: str,
    source_file: Path,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Create a column-level missingness summary."""
    rows = []

    for column in df.columns:
        missing = df[column].isna().sum()

        rows.append(
            {
                "dataset": dataset_name,
                "source_file": relative(source_file),
                "column_name": column,
                "row_count": int(len(df)),
                "missing_count": int(missing),
                "missing_percent": round(float(missing / len(df) * 100), 4)
                if len(df) > 0
                else 0.0,
            }
        )

    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Dataset-level profiling
# -----------------------------------------------------------------------------

def profile_fred(fred_df: pd.DataFrame) -> dict:
    """Profile raw FRED DFF data quality."""
    date_col = "date"
    value_col = "value"

    if date_col not in fred_df.columns:
        raise ValueError("FRED raw data must contain a 'date' column.")

    if value_col not in fred_df.columns:
        raise ValueError("FRED raw data must contain a 'value' column.")

    parsed_dates = safe_dates(fred_df[date_col])
    numeric_values = safe_numeric(fred_df[value_col])

    invalid_date_rows = int(parsed_dates.isna().sum())
    missing_value_rows_raw = int(fred_df[value_col].isna().sum())
    non_numeric_value_rows = int(
        numeric_values.isna().sum() - fred_df[value_col].isna().sum()
    )

    duplicate_date_rows = int(parsed_dates.duplicated().sum())
    duplicate_full_rows = int(fred_df.duplicated().sum())

    coverage = weekday_counts(fred_df[date_col])

    summary = {
        "dataset": "Federal Funds Effective Rate",
        "source_file": relative(FRED_RAW_PATH),
        "row_count": int(len(fred_df)),
        "column_count": int(len(fred_df.columns)),
        "columns": "; ".join(fred_df.columns),
        "duplicate_full_rows": duplicate_full_rows,
        "duplicate_date_rows": duplicate_date_rows,
        "invalid_date_rows": invalid_date_rows,
        "missing_core_value_rows": missing_value_rows_raw,
        "non_numeric_core_value_rows": non_numeric_value_rows,
        "date_min": parsed_dates.min().strftime("%Y-%m-%d"),
        "date_max": parsed_dates.max().strftime("%Y-%m-%d"),
        "unique_date_count": int(parsed_dates.nunique()),
        "missing_calendar_dates_between_min_max": count_missing_calendar_dates(
            fred_df[date_col]
        ),
        "weekend_observation_count": weekend_observation_count(fred_df[date_col]),
        "core_value_min": float(numeric_values.min()),
        "core_value_max": float(numeric_values.max()),
        "core_value_mean": round(float(numeric_values.mean()), 6),
        "quality_notes": (
            "Raw FRED data appears to be a complete calendar-day series within "
            "its date range. Weekend observations are expected because the "
            "series is reported on a calendar-day basis."
        ),
    }

    summary.update(coverage)

    return summary


def profile_sp500(sp500_df: pd.DataFrame) -> dict:
    """Profile raw S&P 500 data quality."""
    date_col = "date"

    if date_col not in sp500_df.columns:
        raise ValueError("S&P 500 raw data must contain a 'date' column.")

    required_numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
    ]

    missing_required_columns = [
        column for column in required_numeric_columns
        if column not in sp500_df.columns
    ]

    if missing_required_columns:
        raise ValueError(
            "S&P 500 raw data is missing expected columns: "
            f"{missing_required_columns}"
        )

    parsed_dates = safe_dates(sp500_df[date_col])
    duplicate_date_rows = int(parsed_dates.duplicated().sum())
    duplicate_full_rows = int(sp500_df.duplicated().sum())

    numeric_versions = {
        column: safe_numeric(sp500_df[column])
        for column in required_numeric_columns
    }

    non_numeric_counts = {
        column: int(
            numeric_versions[column].isna().sum() - sp500_df[column].isna().sum()
        )
        for column in required_numeric_columns
    }

    missing_numeric_raw = {
        column: int(sp500_df[column].isna().sum())
        for column in required_numeric_columns
    }

    open_series = numeric_versions["open"]
    high_series = numeric_versions["high"]
    low_series = numeric_versions["low"]
    close_series = numeric_versions["close"]
    adj_close_series = numeric_versions["adj_close"]
    volume_series = numeric_versions["volume"]

    high_less_than_low_rows = int((high_series < low_series).sum())
    open_outside_high_low_rows = int(
        ((open_series > high_series) | (open_series < low_series)).sum()
    )
    close_outside_high_low_rows = int(
        ((close_series > high_series) | (close_series < low_series)).sum()
    )
    non_positive_close_rows = int((close_series <= 0).sum())
    negative_volume_rows = int((volume_series < 0).sum())
    zero_volume_rows = int((volume_series == 0).sum())

    coverage = weekday_counts(sp500_df[date_col])

    summary = {
        "dataset": "S&P 500 Index",
        "source_file": relative(SP500_RAW_PATH),
        "row_count": int(len(sp500_df)),
        "column_count": int(len(sp500_df.columns)),
        "columns": "; ".join(sp500_df.columns),
        "duplicate_full_rows": duplicate_full_rows,
        "duplicate_date_rows": duplicate_date_rows,
        "invalid_date_rows": int(parsed_dates.isna().sum()),
        "missing_core_value_rows": int(
            sp500_df[
                ["date"] + required_numeric_columns
            ].isna().any(axis=1).sum()
        ),
        "non_numeric_core_value_rows": int(sum(non_numeric_counts.values())),
        "date_min": parsed_dates.min().strftime("%Y-%m-%d"),
        "date_max": parsed_dates.max().strftime("%Y-%m-%d"),
        "unique_date_count": int(parsed_dates.nunique()),
        "missing_calendar_dates_between_min_max": count_missing_calendar_dates(
            sp500_df[date_col]
        ),
        "weekend_observation_count": weekend_observation_count(sp500_df[date_col]),
        "core_value_min": float(close_series.min()),
        "core_value_max": float(close_series.max()),
        "core_value_mean": round(float(close_series.mean()), 6),
        "high_less_than_low_rows": high_less_than_low_rows,
        "open_outside_high_low_rows": open_outside_high_low_rows,
        "close_outside_high_low_rows": close_outside_high_low_rows,
        "non_positive_close_rows": non_positive_close_rows,
        "negative_volume_rows": negative_volume_rows,
        "zero_volume_rows": zero_volume_rows,
        "missing_numeric_raw_by_column": "; ".join(
            f"{column}={missing_numeric_raw[column]}"
            for column in required_numeric_columns
        ),
        "non_numeric_by_column": "; ".join(
            f"{column}={non_numeric_counts[column]}"
            for column in required_numeric_columns
        ),
        "quality_notes": (
            "Raw S&P 500 data is a trading-day series. Missing calendar dates "
            "between the first and last observation are expected because the "
            "market is closed on weekends and holidays. Zero-volume rows occur "
            "in older index records and should be considered when deciding "
            "whether volume is a core analysis variable."
        ),
    }

    summary.update(coverage)

    return summary


def build_date_coverage_summary(
    dataset_name: str,
    source_file: Path,
    df: pd.DataFrame,
    expected_frequency: str,
) -> dict:
    """Build date coverage profile for one dataset."""
    parsed_dates = safe_dates(df["date"]).dropna()

    full_calendar_days = len(
        pd.date_range(parsed_dates.min(), parsed_dates.max(), freq="D")
    )

    observed_unique_dates = parsed_dates.nunique()
    missing_calendar_dates = count_missing_calendar_dates(df["date"])

    row = {
        "dataset": dataset_name,
        "source_file": relative(source_file),
        "expected_frequency": expected_frequency,
        "date_min": parsed_dates.min().strftime("%Y-%m-%d"),
        "date_max": parsed_dates.max().strftime("%Y-%m-%d"),
        "row_count": int(len(df)),
        "unique_date_count": int(observed_unique_dates),
        "full_calendar_days_between_min_max": int(full_calendar_days),
        "missing_calendar_dates_between_min_max": int(missing_calendar_dates),
        "calendar_coverage_ratio": round(
            float(observed_unique_dates / full_calendar_days),
            6,
        ),
        "weekend_observation_count": weekend_observation_count(df["date"]),
    }

    row.update(weekday_counts(df["date"]))

    return row


# -----------------------------------------------------------------------------
# Cross-dataset temporal alignment profiling
# -----------------------------------------------------------------------------

def build_temporal_alignment_profile(
    fred_df: pd.DataFrame,
    sp500_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Profile date-level overlap before cleaning or integration.

    This does not integrate the datasets. It only quantifies the temporal
    alignment challenge that later cleaning and integration scripts need to
    address.
    """
    fred_dates = date_set_from_series(fred_df["date"])
    sp500_dates = date_set_from_series(sp500_df["date"])

    overlap_dates = fred_dates & sp500_dates
    fred_only_dates = fred_dates - sp500_dates
    sp500_only_dates = sp500_dates - fred_dates

    fred_min = min(fred_dates)
    fred_max = max(fred_dates)
    sp500_min = min(sp500_dates)
    sp500_max = max(sp500_dates)

    sp500_before_fred = {
        date for date in sp500_dates
        if date < fred_min
    }

    sp500_after_fred = {
        date for date in sp500_dates
        if date > fred_max
    }

    rows = [
        {
            "metric": "fred_unique_dates",
            "value": len(fred_dates),
            "notes": "Unique raw dates in the FRED DFF dataset.",
        },
        {
            "metric": "sp500_unique_dates",
            "value": len(sp500_dates),
            "notes": "Unique raw dates in the S&P 500 dataset.",
        },
        {
            "metric": "overlapping_dates",
            "value": len(overlap_dates),
            "notes": "Raw dates present in both datasets before cleaning or integration.",
        },
        {
            "metric": "fred_only_dates",
            "value": len(fred_only_dates),
            "notes": (
                "Dates present in FRED but not in S&P 500. Many of these are "
                "expected because FRED is calendar-day data while S&P 500 is "
                "trading-day data."
            ),
        },
        {
            "metric": "sp500_only_dates",
            "value": len(sp500_only_dates),
            "notes": (
                "Dates present in S&P 500 but not in FRED. In this project, "
                "these primarily reflect S&P 500 observations before the FRED "
                "DFF series begins."
            ),
        },
        {
            "metric": "sp500_dates_before_fred_start",
            "value": len(sp500_before_fred),
            "notes": "S&P 500 raw dates earlier than the first FRED DFF date.",
        },
        {
            "metric": "sp500_dates_after_fred_end",
            "value": len(sp500_after_fred),
            "notes": "S&P 500 raw dates later than the final FRED DFF date.",
        },
        {
            "metric": "fred_date_min",
            "value": fred_min.isoformat(),
            "notes": "Earliest FRED raw date.",
        },
        {
            "metric": "fred_date_max",
            "value": fred_max.isoformat(),
            "notes": "Latest FRED raw date.",
        },
        {
            "metric": "sp500_date_min",
            "value": sp500_min.isoformat(),
            "notes": "Earliest S&P 500 raw date.",
        },
        {
            "metric": "sp500_date_max",
            "value": sp500_max.isoformat(),
            "notes": "Latest S&P 500 raw date.",
        },
        {
            "metric": "overlap_date_min",
            "value": min(overlap_dates).isoformat() if overlap_dates else "",
            "notes": "Earliest date shared by both raw datasets.",
        },
        {
            "metric": "overlap_date_max",
            "value": max(overlap_dates).isoformat() if overlap_dates else "",
            "notes": "Latest date shared by both raw datasets.",
        },
    ]

    alignment_df = pd.DataFrame(rows)
    alignment_df.to_csv(TEMPORAL_ALIGNMENT_PROFILE_PATH, index=False)

    return alignment_df


# -----------------------------------------------------------------------------
# Human-readable documentation
# -----------------------------------------------------------------------------

def write_quality_profile_doc(
    fred_summary: dict,
    sp500_summary: dict,
    alignment_df: pd.DataFrame,
    checksum_df: pd.DataFrame,
) -> Path:
    """Write human-readable data quality profiling documentation."""

    alignment = {
        row["metric"]: row["value"]
        for _, row in alignment_df.iterrows()
    }

    checksum_failed = checksum_df[
        checksum_df["matches_expected"] == False
    ]

    checksum_status = (
        "All available raw-file checksums matched expected values."
        if checksum_failed.empty
        else "At least one raw-file checksum did not match the expected value."
    )

    content = f"""# Raw Data Quality Profile

Generated by `scripts/data_quality.py` on `{utc_now_iso()}`.

## Scope of This Profile

This profile evaluates the raw input data before cleaning and integration. It reads files from `data/raw/` and writes quality summaries to `results/`. It does not use or modify any files in `data/processed/`.

## Input Files Profiled

- `{relative(FRED_RAW_PATH)}`
- `{relative(SP500_RAW_PATH)}`
- `{relative(CHECKSUMS_PATH)}`

## Output Files

- `{relative(DATA_QUALITY_SUMMARY_PATH)}`
- `{relative(MISSINGNESS_SUMMARY_PATH)}`
- `{relative(DATE_COVERAGE_SUMMARY_PATH)}`
- `{relative(SCHEMA_SUMMARY_PATH)}`
- `{relative(TEMPORAL_ALIGNMENT_PROFILE_PATH)}`
- `{relative(CHECKSUM_VERIFICATION_PATH)}`

## Integrity Check

{checksum_status}

The checksum verification results are stored in `{relative(CHECKSUM_VERIFICATION_PATH)}`.

## Dataset 1: Federal Funds Effective Rate

Source file: `{fred_summary["source_file"]}`

Rows: {fred_summary["row_count"]}

Columns: {fred_summary["column_count"]}

Date range: {fred_summary["date_min"]} to {fred_summary["date_max"]}

Unique dates: {fred_summary["unique_date_count"]}

Missing calendar dates between minimum and maximum date: {fred_summary["missing_calendar_dates_between_min_max"]}

Weekend observations: {fred_summary["weekend_observation_count"]}

Duplicate date rows: {fred_summary["duplicate_date_rows"]}

Invalid date rows: {fred_summary["invalid_date_rows"]}

Missing core value rows: {fred_summary["missing_core_value_rows"]}

Non-numeric core value rows: {fred_summary["non_numeric_core_value_rows"]}

Core value range: {fred_summary["core_value_min"]} to {fred_summary["core_value_max"]}

Interpretation:

The FRED DFF data behaves like a complete calendar-day time series within its date range. Weekend observations are expected and should not be treated as errors. This structure creates an important temporal alignment issue when the data is later compared with S&P 500 trading-day observations.

## Dataset 2: S&P 500 Index

Source file: `{sp500_summary["source_file"]}`

Rows: {sp500_summary["row_count"]}

Columns: {sp500_summary["column_count"]}

Date range: {sp500_summary["date_min"]} to {sp500_summary["date_max"]}

Unique dates: {sp500_summary["unique_date_count"]}

Missing calendar dates between minimum and maximum date: {sp500_summary["missing_calendar_dates_between_min_max"]}

Weekend observations: {sp500_summary["weekend_observation_count"]}

Duplicate date rows: {sp500_summary["duplicate_date_rows"]}

Invalid date rows: {sp500_summary["invalid_date_rows"]}

Missing core value rows: {sp500_summary["missing_core_value_rows"]}

Non-numeric core value rows: {sp500_summary["non_numeric_core_value_rows"]}

Close value range: {sp500_summary["core_value_min"]} to {sp500_summary["core_value_max"]}

Zero-volume rows: {sp500_summary["zero_volume_rows"]}

Interpretation:

The S&P 500 data behaves like a trading-day time series. Missing calendar dates are expected because the stock market is closed on weekends and holidays. Zero-volume rows appear in older historical observations and should be documented, especially if volume is used in analysis.

## Cross-Dataset Temporal Alignment

FRED unique dates: {alignment.get("fred_unique_dates")}

S&P 500 unique dates: {alignment.get("sp500_unique_dates")}

Overlapping raw dates: {alignment.get("overlapping_dates")}

FRED-only dates: {alignment.get("fred_only_dates")}

S&P 500-only dates: {alignment.get("sp500_only_dates")}

S&P 500 dates before FRED starts: {alignment.get("sp500_dates_before_fred_start")}

Overlap range: {alignment.get("overlap_date_min")} to {alignment.get("overlap_date_max")}

Interpretation:

The main quality and curation challenge is temporal alignment. The FRED dataset is a calendar-day interest-rate series, while the S&P 500 dataset is a trading-day market series. A shared `date` column exists, but the two datasets do not represent the same observation schedule. This issue should guide the later cleaning and integration scripts.

## Implications for Cleaning

The quality profile suggests the following cleaning needs:

1. Standardize date parsing in both datasets.
2. Convert numeric columns to stable numeric types.
3. Rename columns to clear analysis-ready names.
4. Preserve raw files without manual editing.
5. Document zero-volume observations in S&P 500 data.
6. Avoid treating expected trading-day calendar gaps as ordinary missing data.

## Implications for Integration

The quality profile suggests the following integration strategy:

1. Use `date` as the integration key.
2. Treat S&P 500 trading days as the natural base timeline for daily market-return analysis.
3. Do not invent stock market observations for weekends or holidays.
4. Clearly document FRED-only dates as expected non-trading-day mismatch rather than data collection failure.
5. Restrict final integrated analysis to the overlapping date range.
"""

    DATA_QUALITY_PROFILE_DOC_PATH.write_text(content, encoding="utf-8")
    return DATA_QUALITY_PROFILE_DOC_PATH


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def main() -> None:
    """Run raw data quality profiling."""

    print("=" * 72)
    print("IS 477 Final Project: Raw Data Quality Profiling")
    print("=" * 72)

    ensure_output_directories()

    print("Checking required raw files...")
    require_file(FRED_RAW_PATH)
    require_file(SP500_RAW_PATH)

    if CHECKSUMS_PATH.exists():
        print("Checksum file found.")
    else:
        print("Warning: checksum file not found. Checksum verification will be limited.")

    print("\nLoading raw datasets...")
    fred_df, sp500_df = load_raw_datasets()
    print(f"Loaded FRED raw data: {len(fred_df)} rows")
    print(f"Loaded S&P 500 raw data: {len(sp500_df)} rows")

    print("\nVerifying raw-file checksums...")
    checksum_df = verify_checksums()
    print(f"Saved: {relative(CHECKSUM_VERIFICATION_PATH)}")

    print("\nBuilding schema summaries...")
    schema_df = pd.concat(
        [
            build_schema_summary(
                "Federal Funds Effective Rate",
                FRED_RAW_PATH,
                fred_df,
            ),
            build_schema_summary(
                "S&P 500 Index",
                SP500_RAW_PATH,
                sp500_df,
            ),
        ],
        ignore_index=True,
    )
    schema_df.to_csv(SCHEMA_SUMMARY_PATH, index=False)
    print(f"Saved: {relative(SCHEMA_SUMMARY_PATH)}")

    print("\nBuilding missingness summaries...")
    missingness_df = pd.concat(
        [
            build_missingness_summary(
                "Federal Funds Effective Rate",
                FRED_RAW_PATH,
                fred_df,
            ),
            build_missingness_summary(
                "S&P 500 Index",
                SP500_RAW_PATH,
                sp500_df,
            ),
        ],
        ignore_index=True,
    )
    missingness_df.to_csv(MISSINGNESS_SUMMARY_PATH, index=False)
    print(f"Saved: {relative(MISSINGNESS_SUMMARY_PATH)}")

    print("\nProfiling dataset-level quality...")
    fred_summary = profile_fred(fred_df)
    sp500_summary = profile_sp500(sp500_df)

    quality_summary_df = pd.DataFrame([fred_summary, sp500_summary])
    quality_summary_df.to_csv(DATA_QUALITY_SUMMARY_PATH, index=False)
    print(f"Saved: {relative(DATA_QUALITY_SUMMARY_PATH)}")

    print("\nProfiling date coverage...")
    date_coverage_df = pd.DataFrame(
        [
            build_date_coverage_summary(
                "Federal Funds Effective Rate",
                FRED_RAW_PATH,
                fred_df,
                "calendar-day daily",
            ),
            build_date_coverage_summary(
                "S&P 500 Index",
                SP500_RAW_PATH,
                sp500_df,
                "trading-day daily",
            ),
        ]
    )
    date_coverage_df.to_csv(DATE_COVERAGE_SUMMARY_PATH, index=False)
    print(f"Saved: {relative(DATE_COVERAGE_SUMMARY_PATH)}")

    print("\nProfiling cross-dataset temporal alignment...")
    alignment_df = build_temporal_alignment_profile(fred_df, sp500_df)
    print(f"Saved: {relative(TEMPORAL_ALIGNMENT_PROFILE_PATH)}")

    print("\nWriting human-readable quality profile...")
    profile_doc = write_quality_profile_doc(
        fred_summary=fred_summary,
        sp500_summary=sp500_summary,
        alignment_df=alignment_df,
        checksum_df=checksum_df,
    )
    print(f"Saved: {relative(profile_doc)}")

    print("\nRaw data quality profiling complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()