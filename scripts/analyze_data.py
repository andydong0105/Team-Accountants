"""
analyze_data.py

Analyze the integrated FRED Federal Funds Effective Rate and S&P 500 dataset
for the IS 477 final project.

Workflow position:
    data_quality.py -> data_cleaning.py -> data_integration.py -> analyze_data.py

This script reads:

- data/processed/integrated_fred_sp500.csv

It produces:

- results/summary_statistics.csv
- results/correlation_results.csv
- results/rate_change_analysis.csv
- results/period_summary.csv
- results/analysis_findings_summary.csv
- docs/ANALYSIS_SUMMARY.md

The analysis is exploratory. It does not claim that Federal Funds Rate changes
cause S&P 500 returns. Instead, it summarizes observed relationships in the
integrated dataset.

Usage from repository root:
    python scripts/analyze_data.py
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

INTEGRATED_PATH = PROCESSED_DIR / "integrated_fred_sp500.csv"

SUMMARY_STATISTICS_PATH = RESULTS_DIR / "summary_statistics.csv"
CORRELATION_RESULTS_PATH = RESULTS_DIR / "correlation_results.csv"
RATE_CHANGE_ANALYSIS_PATH = RESULTS_DIR / "rate_change_analysis.csv"
PERIOD_SUMMARY_PATH = RESULTS_DIR / "period_summary.csv"
ANALYSIS_FINDINGS_SUMMARY_PATH = RESULTS_DIR / "analysis_findings_summary.csv"
ANALYSIS_DOC_PATH = DOCS_DIR / "ANALYSIS_SUMMARY.md"


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
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def require_file(path: Path) -> None:
    """Raise a clear error if an expected input file is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file is missing: {relative(path)}\n"
            "Run scripts/data_integration.py before running scripts/analyze_data.py."
        )


def require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    """Raise a clear error if required columns are missing."""
    missing = [column for column in columns if column not in df.columns]

    if missing:
        raise ValueError(
            f"Integrated dataset is missing required columns: {missing}"
        )


def safe_float(value: float | int | np.floating | None) -> float | None:
    """Convert numeric values to regular Python floats for cleaner CSV output."""
    if value is None or pd.isna(value):
        return None

    return float(value)


def percent(value: float | int | np.floating | None) -> float | None:
    """Convert a decimal value to percent scale."""
    if value is None or pd.isna(value):
        return None

    return float(value) * 100


def annualized_return_from_daily_mean(daily_mean: float, trading_days: int = 252) -> float | None:
    """
    Approximate annualized return from average daily return.

    This is included as a descriptive statistic only.
    """
    if pd.isna(daily_mean):
        return None

    return float((1 + daily_mean) ** trading_days - 1)


def categorize_rate_environment(rate: float) -> str:
    """Categorize Federal Funds Rate level into simple descriptive bins."""
    if pd.isna(rate):
        return "missing"

    if rate < 2:
        return "low_rate_below_2pct"

    if rate < 5:
        return "moderate_rate_2_to_5pct"

    if rate < 10:
        return "high_rate_5_to_10pct"

    return "very_high_rate_10pct_or_above"


# -----------------------------------------------------------------------------
# Load and validate data
# -----------------------------------------------------------------------------

def load_integrated_data() -> pd.DataFrame:
    """Load and validate the integrated dataset."""
    require_file(INTEGRATED_PATH)

    df = pd.read_csv(INTEGRATED_PATH)

    required_columns = [
        "date",
        "sp500_close",
        "sp500_daily_return",
        "sp500_log_return",
        "sp500_zero_volume_flag",
        "federal_funds_rate",
        "federal_funds_rate_change",
        "federal_funds_rate_direction",
    ]

    require_columns(df, required_columns)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    invalid_dates = int(df["date"].isna().sum())
    if invalid_dates > 0:
        raise ValueError(
            f"Integrated dataset contains {invalid_dates} invalid dates."
        )

    numeric_columns = [
        "sp500_close",
        "sp500_daily_return",
        "sp500_log_return",
        "sp500_zero_volume_flag",
        "federal_funds_rate",
        "federal_funds_rate_change",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.sort_values("date").reset_index(drop=True)

    return df


# -----------------------------------------------------------------------------
# Analysis outputs
# -----------------------------------------------------------------------------

def build_summary_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Build descriptive statistics for core variables."""
    variables = [
        {
            "variable": "sp500_close",
            "description": "S&P 500 closing index level",
            "scale": "index level",
        },
        {
            "variable": "sp500_daily_return",
            "description": "Daily percent change in S&P 500 closing level",
            "scale": "decimal return",
        },
        {
            "variable": "sp500_log_return",
            "description": "Daily log return in S&P 500 closing level",
            "scale": "log return",
        },
        {
            "variable": "federal_funds_rate",
            "description": "Federal Funds Effective Rate",
            "scale": "percent",
        },
        {
            "variable": "federal_funds_rate_change",
            "description": "Daily change in Federal Funds Effective Rate",
            "scale": "percentage points",
        },
    ]

    rows = []

    for item in variables:
        column = item["variable"]
        series = df[column].dropna()

        rows.append(
            {
                "variable": column,
                "description": item["description"],
                "scale": item["scale"],
                "non_missing_count": int(series.count()),
                "missing_count": int(df[column].isna().sum()),
                "mean": safe_float(series.mean()),
                "median": safe_float(series.median()),
                "standard_deviation": safe_float(series.std()),
                "minimum": safe_float(series.min()),
                "percentile_25": safe_float(series.quantile(0.25)),
                "percentile_75": safe_float(series.quantile(0.75)),
                "maximum": safe_float(series.max()),
            }
        )

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(SUMMARY_STATISTICS_PATH, index=False)

    return summary_df


def build_correlation_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build correlation results for interest-rate variables and S&P 500 returns.

    These are descriptive correlations only and should not be interpreted as
    causal estimates.
    """
    analysis_df = df.dropna(
        subset=[
            "sp500_daily_return",
            "sp500_log_return",
            "federal_funds_rate",
            "federal_funds_rate_change",
        ]
    ).copy()

    pairs = [
        {
            "x_variable": "federal_funds_rate",
            "y_variable": "sp500_daily_return",
            "description": "Correlation between rate level and simple daily S&P 500 return",
        },
        {
            "x_variable": "federal_funds_rate_change",
            "y_variable": "sp500_daily_return",
            "description": "Correlation between rate change and simple daily S&P 500 return",
        },
        {
            "x_variable": "federal_funds_rate",
            "y_variable": "sp500_log_return",
            "description": "Correlation between rate level and S&P 500 log return",
        },
        {
            "x_variable": "federal_funds_rate_change",
            "y_variable": "sp500_log_return",
            "description": "Correlation between rate change and S&P 500 log return",
        },
    ]

    rows = []

    for pair in pairs:
        x = pair["x_variable"]
        y = pair["y_variable"]

        correlation = analysis_df[x].corr(analysis_df[y])

        rows.append(
            {
                "x_variable": x,
                "y_variable": y,
                "method": "pearson",
                "non_missing_pair_count": int(analysis_df[[x, y]].dropna().shape[0]),
                "correlation": safe_float(correlation),
                "description": pair["description"],
                "interpretation_note": (
                    "Exploratory association only; this is not a causal estimate."
                ),
            }
        )

    correlation_df = pd.DataFrame(rows)
    correlation_df.to_csv(CORRELATION_RESULTS_PATH, index=False)

    return correlation_df


def build_rate_change_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize S&P 500 returns by Federal Funds Rate direction.

    Rate direction categories:
    - increase
    - decrease
    - no_change
    - first_observation
    """
    analysis_df = df.dropna(subset=["sp500_daily_return"]).copy()

    grouped = (
        analysis_df
        .groupby("federal_funds_rate_direction", dropna=False)
        .agg(
            observation_count=("sp500_daily_return", "count"),
            average_daily_return=("sp500_daily_return", "mean"),
            median_daily_return=("sp500_daily_return", "median"),
            daily_return_standard_deviation=("sp500_daily_return", "std"),
            minimum_daily_return=("sp500_daily_return", "min"),
            maximum_daily_return=("sp500_daily_return", "max"),
            positive_return_days=("sp500_daily_return", lambda x: int((x > 0).sum())),
            negative_return_days=("sp500_daily_return", lambda x: int((x < 0).sum())),
            average_rate_change=("federal_funds_rate_change", "mean"),
        )
        .reset_index()
    )

    grouped["positive_return_share"] = (
        grouped["positive_return_days"] / grouped["observation_count"]
    )

    grouped["negative_return_share"] = (
        grouped["negative_return_days"] / grouped["observation_count"]
    )

    grouped["average_daily_return_percent"] = grouped["average_daily_return"].apply(percent)
    grouped["median_daily_return_percent"] = grouped["median_daily_return"].apply(percent)
    grouped["positive_return_share_percent"] = grouped["positive_return_share"].apply(percent)
    grouped["negative_return_share_percent"] = grouped["negative_return_share"].apply(percent)

    grouped = grouped.sort_values("federal_funds_rate_direction")
    grouped.to_csv(RATE_CHANGE_ANALYSIS_PATH, index=False)

    return grouped


def build_period_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize observations by decade and rate environment.

    This gives the final report a compact way to describe long-run variation
    across different interest-rate environments.
    """
    analysis_df = df.copy()

    analysis_df["year"] = analysis_df["date"].dt.year
    analysis_df["decade"] = (analysis_df["year"] // 10 * 10).astype(str) + "s"
    analysis_df["rate_environment"] = analysis_df["federal_funds_rate"].apply(
        categorize_rate_environment
    )

    decade_summary = (
        analysis_df
        .dropna(subset=["sp500_daily_return"])
        .groupby("decade")
        .agg(
            observation_count=("sp500_daily_return", "count"),
            start_date=("date", "min"),
            end_date=("date", "max"),
            average_federal_funds_rate=("federal_funds_rate", "mean"),
            average_daily_return=("sp500_daily_return", "mean"),
            daily_return_standard_deviation=("sp500_daily_return", "std"),
            average_sp500_close=("sp500_close", "mean"),
        )
        .reset_index()
    )

    decade_summary["summary_type"] = "decade"
    decade_summary["group"] = decade_summary["decade"]
    decade_summary = decade_summary.drop(columns=["decade"])

    environment_summary = (
        analysis_df
        .dropna(subset=["sp500_daily_return"])
        .groupby("rate_environment")
        .agg(
            observation_count=("sp500_daily_return", "count"),
            start_date=("date", "min"),
            end_date=("date", "max"),
            average_federal_funds_rate=("federal_funds_rate", "mean"),
            average_daily_return=("sp500_daily_return", "mean"),
            daily_return_standard_deviation=("sp500_daily_return", "std"),
            average_sp500_close=("sp500_close", "mean"),
        )
        .reset_index()
    )

    environment_summary["summary_type"] = "rate_environment"
    environment_summary["group"] = environment_summary["rate_environment"]
    environment_summary = environment_summary.drop(columns=["rate_environment"])

    period_summary = pd.concat(
        [decade_summary, environment_summary],
        ignore_index=True,
    )

    period_summary["start_date"] = pd.to_datetime(
        period_summary["start_date"]
    ).dt.strftime("%Y-%m-%d")

    period_summary["end_date"] = pd.to_datetime(
        period_summary["end_date"]
    ).dt.strftime("%Y-%m-%d")

    period_summary["average_daily_return_percent"] = (
        period_summary["average_daily_return"].apply(percent)
    )

    period_summary["approx_annualized_return_from_daily_mean"] = (
        period_summary["average_daily_return"].apply(
            annualized_return_from_daily_mean
        )
    )

    period_summary.to_csv(PERIOD_SUMMARY_PATH, index=False)

    return period_summary


def build_findings_summary(
    df: pd.DataFrame,
    summary_statistics: pd.DataFrame,
    correlation_results: pd.DataFrame,
    rate_change_analysis: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a compact findings summary for use in the final README.
    """
    date_min = df["date"].min().strftime("%Y-%m-%d")
    date_max = df["date"].max().strftime("%Y-%m-%d")

    sp500_start = float(df["sp500_close"].iloc[0])
    sp500_end = float(df["sp500_close"].iloc[-1])
    total_sp500_return = sp500_end / sp500_start - 1

    first_valid_return_date = (
        df.loc[df["sp500_daily_return"].notna(), "date"].min().strftime("%Y-%m-%d")
    )

    rate_min = float(df["federal_funds_rate"].min())
    rate_max = float(df["federal_funds_rate"].max())
    rate_mean = float(df["federal_funds_rate"].mean())

    daily_return_mean = float(df["sp500_daily_return"].mean())
    daily_return_std = float(df["sp500_daily_return"].std())

    corr_rate_level = correlation_results.loc[
        (
            correlation_results["x_variable"] == "federal_funds_rate"
        )
        & (
            correlation_results["y_variable"] == "sp500_daily_return"
        ),
        "correlation",
    ].iloc[0]

    corr_rate_change = correlation_results.loc[
        (
            correlation_results["x_variable"] == "federal_funds_rate_change"
        )
        & (
            correlation_results["y_variable"] == "sp500_daily_return"
        ),
        "correlation",
    ].iloc[0]

    direction_counts = (
        df["federal_funds_rate_direction"]
        .value_counts(dropna=False)
        .to_dict()
    )

    zero_volume_rows = int(df["sp500_zero_volume_flag"].sum())

    rows = [
        {
            "finding": "integrated_dataset_observations",
            "value": len(df),
            "description": "Number of trading-day observations in the final integrated dataset.",
        },
        {
            "finding": "integrated_dataset_date_range",
            "value": f"{date_min} to {date_max}",
            "description": "Date range covered by the final integrated dataset.",
        },
        {
            "finding": "first_valid_return_date",
            "value": first_valid_return_date,
            "description": "First date with a non-missing S&P 500 daily return.",
        },
        {
            "finding": "sp500_start_close",
            "value": sp500_start,
            "description": "S&P 500 close on the first integrated observation.",
        },
        {
            "finding": "sp500_end_close",
            "value": sp500_end,
            "description": "S&P 500 close on the final integrated observation.",
        },
        {
            "finding": "total_sp500_return_over_integrated_period",
            "value": total_sp500_return,
            "description": "Total S&P 500 return over the integrated date range.",
        },
        {
            "finding": "federal_funds_rate_min",
            "value": rate_min,
            "description": "Minimum Federal Funds Rate in the integrated dataset.",
        },
        {
            "finding": "federal_funds_rate_max",
            "value": rate_max,
            "description": "Maximum Federal Funds Rate in the integrated dataset.",
        },
        {
            "finding": "federal_funds_rate_mean",
            "value": rate_mean,
            "description": "Average Federal Funds Rate in the integrated dataset.",
        },
        {
            "finding": "average_sp500_daily_return",
            "value": daily_return_mean,
            "description": "Average S&P 500 daily return in the integrated dataset.",
        },
        {
            "finding": "sp500_daily_return_standard_deviation",
            "value": daily_return_std,
            "description": "Standard deviation of S&P 500 daily returns.",
        },
        {
            "finding": "correlation_rate_level_and_daily_return",
            "value": corr_rate_level,
            "description": "Pearson correlation between Federal Funds Rate level and S&P 500 daily return.",
        },
        {
            "finding": "correlation_rate_change_and_daily_return",
            "value": corr_rate_change,
            "description": "Pearson correlation between Federal Funds Rate daily change and S&P 500 daily return.",
        },
        {
            "finding": "rate_direction_counts",
            "value": str(direction_counts),
            "description": "Number of observations by Federal Funds Rate direction category.",
        },
        {
            "finding": "zero_volume_rows_retained",
            "value": zero_volume_rows,
            "description": "Zero-volume rows retained and flagged in the integrated dataset.",
        },
    ]

    findings_df = pd.DataFrame(rows)
    findings_df.to_csv(ANALYSIS_FINDINGS_SUMMARY_PATH, index=False)

    return findings_df


# -----------------------------------------------------------------------------
# Documentation
# -----------------------------------------------------------------------------

def write_analysis_doc(
    df: pd.DataFrame,
    findings: pd.DataFrame,
    correlation_results: pd.DataFrame,
    rate_change_analysis: pd.DataFrame,
) -> Path:
    """Write human-readable analysis summary documentation."""

    finding_map = {
        row["finding"]: row["value"]
        for _, row in findings.iterrows()
    }

    corr_level = correlation_results.loc[
        (
            correlation_results["x_variable"] == "federal_funds_rate"
        )
        & (
            correlation_results["y_variable"] == "sp500_daily_return"
        ),
        "correlation",
    ].iloc[0]

    corr_change = correlation_results.loc[
        (
            correlation_results["x_variable"] == "federal_funds_rate_change"
        )
        & (
            correlation_results["y_variable"] == "sp500_daily_return"
        ),
        "correlation",
    ].iloc[0]

    rate_change_markdown = rate_change_analysis[
        [
            "federal_funds_rate_direction",
            "observation_count",
            "average_daily_return_percent",
            "positive_return_share_percent",
        ]
    ].to_string(index=False)

    content = f"""# Analysis Summary

Generated by `scripts/analyze_data.py` on `{utc_now_iso()}`.

## Scope

This document summarizes exploratory numeric findings from the final integrated dataset. The analysis is descriptive and does not establish causality.

## Input File

- `{relative(INTEGRATED_PATH)}`

## Output Files

- `{relative(SUMMARY_STATISTICS_PATH)}`
- `{relative(CORRELATION_RESULTS_PATH)}`
- `{relative(RATE_CHANGE_ANALYSIS_PATH)}`
- `{relative(PERIOD_SUMMARY_PATH)}`
- `{relative(ANALYSIS_FINDINGS_SUMMARY_PATH)}`

## Dataset Coverage

The final integrated dataset contains {finding_map["integrated_dataset_observations"]} trading-day observations.

Date range: {finding_map["integrated_dataset_date_range"]}

First date with valid daily return: {finding_map["first_valid_return_date"]}

## S&P 500 Summary

S&P 500 close on first integrated observation: {finding_map["sp500_start_close"]}

S&P 500 close on final integrated observation: {finding_map["sp500_end_close"]}

Total S&P 500 return over integrated period: {float(finding_map["total_sp500_return_over_integrated_period"]) * 100:.2f}%

Average daily S&P 500 return: {float(finding_map["average_sp500_daily_return"]) * 100:.4f}%

Daily return standard deviation: {float(finding_map["sp500_daily_return_standard_deviation"]) * 100:.4f}%

## Federal Funds Rate Summary

Minimum Federal Funds Rate: {finding_map["federal_funds_rate_min"]}

Maximum Federal Funds Rate: {finding_map["federal_funds_rate_max"]}

Average Federal Funds Rate: {float(finding_map["federal_funds_rate_mean"]):.4f}

## Correlation Results

Correlation between Federal Funds Rate level and S&P 500 daily return: {corr_level:.6f}

Correlation between Federal Funds Rate daily change and S&P 500 daily return: {corr_change:.6f}

These correlations are exploratory associations only. They should not be interpreted as causal evidence that rate levels or rate changes directly caused daily stock market returns.

## S&P 500 Returns by Federal Funds Rate Direction

{rate_change_markdown}

## Zero-Volume Rows

Zero-volume rows retained in the integrated dataset: {finding_map["zero_volume_rows_retained"]}

These observations are retained because the closing price fields are still useful for index-level analysis, while volume is not a primary research variable.

## Interpretation for Final Report

The results support a cautious descriptive finding: the integrated dataset is suitable for exploring how monetary policy conditions and equity market performance align over time, but simple daily correlations between Federal Funds Rate variables and S&P 500 returns are not sufficient to establish causality. More rigorous future work could examine lag structures, macroeconomic controls, monetary policy regimes, and lower-frequency aggregation.
"""

    ANALYSIS_DOC_PATH.write_text(content, encoding="utf-8")

    return ANALYSIS_DOC_PATH


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def main() -> None:
    """Run exploratory data analysis."""

    print("=" * 72)
    print("IS 477 Final Project: Data Analysis")
    print("=" * 72)

    ensure_output_directories()

    print("Loading integrated dataset...")
    df = load_integrated_data()
    print(f"Loaded integrated dataset: {len(df)} rows")
    print(
        "Date range: "
        f"{df['date'].min().strftime('%Y-%m-%d')} to "
        f"{df['date'].max().strftime('%Y-%m-%d')}"
    )

    print("\nBuilding summary statistics...")
    summary_statistics = build_summary_statistics(df)
    print(f"Saved: {relative(SUMMARY_STATISTICS_PATH)}")

    print("\nBuilding correlation results...")
    correlation_results = build_correlation_results(df)
    print(f"Saved: {relative(CORRELATION_RESULTS_PATH)}")

    print("\nBuilding rate-change analysis...")
    rate_change_analysis = build_rate_change_analysis(df)
    print(f"Saved: {relative(RATE_CHANGE_ANALYSIS_PATH)}")

    print("\nBuilding period summary...")
    period_summary = build_period_summary(df)
    print(f"Saved: {relative(PERIOD_SUMMARY_PATH)}")

    print("\nBuilding findings summary...")
    findings_summary = build_findings_summary(
        df=df,
        summary_statistics=summary_statistics,
        correlation_results=correlation_results,
        rate_change_analysis=rate_change_analysis,
    )
    print(f"Saved: {relative(ANALYSIS_FINDINGS_SUMMARY_PATH)}")

    print("\nWriting analysis documentation...")
    analysis_doc = write_analysis_doc(
        df=df,
        findings=findings_summary,
        correlation_results=correlation_results,
        rate_change_analysis=rate_change_analysis,
    )
    print(f"Saved: {relative(analysis_doc)}")

    print("\nData analysis complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()