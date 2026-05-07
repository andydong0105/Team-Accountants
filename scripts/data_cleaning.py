"""
data_cleaning.py

Clean and standardize raw datasets for the IS 477 final project.

Workflow position:
    data_quality.py -> data_cleaning.py -> data_integration.py

This script is designed to run AFTER raw data quality profiling and BEFORE
data integration. It uses the raw data quality results to guide cleaning
decisions, but it does not depend on any integrated or previously cleaned files.

Raw inputs:
- data/raw/fred_dff.csv
- data/raw/sp500_raw.csv

Clean outputs:
- data/processed/fred_dff_clean.csv
- data/processed/sp500_clean.csv

Documentation and summary outputs:
- results/cleaning_summary.csv
- results/cleaning_decisions.csv
- docs/cleaning_provenance.md

Cleaning decisions based on data quality profiling:
1. Preserve raw files without manual editing.
2. Standardize date parsing in both datasets.
3. Convert numeric columns to stable numeric types.
4. Rename columns to clear analysis-ready names.
5. Remove invalid dates, missing core values, and duplicate dates if present.
6. Retain FRED weekend observations because FRED is a calendar-day series.
7. Retain S&P 500 zero-volume rows because price fields remain valid and
   volume is not a core analysis variable.
8. Do not impute missing trading days or create stock market observations for
   weekends/holidays. Temporal alignment is handled later in integration.

Usage from repository root:
    python scripts/data_cleaning.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
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
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
DOCS_DIR = PROJECT_ROOT / "docs"

FRED_RAW_PATH = RAW_DIR / "fred_dff.csv"
SP500_RAW_PATH = RAW_DIR / "sp500_raw.csv"

FRED_CLEAN_PATH = PROCESSED_DIR / "fred_dff_clean.csv"
SP500_CLEAN_PATH = PROCESSED_DIR / "sp500_clean.csv"

CLEANING_SUMMARY_PATH = RESULTS_DIR / "cleaning_summary.csv"
CLEANING_DECISIONS_PATH = RESULTS_DIR / "cleaning_decisions.csv"
CLEANING_PROVENANCE_PATH = DOCS_DIR / "cleaning_provenance.md"


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
    """Create output directories if they do not already exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def require_file(path: Path) -> None:
    """Raise a clear error if an expected input file is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file is missing: {relative(path)}\n"
            "Run scripts/acquire_data.py before running scripts/data_cleaning.py."
        )


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names to lowercase snake_case.

    This handles source columns such as Date, Adj Close, and already-standardized
    names such as adj_close.
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


def parse_date_column(df: pd.DataFrame, column: str = "date") -> pd.DataFrame:
    """Parse a date column as pandas datetime."""
    if column not in df.columns:
        raise ValueError(f"Expected date column not found: {column}")

    df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def format_date_column(df: pd.DataFrame, column: str = "date") -> pd.DataFrame:
    """Format a parsed datetime column as ISO YYYY-MM-DD strings."""
    df[column] = pd.to_datetime(df[column], errors="coerce").dt.strftime("%Y-%m-%d")
    return df


def count_duplicate_dates(df: pd.DataFrame) -> int:
    """Count duplicate dates in a dataframe."""
    if "date" not in df.columns:
        return 0

    return int(df["date"].duplicated().sum())


def count_invalid_dates(df: pd.DataFrame) -> int:
    """Count invalid dates in a dataframe."""
    if "date" not in df.columns:
        return 0

    return int(pd.to_datetime(df["date"], errors="coerce").isna().sum())


def count_rows_missing_any(df: pd.DataFrame, columns: list[str]) -> int:
    """Count rows missing at least one value in the selected columns."""
    existing_columns = [column for column in columns if column in df.columns]

    if not existing_columns:
        return 0

    return int(df[existing_columns].isna().any(axis=1).sum())


def count_non_numeric_values(df: pd.DataFrame, columns: list[str]) -> int:
    """
    Count non-numeric values across selected columns.

    Missing raw values are not double-counted as non-numeric values.
    """
    total = 0

    for column in columns:
        if column not in df.columns:
            continue

        converted = pd.to_numeric(df[column], errors="coerce")
        original_missing = df[column].isna()
        non_numeric = converted.isna() & ~original_missing
        total += int(non_numeric.sum())

    return total


def date_range_string(df: pd.DataFrame) -> tuple[str, str]:
    """Return min and max date as ISO strings."""
    parsed_dates = pd.to_datetime(df["date"], errors="coerce").dropna()

    if parsed_dates.empty:
        return "", ""

    return (
        parsed_dates.min().strftime("%Y-%m-%d"),
        parsed_dates.max().strftime("%Y-%m-%d"),
    )


# -----------------------------------------------------------------------------
# FRED cleaning
# -----------------------------------------------------------------------------

def clean_fred() -> tuple[pd.DataFrame, dict]:
    """
    Clean Federal Funds Effective Rate raw data.

    Raw expected columns:
    - realtime_start
    - realtime_end
    - date
    - value

    Clean output columns:
    - date
    - federal_funds_rate
    """
    require_file(FRED_RAW_PATH)

    raw_df = pd.read_csv(FRED_RAW_PATH)
    raw_df = standardize_column_names(raw_df)

    raw_rows = len(raw_df)
    raw_columns = list(raw_df.columns)

    required_columns = ["date", "value"]
    missing_required_columns = [
        column for column in required_columns if column not in raw_df.columns
    ]

    if missing_required_columns:
        raise ValueError(
            "FRED raw data is missing required columns: "
            f"{missing_required_columns}"
        )

    before_invalid_dates = count_invalid_dates(raw_df)
    before_duplicate_dates = count_duplicate_dates(raw_df)
    before_missing_core = count_rows_missing_any(raw_df, ["date", "value"])
    before_non_numeric_core = count_non_numeric_values(raw_df, ["value"])

    cleaned_df = raw_df.copy()

    cleaned_df = cleaned_df.rename(columns={"value": "federal_funds_rate"})
    cleaned_df = parse_date_column(cleaned_df, "date")

    cleaned_df["federal_funds_rate"] = pd.to_numeric(
        cleaned_df["federal_funds_rate"],
        errors="coerce",
    )

    cleaned_df = cleaned_df.dropna(subset=["date", "federal_funds_rate"])
    cleaned_df = cleaned_df.sort_values("date")
    cleaned_df = cleaned_df.drop_duplicates(subset=["date"], keep="last")

    # Retain only analysis-relevant fields. The realtime fields are preserved in
    # the raw file and documented, but are not needed for integration.
    cleaned_df = cleaned_df[
        [
            "date",
            "federal_funds_rate",
        ]
    ]

    cleaned_df = format_date_column(cleaned_df, "date")
    cleaned_df.to_csv(FRED_CLEAN_PATH, index=False)

    clean_start_date, clean_end_date = date_range_string(cleaned_df)

    summary = {
        "dataset": "Federal Funds Effective Rate",
        "input_file": relative(FRED_RAW_PATH),
        "output_file": relative(FRED_CLEAN_PATH),
        "raw_rows": raw_rows,
        "clean_rows": len(cleaned_df),
        "rows_removed": raw_rows - len(cleaned_df),
        "raw_columns": "; ".join(raw_columns),
        "clean_columns": "; ".join(cleaned_df.columns),
        "invalid_date_rows_before_cleaning": before_invalid_dates,
        "duplicate_date_rows_before_cleaning": before_duplicate_dates,
        "missing_core_value_rows_before_cleaning": before_missing_core,
        "non_numeric_core_value_rows_before_cleaning": before_non_numeric_core,
        "duplicate_date_rows_after_cleaning": count_duplicate_dates(cleaned_df),
        "invalid_date_rows_after_cleaning": count_invalid_dates(cleaned_df),
        "missing_core_value_rows_after_cleaning": count_rows_missing_any(
            cleaned_df,
            ["date", "federal_funds_rate"],
        ),
        "start_date_after_cleaning": clean_start_date,
        "end_date_after_cleaning": clean_end_date,
        "cleaning_action": (
            "Renamed value to federal_funds_rate; parsed date; converted "
            "federal_funds_rate to numeric; removed invalid or missing core "
            "records if present; removed duplicate dates if present; retained "
            "calendar-day observations, including weekends."
        ),
        "quality_profile_guidance": (
            "Data quality profiling showed that FRED DFF is a complete "
            "calendar-day series with no invalid dates, no duplicate dates, "
            "and no missing core values. Weekend observations are expected "
            "and are retained."
        ),
    }

    return cleaned_df, summary


# -----------------------------------------------------------------------------
# S&P 500 cleaning
# -----------------------------------------------------------------------------

def simplify_sp500_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize and simplify possible yfinance S&P 500 column names.

    Depending on yfinance version, columns may appear as:
    - close
    - close_^gspc
    - close__gspc
    - Close
    """
    df = standardize_column_names(df)

    rename_map: dict[str, str] = {}

    for column in df.columns:
        simplified = column
        simplified = simplified.replace("_^gspc", "")
        simplified = simplified.replace("__gspc", "")
        simplified = simplified.replace("_gspc", "")

        if simplified == "date":
            rename_map[column] = "date"
        elif simplified == "open":
            rename_map[column] = "sp500_open"
        elif simplified == "high":
            rename_map[column] = "sp500_high"
        elif simplified == "low":
            rename_map[column] = "sp500_low"
        elif simplified == "close":
            rename_map[column] = "sp500_close"
        elif simplified == "adj_close":
            rename_map[column] = "sp500_adj_close"
        elif simplified == "volume":
            rename_map[column] = "sp500_volume"

    return df.rename(columns=rename_map)


def clean_sp500() -> tuple[pd.DataFrame, dict]:
    """
    Clean S&P 500 raw data.

    Raw expected columns:
    - date
    - adj_close
    - close
    - high
    - low
    - open
    - volume

    Clean output columns:
    - date
    - sp500_open
    - sp500_high
    - sp500_low
    - sp500_close
    - sp500_adj_close
    - sp500_volume
    - sp500_zero_volume_flag
    """
    require_file(SP500_RAW_PATH)

    raw_df = pd.read_csv(SP500_RAW_PATH)
    raw_rows = len(raw_df)
    raw_columns = list(raw_df.columns)

    standardized_df = simplify_sp500_column_names(raw_df)

    required_columns = [
        "date",
        "sp500_open",
        "sp500_high",
        "sp500_low",
        "sp500_close",
        "sp500_volume",
    ]

    missing_required_columns = [
        column for column in required_columns if column not in standardized_df.columns
    ]

    if missing_required_columns:
        raise ValueError(
            "S&P 500 raw data is missing required columns after column-name "
            f"standardization: {missing_required_columns}"
        )

    if "sp500_adj_close" not in standardized_df.columns:
        standardized_df["sp500_adj_close"] = standardized_df["sp500_close"]

    numeric_columns = [
        "sp500_open",
        "sp500_high",
        "sp500_low",
        "sp500_close",
        "sp500_adj_close",
        "sp500_volume",
    ]

    before_invalid_dates = count_invalid_dates(standardized_df)
    before_duplicate_dates = count_duplicate_dates(standardized_df)
    before_missing_core = count_rows_missing_any(
        standardized_df,
        ["date"] + numeric_columns,
    )
    before_non_numeric_core = count_non_numeric_values(
        standardized_df,
        numeric_columns,
    )

    cleaned_df = standardized_df.copy()
    cleaned_df = parse_date_column(cleaned_df, "date")

    for column in numeric_columns:
        cleaned_df[column] = pd.to_numeric(cleaned_df[column], errors="coerce")

    # Basic plausibility checks before dropping invalid rows.
    before_high_less_than_low = int(
        (cleaned_df["sp500_high"] < cleaned_df["sp500_low"]).sum()
    )
    before_open_outside_range = int(
        (
            (cleaned_df["sp500_open"] > cleaned_df["sp500_high"])
            | (cleaned_df["sp500_open"] < cleaned_df["sp500_low"])
        ).sum()
    )
    before_close_outside_range = int(
        (
            (cleaned_df["sp500_close"] > cleaned_df["sp500_high"])
            | (cleaned_df["sp500_close"] < cleaned_df["sp500_low"])
        ).sum()
    )
    before_non_positive_close = int((cleaned_df["sp500_close"] <= 0).sum())
    before_negative_volume = int((cleaned_df["sp500_volume"] < 0).sum())
    before_zero_volume = int((cleaned_df["sp500_volume"] == 0).sum())

    cleaned_df = cleaned_df.dropna(subset=["date"] + numeric_columns)
    cleaned_df = cleaned_df.sort_values("date")
    cleaned_df = cleaned_df.drop_duplicates(subset=["date"], keep="last")

    # Do not remove zero-volume observations. The quality profile showed that
    # zero volume appears in older index records; price fields remain useful.
    cleaned_df["sp500_zero_volume_flag"] = (
        cleaned_df["sp500_volume"] == 0
    ).astype(int)

    cleaned_df = cleaned_df[
        [
            "date",
            "sp500_open",
            "sp500_high",
            "sp500_low",
            "sp500_close",
            "sp500_adj_close",
            "sp500_volume",
            "sp500_zero_volume_flag",
        ]
    ]

    cleaned_df = format_date_column(cleaned_df, "date")
    cleaned_df.to_csv(SP500_CLEAN_PATH, index=False)

    clean_start_date, clean_end_date = date_range_string(cleaned_df)

    summary = {
        "dataset": "S&P 500 Index",
        "input_file": relative(SP500_RAW_PATH),
        "output_file": relative(SP500_CLEAN_PATH),
        "raw_rows": raw_rows,
        "clean_rows": len(cleaned_df),
        "rows_removed": raw_rows - len(cleaned_df),
        "raw_columns": "; ".join(raw_columns),
        "clean_columns": "; ".join(cleaned_df.columns),
        "invalid_date_rows_before_cleaning": before_invalid_dates,
        "duplicate_date_rows_before_cleaning": before_duplicate_dates,
        "missing_core_value_rows_before_cleaning": before_missing_core,
        "non_numeric_core_value_rows_before_cleaning": before_non_numeric_core,
        "duplicate_date_rows_after_cleaning": count_duplicate_dates(cleaned_df),
        "invalid_date_rows_after_cleaning": count_invalid_dates(cleaned_df),
        "missing_core_value_rows_after_cleaning": count_rows_missing_any(
            cleaned_df,
            ["date"] + numeric_columns,
        ),
        "start_date_after_cleaning": clean_start_date,
        "end_date_after_cleaning": clean_end_date,
        "high_less_than_low_rows_before_cleaning": before_high_less_than_low,
        "open_outside_high_low_rows_before_cleaning": before_open_outside_range,
        "close_outside_high_low_rows_before_cleaning": before_close_outside_range,
        "non_positive_close_rows_before_cleaning": before_non_positive_close,
        "negative_volume_rows_before_cleaning": before_negative_volume,
        "zero_volume_rows_before_cleaning": before_zero_volume,
        "zero_volume_rows_after_cleaning": int(
            cleaned_df["sp500_zero_volume_flag"].sum()
        ),
        "cleaning_action": (
            "Standardized column names; renamed price and volume fields with "
            "sp500_ prefixes; parsed date; converted price and volume fields "
            "to numeric; removed invalid or missing core records if present; "
            "removed duplicate dates if present; retained zero-volume rows and "
            "added sp500_zero_volume_flag for transparency."
        ),
        "quality_profile_guidance": (
            "Data quality profiling showed that the S&P 500 data is a "
            "trading-day series with no invalid dates, no duplicate dates, "
            "and no missing core values. The profile identified zero-volume "
            "rows in older records, so these rows are retained and flagged "
            "rather than removed."
        ),
    }

    return cleaned_df, summary


# -----------------------------------------------------------------------------
# Cleaning decisions
# -----------------------------------------------------------------------------

def build_cleaning_decisions() -> pd.DataFrame:
    """Create a structured table documenting cleaning decisions."""
    rows = [
        {
            "dataset": "Federal Funds Effective Rate",
            "issue_identified_by_quality_profile": "Calendar-day observations include weekends",
            "cleaning_decision": "Retain weekend observations",
            "reason": (
                "Weekend observations are expected for FRED DFF and are not "
                "data errors. Temporal mismatch is handled during integration."
            ),
            "affects_row_removal": "no",
        },
        {
            "dataset": "Federal Funds Effective Rate",
            "issue_identified_by_quality_profile": "Raw column name value is not analysis-specific",
            "cleaning_decision": "Rename value to federal_funds_rate",
            "reason": "Clear variable names improve readability and downstream documentation.",
            "affects_row_removal": "no",
        },
        {
            "dataset": "Federal Funds Effective Rate",
            "issue_identified_by_quality_profile": "Raw data includes realtime_start and realtime_end columns",
            "cleaning_decision": "Drop realtime fields from cleaned analysis file",
            "reason": (
                "The project analyzes observed rate values by date; realtime "
                "metadata remains preserved in raw files."
            ),
            "affects_row_removal": "no",
        },
        {
            "dataset": "S&P 500 Index",
            "issue_identified_by_quality_profile": "Trading-day series has missing calendar dates",
            "cleaning_decision": "Do not fill missing weekends or market holidays",
            "reason": (
                "Missing calendar days are expected because the stock market is "
                "closed on weekends and holidays. Creating artificial price "
                "records would distort market-return analysis."
            ),
            "affects_row_removal": "no",
        },
        {
            "dataset": "S&P 500 Index",
            "issue_identified_by_quality_profile": "Zero-volume rows in older observations",
            "cleaning_decision": "Retain zero-volume rows and add sp500_zero_volume_flag",
            "reason": (
                "The price fields remain useful for index-level analysis and "
                "volume is not the primary research variable."
            ),
            "affects_row_removal": "no",
        },
        {
            "dataset": "S&P 500 Index",
            "issue_identified_by_quality_profile": "Column names need analysis-ready format",
            "cleaning_decision": "Rename columns with sp500_ prefixes",
            "reason": (
                "Prefixed names prevent ambiguity after integration with the "
                "FRED dataset."
            ),
            "affects_row_removal": "no",
        },
        {
            "dataset": "Both datasets",
            "issue_identified_by_quality_profile": "Need stable data types for integration",
            "cleaning_decision": "Parse dates and convert numeric fields",
            "reason": (
                "Stable date and numeric types are required for reliable "
                "quality assessment, integration, and analysis."
            ),
            "affects_row_removal": "only if invalid values exist",
        },
        {
            "dataset": "Both datasets",
            "issue_identified_by_quality_profile": "Potential invalid, missing, or duplicate core records",
            "cleaning_decision": "Remove invalid/missing core rows and duplicate dates if present",
            "reason": (
                "A one-row-per-date structure is necessary for later time-series "
                "integration."
            ),
            "affects_row_removal": "only if such rows exist",
        },
    ]

    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Documentation outputs
# -----------------------------------------------------------------------------

def write_cleaning_summary(summaries: list[dict]) -> Path:
    """Write a machine-readable cleaning summary CSV."""
    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv(CLEANING_SUMMARY_PATH, index=False)
    return CLEANING_SUMMARY_PATH


def write_cleaning_decisions() -> Path:
    """Write a machine-readable cleaning decisions CSV."""
    decisions_df = build_cleaning_decisions()
    decisions_df.to_csv(CLEANING_DECISIONS_PATH, index=False)
    return CLEANING_DECISIONS_PATH


def write_cleaning_provenance(
    fred_summary: dict,
    sp500_summary: dict,
) -> Path:
    """Write human-readable cleaning provenance documentation."""

    content = f"""# Cleaning Provenance

Generated by `scripts/data_cleaning.py` on `{utc_now_iso()}`.

## Scope

This document explains how raw source data were transformed into cleaned datasets for later integration and analysis. This cleaning step runs after raw data quality profiling and before data integration.

The script reads only files from `data/raw/` and writes cleaned outputs to `data/processed/`. It does not use previously integrated files.

## Input Files

- `{relative(FRED_RAW_PATH)}`
- `{relative(SP500_RAW_PATH)}`

## Output Files

- `{relative(FRED_CLEAN_PATH)}`
- `{relative(SP500_CLEAN_PATH)}`
- `{relative(CLEANING_SUMMARY_PATH)}`
- `{relative(CLEANING_DECISIONS_PATH)}`

## Quality Profile Findings Used

The raw data quality profile showed that the FRED dataset is a calendar-day series with {fred_summary["raw_rows"]:,} rows, {fred_summary["duplicate_date_rows_before_cleaning"]} duplicate dates, {fred_summary["invalid_date_rows_before_cleaning"]} invalid dates, and {fred_summary["missing_core_value_rows_before_cleaning"]} missing core value rows. FRED weekend observations are expected because the series is reported on a calendar-day basis.

The raw data quality profile showed that the S&P 500 dataset is a trading-day series with {sp500_summary["raw_rows"]:,} rows, {sp500_summary["duplicate_date_rows_before_cleaning"]} duplicate dates, {sp500_summary["invalid_date_rows_before_cleaning"]} invalid dates, and {sp500_summary["missing_core_value_rows_before_cleaning"]} missing core value rows. It also showed {sp500_summary["zero_volume_rows_before_cleaning"]:,} zero-volume rows in older records.

The main curation issue identified by profiling is not a severe raw-data defect. Instead, the main issue is temporal alignment: FRED is reported on calendar days, while the S&P 500 is observed on trading days.

## Federal Funds Effective Rate Cleaning

Source file: `{fred_summary["input_file"]}`

Output file: `{fred_summary["output_file"]}`

Raw rows: {fred_summary["raw_rows"]}

Clean rows: {fred_summary["clean_rows"]}

Rows removed: {fred_summary["rows_removed"]}

Date range after cleaning: {fred_summary["start_date_after_cleaning"]} to {fred_summary["end_date_after_cleaning"]}

Cleaning operations:

1. Standardized column names to lowercase snake_case.
2. Renamed `value` to `federal_funds_rate`.
3. Parsed `date` as a date field.
4. Converted `federal_funds_rate` to numeric.
5. Removed invalid dates, missing core values, and duplicate dates if present.
6. Retained calendar-day observations, including weekends.
7. Dropped `realtime_start` and `realtime_end` from the cleaned analysis file because those fields are not needed for date-based integration. They remain preserved in the raw file.

Quality issues addressed:

- Invalid date rows before cleaning: {fred_summary["invalid_date_rows_before_cleaning"]}
- Missing core value rows before cleaning: {fred_summary["missing_core_value_rows_before_cleaning"]}
- Non-numeric core value rows before cleaning: {fred_summary["non_numeric_core_value_rows_before_cleaning"]}
- Duplicate date rows before cleaning: {fred_summary["duplicate_date_rows_before_cleaning"]}
- Duplicate date rows after cleaning: {fred_summary["duplicate_date_rows_after_cleaning"]}

## S&P 500 Cleaning

Source file: `{sp500_summary["input_file"]}`

Output file: `{sp500_summary["output_file"]}`

Raw rows: {sp500_summary["raw_rows"]}

Clean rows: {sp500_summary["clean_rows"]}

Rows removed: {sp500_summary["rows_removed"]}

Date range after cleaning: {sp500_summary["start_date_after_cleaning"]} to {sp500_summary["end_date_after_cleaning"]}

Cleaning operations:

1. Standardized column names to lowercase snake_case.
2. Renamed price and volume fields with clear `sp500_` prefixes.
3. Parsed `date` as a date field.
4. Converted price and volume fields to numeric.
5. Removed invalid dates, missing core values, and duplicate dates if present.
6. Retained zero-volume rows and added `sp500_zero_volume_flag`.
7. Did not fill missing calendar dates because those gaps reflect weekends and market holidays.

Quality issues addressed:

- Invalid date rows before cleaning: {sp500_summary["invalid_date_rows_before_cleaning"]}
- Missing core value rows before cleaning: {sp500_summary["missing_core_value_rows_before_cleaning"]}
- Non-numeric core value rows before cleaning: {sp500_summary["non_numeric_core_value_rows_before_cleaning"]}
- Duplicate date rows before cleaning: {sp500_summary["duplicate_date_rows_before_cleaning"]}
- Duplicate date rows after cleaning: {sp500_summary["duplicate_date_rows_after_cleaning"]}
- Zero-volume rows before cleaning: {sp500_summary["zero_volume_rows_before_cleaning"]}
- Zero-volume rows after cleaning: {sp500_summary["zero_volume_rows_after_cleaning"]}

## Imputation Policy

No imputation is performed in this cleaning step. The project does not fill S&P 500 non-trading days, does not invent stock market observations for weekends or holidays, and does not forward-fill market prices. Temporal alignment is handled later in the integration step.

## Relationship to Integration

The cleaned datasets are prepared for date-based integration:

- `fred_dff_clean.csv` has one row per calendar date.
- `sp500_clean.csv` has one row per trading date.
- Both files use the shared `date` field in ISO format.
- The later integration step should treat S&P 500 trading days as the natural base timeline and attach the corresponding Federal Funds Effective Rate for those dates.
"""

    CLEANING_PROVENANCE_PATH.write_text(content, encoding="utf-8")
    return CLEANING_PROVENANCE_PATH


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def main() -> None:
    """Run the data cleaning workflow."""

    print("=" * 72)
    print("IS 477 Final Project: Data Cleaning")
    print("=" * 72)

    ensure_output_directories()

    print("Cleaning Federal Funds Effective Rate data...")
    fred_clean, fred_summary = clean_fred()
    print(f"Saved: {relative(FRED_CLEAN_PATH)}")
    print(f"Rows: {fred_summary['raw_rows']} raw -> {fred_summary['clean_rows']} clean")

    print("\nCleaning S&P 500 data...")
    sp500_clean, sp500_summary = clean_sp500()
    print(f"Saved: {relative(SP500_CLEAN_PATH)}")
    print(f"Rows: {sp500_summary['raw_rows']} raw -> {sp500_summary['clean_rows']} clean")

    print("\nWriting cleaning summary...")
    summary_path = write_cleaning_summary([fred_summary, sp500_summary])
    print(f"Saved: {relative(summary_path)}")

    print("\nWriting cleaning decisions...")
    decisions_path = write_cleaning_decisions()
    print(f"Saved: {relative(decisions_path)}")

    print("\nWriting cleaning provenance documentation...")
    provenance_path = write_cleaning_provenance(
        fred_summary=fred_summary,
        sp500_summary=sp500_summary,
    )
    print(f"Saved: {relative(provenance_path)}")

    print("\nData cleaning complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()