"""
data_integration.py

Integrate cleaned FRED Federal Funds Effective Rate data with cleaned S&P 500
market data for the IS 477 final project.

Workflow position:
    data_quality.py -> data_cleaning.py -> data_integration.py

This script reads only cleaned datasets:

- data/processed/fred_dff_clean.csv
- data/processed/sp500_clean.csv

It produces:

- data/processed/integrated_fred_sp500.csv
- results/integration_summary.csv
- results/integration_quality_checks.csv
- docs/INTEGRATION_SUMMARY.md

Integration strategy:

1. Use date as the integration key.
2. Treat S&P 500 trading days as the base timeline.
3. Restrict the S&P 500 data to the date range covered by FRED DFF.
4. Left-join FRED rates onto S&P 500 trading dates.
5. Do not create stock market observations for weekends or holidays.
6. Do not forward-fill S&P 500 prices.
7. Keep only variables needed for later analysis and visualization.

Final integrated dataset columns:

- date
- sp500_close
- sp500_daily_return
- sp500_log_return
- sp500_zero_volume_flag
- federal_funds_rate
- federal_funds_rate_change
- federal_funds_rate_direction

Usage from repository root:
    python scripts/data_integration.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import numpy as np
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

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
DOCS_DIR = PROJECT_ROOT / "docs"

FRED_CLEAN_PATH = PROCESSED_DIR / "fred_dff_clean.csv"
SP500_CLEAN_PATH = PROCESSED_DIR / "sp500_clean.csv"

INTEGRATED_PATH = PROCESSED_DIR / "integrated_fred_sp500.csv"
INTEGRATION_SUMMARY_PATH = RESULTS_DIR / "integration_summary.csv"
INTEGRATION_QUALITY_CHECKS_PATH = RESULTS_DIR / "integration_quality_checks.csv"
INTEGRATION_DOC_PATH = DOCS_DIR / "INTEGRATION_SUMMARY.md"


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
            "Run scripts/data_cleaning.py before running scripts/data_integration.py."
        )


def require_columns(df: pd.DataFrame, columns: list[str], dataset_name: str) -> None:
    """Raise a clear error if expected columns are missing."""
    missing = [column for column in columns if column not in df.columns]

    if missing:
        raise ValueError(
            f"{dataset_name} is missing required columns: {missing}"
        )


def parse_dates(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """Parse date column and check for invalid dates."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    invalid_dates = int(df["date"].isna().sum())
    if invalid_dates > 0:
        raise ValueError(
            f"{dataset_name} contains {invalid_dates} invalid date values "
            "after cleaning. Revisit scripts/data_cleaning.py."
        )

    return df


def count_duplicate_dates(df: pd.DataFrame) -> int:
    """Count duplicate date rows."""
    return int(df["date"].duplicated().sum())


def date_set(df: pd.DataFrame) -> set:
    """Return set of Python date objects from a dataframe date column."""
    return set(pd.to_datetime(df["date"], errors="coerce").dropna().dt.date)


def pct(value: float) -> str:
    """Format a decimal ratio as a percent string."""
    return f"{value * 100:.2f}%"


def direction_from_change(change: float) -> str:
    """Classify federal funds rate change direction."""
    if pd.isna(change):
        return "first_observation"

    if change > 0:
        return "increase"

    if change < 0:
        return "decrease"

    return "no_change"


# -----------------------------------------------------------------------------
# Load cleaned datasets
# -----------------------------------------------------------------------------

def load_cleaned_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load cleaned FRED and S&P 500 datasets."""
    require_file(FRED_CLEAN_PATH)
    require_file(SP500_CLEAN_PATH)

    fred_df = pd.read_csv(FRED_CLEAN_PATH)
    sp500_df = pd.read_csv(SP500_CLEAN_PATH)

    require_columns(
        fred_df,
        ["date", "federal_funds_rate"],
        "FRED cleaned dataset",
    )

    require_columns(
        sp500_df,
        [
            "date",
            "sp500_close",
            "sp500_zero_volume_flag",
        ],
        "S&P 500 cleaned dataset",
    )

    fred_df = parse_dates(fred_df, "FRED cleaned dataset")
    sp500_df = parse_dates(sp500_df, "S&P 500 cleaned dataset")

    fred_df["federal_funds_rate"] = pd.to_numeric(
        fred_df["federal_funds_rate"],
        errors="coerce",
    )

    sp500_df["sp500_close"] = pd.to_numeric(
        sp500_df["sp500_close"],
        errors="coerce",
    )

    sp500_df["sp500_zero_volume_flag"] = pd.to_numeric(
        sp500_df["sp500_zero_volume_flag"],
        errors="coerce",
    ).fillna(0).astype(int)

    return fred_df, sp500_df


# -----------------------------------------------------------------------------
# Integration logic
# -----------------------------------------------------------------------------

def prepare_fred_for_integration(fred_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare FRED data for date-based integration.

    Keeps only variables needed for analysis.
    """
    fred_prepared = fred_df[
        [
            "date",
            "federal_funds_rate",
        ]
    ].copy()

    fred_prepared = fred_prepared.sort_values("date")
    fred_prepared = fred_prepared.drop_duplicates(subset=["date"], keep="last")

    return fred_prepared


def prepare_sp500_for_integration(sp500_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare S&P 500 data for date-based integration.

    Keeps only variables needed for analysis and visualization.
    """
    sp500_prepared = sp500_df[
        [
            "date",
            "sp500_close",
            "sp500_zero_volume_flag",
        ]
    ].copy()

    sp500_prepared = sp500_prepared.sort_values("date")
    sp500_prepared = sp500_prepared.drop_duplicates(subset=["date"], keep="last")

    return sp500_prepared


def restrict_sp500_to_fred_range(
    sp500_df: pd.DataFrame,
    fred_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Restrict S&P 500 observations to the date range covered by FRED.

    This removes S&P 500 observations before FRED DFF begins.
    """
    fred_start = fred_df["date"].min()
    fred_end = fred_df["date"].max()

    restricted = sp500_df[
        (sp500_df["date"] >= fred_start)
        & (sp500_df["date"] <= fred_end)
    ].copy()

    return restricted


def integrate_datasets(
    fred_df: pd.DataFrame,
    sp500_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """
    Integrate cleaned FRED and S&P 500 data.

    Returns:
        integrated dataframe and integration summary dictionary
    """
    fred_prepared = prepare_fred_for_integration(fred_df)
    sp500_prepared = prepare_sp500_for_integration(sp500_df)

    fred_clean_rows = len(fred_prepared)
    sp500_clean_rows = len(sp500_prepared)

    fred_dates = date_set(fred_prepared)
    sp500_dates = date_set(sp500_prepared)

    overlap_dates_before_range_filter = fred_dates & sp500_dates
    fred_only_dates_before_range_filter = fred_dates - sp500_dates
    sp500_only_dates_before_range_filter = sp500_dates - fred_dates

    fred_start = fred_prepared["date"].min()
    fred_end = fred_prepared["date"].max()
    sp500_start = sp500_prepared["date"].min()
    sp500_end = sp500_prepared["date"].max()

    sp500_before_fred_start = sp500_prepared[
        sp500_prepared["date"] < fred_start
    ]

    sp500_after_fred_end = sp500_prepared[
        sp500_prepared["date"] > fred_end
    ]

    sp500_in_fred_range = restrict_sp500_to_fred_range(
        sp500_prepared,
        fred_prepared,
    )

    integrated = sp500_in_fred_range.merge(
        fred_prepared,
        on="date",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    unmatched_after_merge = int((integrated["_merge"] != "both").sum())

    # If unmatched rows exist, they are serious because FRED is expected to have
    # calendar-day observations for all S&P 500 trading dates within the overlap.
    if unmatched_after_merge > 0:
        unmatched_preview = integrated.loc[
            integrated["_merge"] != "both",
            "date",
        ].head(10).dt.strftime("%Y-%m-%d").tolist()

        raise ValueError(
            "Integration produced unmatched S&P 500 trading dates within the "
            f"FRED date range. Unmatched rows: {unmatched_after_merge}. "
            f"Example dates: {unmatched_preview}"
        )

    integrated = integrated.drop(columns=["_merge"])

    integrated = integrated.sort_values("date")

    # Derived analysis variables.
    integrated["sp500_daily_return"] = integrated["sp500_close"].pct_change()

    integrated["sp500_log_return"] = np.log(
        integrated["sp500_close"] / integrated["sp500_close"].shift(1)
    )

    integrated["federal_funds_rate_change"] = integrated[
        "federal_funds_rate"
    ].diff()

    integrated["federal_funds_rate_direction"] = integrated[
        "federal_funds_rate_change"
    ].apply(direction_from_change)

    # Keep a compact analysis-ready schema.
    integrated = integrated[
        [
            "date",
            "sp500_close",
            "sp500_daily_return",
            "sp500_log_return",
            "sp500_zero_volume_flag",
            "federal_funds_rate",
            "federal_funds_rate_change",
            "federal_funds_rate_direction",
        ]
    ]

    integrated["date"] = integrated["date"].dt.strftime("%Y-%m-%d")

    integrated_rows = len(integrated)
    integrated_start_date = integrated["date"].min()
    integrated_end_date = integrated["date"].max()

    missing_rate_after_merge = int(integrated["federal_funds_rate"].isna().sum())
    missing_close_after_merge = int(integrated["sp500_close"].isna().sum())

    first_return_missing = int(integrated["sp500_daily_return"].isna().sum())
    first_rate_change_missing = int(integrated["federal_funds_rate_change"].isna().sum())

    zero_volume_rows_integrated = int(integrated["sp500_zero_volume_flag"].sum())

    summary = {
        "fred_clean_rows": fred_clean_rows,
        "sp500_clean_rows": sp500_clean_rows,
        "fred_date_min": fred_start.strftime("%Y-%m-%d"),
        "fred_date_max": fred_end.strftime("%Y-%m-%d"),
        "sp500_date_min": sp500_start.strftime("%Y-%m-%d"),
        "sp500_date_max": sp500_end.strftime("%Y-%m-%d"),
        "overlap_dates_before_range_filter": len(overlap_dates_before_range_filter),
        "fred_only_dates_before_range_filter": len(fred_only_dates_before_range_filter),
        "sp500_only_dates_before_range_filter": len(sp500_only_dates_before_range_filter),
        "sp500_rows_before_fred_start_removed": len(sp500_before_fred_start),
        "sp500_rows_after_fred_end_removed": len(sp500_after_fred_end),
        "sp500_rows_inside_fred_range": len(sp500_in_fred_range),
        "integrated_rows": integrated_rows,
        "integrated_date_min": integrated_start_date,
        "integrated_date_max": integrated_end_date,
        "unmatched_rows_after_merge": unmatched_after_merge,
        "missing_federal_funds_rate_after_merge": missing_rate_after_merge,
        "missing_sp500_close_after_merge": missing_close_after_merge,
        "missing_sp500_daily_return_rows": first_return_missing,
        "missing_federal_funds_rate_change_rows": first_rate_change_missing,
        "zero_volume_rows_in_integrated_dataset": zero_volume_rows_integrated,
        "sp500_retention_rate_after_fred_range_filter": (
            len(sp500_in_fred_range) / sp500_clean_rows
            if sp500_clean_rows > 0
            else np.nan
        ),
        "merge_success_rate_within_fred_range": (
            1 - unmatched_after_merge / len(sp500_in_fred_range)
            if len(sp500_in_fred_range) > 0
            else np.nan
        ),
    }

    return integrated, summary


# -----------------------------------------------------------------------------
# Output generation
# -----------------------------------------------------------------------------

def write_integration_summary(summary: dict) -> Path:
    """Write machine-readable integration summary."""
    rows = [
        {
            "metric": "fred_clean_rows",
            "value": summary["fred_clean_rows"],
            "notes": "Rows in cleaned FRED DFF dataset before integration.",
        },
        {
            "metric": "sp500_clean_rows",
            "value": summary["sp500_clean_rows"],
            "notes": "Rows in cleaned S&P 500 dataset before integration.",
        },
        {
            "metric": "fred_date_min",
            "value": summary["fred_date_min"],
            "notes": "Earliest cleaned FRED date.",
        },
        {
            "metric": "fred_date_max",
            "value": summary["fred_date_max"],
            "notes": "Latest cleaned FRED date.",
        },
        {
            "metric": "sp500_date_min",
            "value": summary["sp500_date_min"],
            "notes": "Earliest cleaned S&P 500 date.",
        },
        {
            "metric": "sp500_date_max",
            "value": summary["sp500_date_max"],
            "notes": "Latest cleaned S&P 500 date.",
        },
        {
            "metric": "overlap_dates_before_range_filter",
            "value": summary["overlap_dates_before_range_filter"],
            "notes": "Dates present in both cleaned datasets before restricting the S&P 500 range.",
        },
        {
            "metric": "fred_only_dates_before_range_filter",
            "value": summary["fred_only_dates_before_range_filter"],
            "notes": "Cleaned FRED dates not present in the cleaned S&P 500 dataset, mostly non-trading days.",
        },
        {
            "metric": "sp500_only_dates_before_range_filter",
            "value": summary["sp500_only_dates_before_range_filter"],
            "notes": "Cleaned S&P 500 dates not present in FRED, primarily dates before FRED DFF begins.",
        },
        {
            "metric": "sp500_rows_before_fred_start_removed",
            "value": summary["sp500_rows_before_fred_start_removed"],
            "notes": "S&P 500 observations removed because they predate the FRED DFF series.",
        },
        {
            "metric": "sp500_rows_after_fred_end_removed",
            "value": summary["sp500_rows_after_fred_end_removed"],
            "notes": "S&P 500 observations removed because they fall after the FRED DFF series end date.",
        },
        {
            "metric": "sp500_rows_inside_fred_range",
            "value": summary["sp500_rows_inside_fred_range"],
            "notes": "S&P 500 trading-day observations within the FRED date range.",
        },
        {
            "metric": "integrated_rows",
            "value": summary["integrated_rows"],
            "notes": "Rows in the final integrated dataset.",
        },
        {
            "metric": "integrated_date_min",
            "value": summary["integrated_date_min"],
            "notes": "Earliest date in the final integrated dataset.",
        },
        {
            "metric": "integrated_date_max",
            "value": summary["integrated_date_max"],
            "notes": "Latest date in the final integrated dataset.",
        },
        {
            "metric": "unmatched_rows_after_merge",
            "value": summary["unmatched_rows_after_merge"],
            "notes": "S&P 500 trading dates within the FRED range that did not receive a FRED rate.",
        },
        {
            "metric": "missing_federal_funds_rate_after_merge",
            "value": summary["missing_federal_funds_rate_after_merge"],
            "notes": "Missing rate values in the final integrated dataset.",
        },
        {
            "metric": "missing_sp500_close_after_merge",
            "value": summary["missing_sp500_close_after_merge"],
            "notes": "Missing S&P 500 close values in the final integrated dataset.",
        },
        {
            "metric": "missing_sp500_daily_return_rows",
            "value": summary["missing_sp500_daily_return_rows"],
            "notes": "Rows with missing daily return, expected for the first observation.",
        },
        {
            "metric": "missing_federal_funds_rate_change_rows",
            "value": summary["missing_federal_funds_rate_change_rows"],
            "notes": "Rows with missing rate change, expected for the first observation.",
        },
        {
            "metric": "zero_volume_rows_in_integrated_dataset",
            "value": summary["zero_volume_rows_in_integrated_dataset"],
            "notes": "S&P 500 zero-volume rows retained and flagged in the final integrated dataset.",
        },
        {
            "metric": "sp500_retention_rate_after_fred_range_filter",
            "value": summary["sp500_retention_rate_after_fred_range_filter"],
            "notes": "Share of cleaned S&P 500 rows retained after limiting to the FRED date range.",
        },
        {
            "metric": "merge_success_rate_within_fred_range",
            "value": summary["merge_success_rate_within_fred_range"],
            "notes": "Share of in-range S&P 500 rows successfully matched to FRED observations.",
        },
    ]

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(INTEGRATION_SUMMARY_PATH, index=False)

    return INTEGRATION_SUMMARY_PATH


def write_integration_quality_checks(integrated: pd.DataFrame) -> Path:
    """Write quality checks for the final integrated dataset."""
    checks = [
        {
            "check": "integrated_dataset_exists",
            "value": INTEGRATED_PATH.exists(),
            "status": "pass" if INTEGRATED_PATH.exists() else "fail",
            "notes": "Final integrated CSV was written.",
        },
        {
            "check": "row_count_positive",
            "value": len(integrated),
            "status": "pass" if len(integrated) > 0 else "fail",
            "notes": "Integrated dataset should contain at least one row.",
        },
        {
            "check": "duplicate_dates",
            "value": int(integrated["date"].duplicated().sum()),
            "status": "pass" if int(integrated["date"].duplicated().sum()) == 0 else "fail",
            "notes": "Final dataset should have one row per trading date.",
        },
        {
            "check": "missing_sp500_close",
            "value": int(integrated["sp500_close"].isna().sum()),
            "status": "pass" if int(integrated["sp500_close"].isna().sum()) == 0 else "fail",
            "notes": "S&P 500 close is required for analysis.",
        },
        {
            "check": "missing_federal_funds_rate",
            "value": int(integrated["federal_funds_rate"].isna().sum()),
            "status": "pass" if int(integrated["federal_funds_rate"].isna().sum()) == 0 else "fail",
            "notes": "Federal Funds Rate is required for analysis.",
        },
        {
            "check": "missing_sp500_daily_return",
            "value": int(integrated["sp500_daily_return"].isna().sum()),
            "status": (
                "pass"
                if int(integrated["sp500_daily_return"].isna().sum()) == 1
                else "review"
            ),
            "notes": "One missing return is expected for the first observation.",
        },
        {
            "check": "missing_federal_funds_rate_change",
            "value": int(integrated["federal_funds_rate_change"].isna().sum()),
            "status": (
                "pass"
                if int(integrated["federal_funds_rate_change"].isna().sum()) == 1
                else "review"
            ),
            "notes": "One missing rate change is expected for the first observation.",
        },
    ]

    checks_df = pd.DataFrame(checks)
    checks_df.to_csv(INTEGRATION_QUALITY_CHECKS_PATH, index=False)

    return INTEGRATION_QUALITY_CHECKS_PATH


def write_integration_doc(summary: dict) -> Path:
    """Write human-readable integration documentation."""

    content = f"""# Integration Summary

Generated by `scripts/data_integration.py` on `{utc_now_iso()}`.

## Scope

This document describes how the cleaned Federal Funds Effective Rate data and cleaned S&P 500 data were integrated. The integration step runs after data quality profiling and cleaning.

## Input Files

- `{relative(FRED_CLEAN_PATH)}`
- `{relative(SP500_CLEAN_PATH)}`

## Output Files

- `{relative(INTEGRATED_PATH)}`
- `{relative(INTEGRATION_SUMMARY_PATH)}`
- `{relative(INTEGRATION_QUALITY_CHECKS_PATH)}`

## Integration Key

The integration key is `date`.

Both cleaned datasets use ISO-formatted dates. However, the two datasets have different observation schedules:

- FRED DFF is a calendar-day interest-rate series.
- S&P 500 is a trading-day market series.

Therefore, sharing a `date` column does not mean the two datasets have identical temporal coverage.

## Integration Strategy

The final integrated dataset uses S&P 500 trading days as the base timeline. This is appropriate because the later analysis focuses on daily market performance, and the S&P 500 does not have real observations on weekends or market holidays.

Steps:

1. Read cleaned FRED and S&P 500 files.
2. Keep only variables needed for downstream analysis and visualization.
3. Restrict S&P 500 observations to the date range covered by FRED.
4. Left-join FRED rates onto S&P 500 trading dates using `date`.
5. Verify that all in-range S&P 500 trading dates received a FRED rate.
6. Calculate S&P 500 daily returns and log returns.
7. Calculate Federal Funds Rate daily changes and rate-change direction.
8. Save the compact integrated dataset.

## Variables Kept in Final Integrated Dataset

The final integrated dataset keeps only variables needed for later analysis and visualization:

- `date`
- `sp500_close`
- `sp500_daily_return`
- `sp500_log_return`
- `sp500_zero_volume_flag`
- `federal_funds_rate`
- `federal_funds_rate_change`
- `federal_funds_rate_direction`

The original S&P 500 `open`, `high`, `low`, `adjusted close`, and `volume` fields are preserved in cleaned and raw files but are not retained in the integrated dataset because the planned analysis focuses on index closing level, returns, interest-rate level, and rate changes.

## Integration Statistics

Cleaned FRED rows: {summary["fred_clean_rows"]}

Cleaned S&P 500 rows: {summary["sp500_clean_rows"]}

FRED date range: {summary["fred_date_min"]} to {summary["fred_date_max"]}

S&P 500 date range: {summary["sp500_date_min"]} to {summary["sp500_date_max"]}

Overlapping dates before range filtering: {summary["overlap_dates_before_range_filter"]}

FRED-only dates before range filtering: {summary["fred_only_dates_before_range_filter"]}

S&P 500-only dates before range filtering: {summary["sp500_only_dates_before_range_filter"]}

S&P 500 rows removed because they predate FRED: {summary["sp500_rows_before_fred_start_removed"]}

S&P 500 rows after FRED end date removed: {summary["sp500_rows_after_fred_end_removed"]}

S&P 500 rows inside FRED date range: {summary["sp500_rows_inside_fred_range"]}

Final integrated rows: {summary["integrated_rows"]}

Final integrated date range: {summary["integrated_date_min"]} to {summary["integrated_date_max"]}

Unmatched rows after merge: {summary["unmatched_rows_after_merge"]}

Missing Federal Funds Rate values after merge: {summary["missing_federal_funds_rate_after_merge"]}

Missing S&P 500 close values after merge: {summary["missing_sp500_close_after_merge"]}

S&P 500 retention rate after FRED range filter: {summary["sp500_retention_rate_after_fred_range_filter"]:.6f}

Merge success rate within FRED range: {summary["merge_success_rate_within_fred_range"]:.6f}

## Interpretation

The row reduction is expected. The S&P 500 dataset begins in 1927, while FRED DFF begins in 1954. S&P 500 observations before the FRED date range cannot be integrated with Federal Funds Rate values and are excluded from the final integrated dataset.

FRED-only dates are also expected because FRED is a calendar-day series, while the S&P 500 only records trading days. These unmatched FRED dates do not indicate a collection error. They reflect the different temporal structure of the two datasets.

The final integrated dataset contains one row per S&P 500 trading day within the FRED date range. This avoids creating artificial stock market observations for weekends and holidays.
"""

    INTEGRATION_DOC_PATH.write_text(content, encoding="utf-8")
    return INTEGRATION_DOC_PATH


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def main() -> None:
    """Run the data integration workflow."""

    print("=" * 72)
    print("IS 477 Final Project: Data Integration")
    print("=" * 72)

    ensure_output_directories()

    print("Loading cleaned datasets...")
    fred_df, sp500_df = load_cleaned_data()
    print(f"Loaded FRED cleaned data: {len(fred_df)} rows")
    print(f"Loaded S&P 500 cleaned data: {len(sp500_df)} rows")

    print("\nIntegrating datasets...")
    integrated, summary = integrate_datasets(
        fred_df=fred_df,
        sp500_df=sp500_df,
    )

    integrated.to_csv(INTEGRATED_PATH, index=False)
    print(f"Saved: {relative(INTEGRATED_PATH)}")
    print(f"Integrated rows: {summary['integrated_rows']}")
    print(
        "Integrated date range: "
        f"{summary['integrated_date_min']} to {summary['integrated_date_max']}"
    )

    print("\nWriting integration summary...")
    summary_path = write_integration_summary(summary)
    print(f"Saved: {relative(summary_path)}")

    print("\nWriting integration quality checks...")
    checks_path = write_integration_quality_checks(integrated)
    print(f"Saved: {relative(checks_path)}")

    print("\nWriting integration documentation...")
    doc_path = write_integration_doc(summary)
    print(f"Saved: {relative(doc_path)}")

    print("\nData integration complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()