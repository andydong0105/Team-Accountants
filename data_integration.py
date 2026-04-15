"""
data_integration.py

Integrate the Federal Funds Effective Rate dataset (FRED) and the
S&P 500 dataset (Yahoo Finance) into a unified time-series dataset.

This script:
1. Loads raw source files
2. Standardizes schema and data types
3. Restricts both datasets to overlapping temporal coverage
4. Uses S&P 500 trading days as the reference relation
5. Performs record-level integration on the date attribute
6. Creates derived variables for downstream analysis
7. Writes the integrated dataset and a short integration summary

Expected inputs:
- data/raw/fred_dff.csv
- data/raw/sp500_raw.csv

Outputs:
- data/processed/integrated_fred_sp500.csv
- docs/INTEGRATION_SUMMARY.md
"""

from pathlib import Path
import pandas as pd


# -----------------------------
# Paths
# -----------------------------
PROJECT_ROOT = Path(".")
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

FRED_PATH = RAW_DIR / "fred_dff.csv"
SP500_PATH = RAW_DIR / "sp500_raw.csv"

OUTPUT_PATH = PROCESSED_DIR / "integrated_fred_sp500.csv"
SUMMARY_PATH = DOCS_DIR / "INTEGRATION_SUMMARY.md"


# -----------------------------
# Load and validate inputs
# -----------------------------
def validate_input_files() -> None:
    """Ensure required raw files exist before integration."""
    missing = []
    for path in [FRED_PATH, SP500_PATH]:
        if not path.exists():
            missing.append(path.as_posix())

    if missing:
        raise FileNotFoundError(
            "Missing required input files:\n- " + "\n- ".join(missing)
        )


def load_fred() -> pd.DataFrame:
    """
    Load and standardize the FRED Federal Funds Rate dataset.

    Expected source columns include:
    - date
    - value
    - realtime_start
    - realtime_end
    """
    df = pd.read_csv(FRED_PATH)

    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError("FRED file must contain 'date' and 'value' columns.")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["federal_funds_rate"] = pd.to_numeric(df["value"], errors="coerce")

    # Keep only the variables needed for the integrated schema
    df = df[["date", "federal_funds_rate"]].copy()

    # Remove rows with invalid dates
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # Ensure one row per date
    df = df.drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)

    return df


def flatten_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flatten possible multi-level columns from yfinance exports.
    Example:
      ('Close', '^GSPC') -> 'Close'
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    return df


def load_sp500() -> pd.DataFrame:
    """
    Load and standardize the S&P 500 dataset.

    Expected source columns include:
    - Date
    - Close
    - Open
    - High
    - Low
    - Volume
    """
    df = pd.read_csv(SP500_PATH)
    df = flatten_yfinance_columns(df)

    if "Date" not in df.columns:
        raise ValueError("S&P 500 file must contain a 'Date' column.")

    required_price_cols = ["Close", "Open", "High", "Low", "Volume"]
    missing_cols = [col for col in required_price_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            "S&P 500 file is missing required columns: " + ", ".join(missing_cols)
        )

    df["date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["sp500_close"] = pd.to_numeric(df["Close"], errors="coerce")
    df["sp500_open"] = pd.to_numeric(df["Open"], errors="coerce")
    df["sp500_high"] = pd.to_numeric(df["High"], errors="coerce")
    df["sp500_low"] = pd.to_numeric(df["Low"], errors="coerce")
    df["sp500_volume"] = pd.to_numeric(df["Volume"], errors="coerce")

    df = df[
        [
            "date",
            "sp500_open",
            "sp500_high",
            "sp500_low",
            "sp500_close",
            "sp500_volume",
        ]
    ].copy()

    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    df = df.drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)

    return df


# -----------------------------
# Integration logic
# -----------------------------
def restrict_to_overlapping_period(
    fred_df: pd.DataFrame, sp500_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp, pd.Timestamp]:
    """
    Restrict both datasets to overlapping temporal coverage.
    """
    start_date = max(fred_df["date"].min(), sp500_df["date"].min())
    end_date = min(fred_df["date"].max(), sp500_df["date"].max())

    fred_overlap = fred_df[
        (fred_df["date"] >= start_date) & (fred_df["date"] <= end_date)
    ].copy()

    sp500_overlap = sp500_df[
        (sp500_df["date"] >= start_date) & (sp500_df["date"] <= end_date)
    ].copy()

    return fred_overlap, sp500_overlap, start_date, end_date


def integrate_datasets(fred_df: pd.DataFrame, sp500_df: pd.DataFrame) -> pd.DataFrame:
    """
    Integrate using S&P 500 trading days as the reference relation.

    Design choice:
    - One row per trading day
    - Left join FRED rates onto S&P 500 dates
    - Non-trading-day FRED observations are excluded from the final integrated dataset
    """
    integrated = sp500_df.merge(
        fred_df,
        on="date",
        how="left",
        validate="one_to_one",
    )

    # Derived variables for downstream analysis
    integrated["sp500_daily_return"] = integrated["sp500_close"].pct_change()
    integrated["federal_funds_rate_change"] = integrated["federal_funds_rate"].diff()

    # Reorder columns into a clearer integrated schema
    integrated = integrated[
        [
            "date",
            "sp500_open",
            "sp500_high",
            "sp500_low",
            "sp500_close",
            "sp500_volume",
            "federal_funds_rate",
            "sp500_daily_return",
            "federal_funds_rate_change",
        ]
    ].copy()

    return integrated


# -----------------------------
# Documentation
# -----------------------------
def write_integration_summary(
    fred_original_rows: int,
    sp500_original_rows: int,
    fred_overlap_rows: int,
    sp500_overlap_rows: int,
    integrated_rows: int,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    missing_rate_rows: int,
) -> None:
    """Write a short markdown summary of the integration process."""
    summary = f"""# Integration Summary

## Sources

- `data/raw/fred_dff.csv`
- `data/raw/sp500_raw.csv`

## Integration strategy

This project uses the S&P 500 dataset as the reference relation and performs a left join on the shared temporal attribute `date`.

The integration workflow includes:
1. Schema matching (`date` in FRED and `Date` in Yahoo Finance)
2. Schema mapping to a common tabular structure
3. Restriction to overlapping temporal coverage
4. Record-level integration on trading-day observations

## Temporal coverage

- Overlapping start date: {start_date.date()}
- Overlapping end date: {end_date.date()}

## Row counts

- Original FRED rows: {fred_original_rows}
- Original S&P 500 rows: {sp500_original_rows}
- FRED rows in overlapping period: {fred_overlap_rows}
- S&P 500 rows in overlapping period: {sp500_overlap_rows}
- Integrated rows: {integrated_rows}

## Completeness note

Because the final integrated dataset uses trading days as the observation unit, non-trading-day Federal Funds Rate observations are excluded from the final table.

Rows with missing federal funds rate after integration: {missing_rate_rows}

## Output

- `data/processed/integrated_fred_sp500.csv`
"""
    SUMMARY_PATH.write_text(summary, encoding="utf-8")


# -----------------------------
# Main workflow
# -----------------------------
def main() -> None:
    print("Starting data integration...")

    validate_input_files()

    fred_df = load_fred()
    sp500_df = load_sp500()

    fred_original_rows = len(fred_df)
    sp500_original_rows = len(sp500_df)

    fred_overlap, sp500_overlap, start_date, end_date = restrict_to_overlapping_period(
        fred_df, sp500_df
    )

    integrated = integrate_datasets(fred_overlap, sp500_overlap)

    # Save output
    integrated.to_csv(OUTPUT_PATH, index=False)

    missing_rate_rows = integrated["federal_funds_rate"].isna().sum()

    write_integration_summary(
        fred_original_rows=fred_original_rows,
        sp500_original_rows=sp500_original_rows,
        fred_overlap_rows=len(fred_overlap),
        sp500_overlap_rows=len(sp500_overlap),
        integrated_rows=len(integrated),
        start_date=start_date,
        end_date=end_date,
        missing_rate_rows=missing_rate_rows,
    )

    print(f"Saved integrated dataset to: {OUTPUT_PATH}")
    print(f"Saved integration summary to: {SUMMARY_PATH}")
    print("Data integration complete.")


if __name__ == "__main__":
    main()