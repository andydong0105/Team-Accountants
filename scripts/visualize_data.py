"""
visualize_data.py

Generate visualizations from the integrated FRED Federal Funds Effective Rate
and S&P 500 dataset for the IS 477 final project.

Workflow position:
    data_quality.py -> data_cleaning.py -> data_integration.py
    -> analyze_data.py -> visualize_data.py

This script reads:
- data/processed/integrated_fred_sp500.csv
- results/rate_change_analysis.csv, if available
- results/correlation_results.csv, if available

It produces:
- figures/fed_funds_rate_trend.png
- figures/sp500_close_trend.png
- figures/sp500_daily_returns.png
- figures/fed_funds_rate_vs_sp500_return.png
- figures/average_return_by_rate_direction.png
- results/visualization_summary.csv
- docs/VISUALIZATION_SUMMARY.md

The visualizations are descriptive and exploratory. They do not establish
causal relationships between Federal Funds Rate movements and S&P 500 returns.

Usage from repository root:
    python scripts/visualize_data.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


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
FIGURES_DIR = PROJECT_ROOT / "figures"
DOCS_DIR = PROJECT_ROOT / "docs"

INTEGRATED_PATH = PROCESSED_DIR / "integrated_fred_sp500.csv"
RATE_CHANGE_ANALYSIS_PATH = RESULTS_DIR / "rate_change_analysis.csv"
CORRELATION_RESULTS_PATH = RESULTS_DIR / "correlation_results.csv"

FED_FUNDS_TREND_PATH = FIGURES_DIR / "fed_funds_rate_trend.png"
SP500_CLOSE_TREND_PATH = FIGURES_DIR / "sp500_close_trend.png"
SP500_DAILY_RETURNS_PATH = FIGURES_DIR / "sp500_daily_returns.png"
RATE_VS_RETURN_PATH = FIGURES_DIR / "fed_funds_rate_vs_sp500_return.png"
RETURN_BY_RATE_DIRECTION_PATH = FIGURES_DIR / "average_return_by_rate_direction.png"

VISUALIZATION_SUMMARY_PATH = RESULTS_DIR / "visualization_summary.csv"
VISUALIZATION_DOC_PATH = DOCS_DIR / "VISUALIZATION_SUMMARY.md"


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
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def require_file(path: Path) -> None:
    """Raise a clear error if an expected input file is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file is missing: {relative(path)}\n"
            "Run scripts/data_integration.py before running scripts/visualize_data.py."
        )


def require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    """Raise a clear error if required columns are missing."""
    missing = [column for column in columns if column not in df.columns]

    if missing:
        raise ValueError(
            f"Integrated dataset is missing required columns: {missing}"
        )


def save_current_figure(path: Path) -> None:
    """Save the current matplotlib figure with consistent export settings."""
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()


def format_date_range(df: pd.DataFrame) -> str:
    """Return the date range of a dataframe as a string."""
    return (
        f"{df['date'].min().strftime('%Y-%m-%d')} to "
        f"{df['date'].max().strftime('%Y-%m-%d')}"
    )


# -----------------------------------------------------------------------------
# Load data
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
            f"Integrated dataset contains {invalid_dates} invalid date values."
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


def load_rate_change_analysis() -> pd.DataFrame | None:
    """Load rate-change analysis output if available."""
    if not RATE_CHANGE_ANALYSIS_PATH.exists():
        return None

    return pd.read_csv(RATE_CHANGE_ANALYSIS_PATH)


def load_correlation_results() -> pd.DataFrame | None:
    """Load correlation results output if available."""
    if not CORRELATION_RESULTS_PATH.exists():
        return None

    return pd.read_csv(CORRELATION_RESULTS_PATH)


# -----------------------------------------------------------------------------
# Visualization functions
# -----------------------------------------------------------------------------

def plot_fed_funds_rate_trend(df: pd.DataFrame) -> Path:
    """Plot Federal Funds Rate over time."""
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["federal_funds_rate"], linewidth=1)

    plt.title("Federal Funds Effective Rate Over Time")
    plt.xlabel("Date")
    plt.ylabel("Federal Funds Effective Rate (%)")
    plt.grid(True, alpha=0.3)

    save_current_figure(FED_FUNDS_TREND_PATH)
    return FED_FUNDS_TREND_PATH


def plot_sp500_close_trend(df: pd.DataFrame) -> Path:
    """Plot S&P 500 closing level over time."""
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["sp500_close"], linewidth=1)

    plt.title("S&P 500 Closing Level Over Time")
    plt.xlabel("Date")
    plt.ylabel("S&P 500 Close")
    plt.grid(True, alpha=0.3)

    save_current_figure(SP500_CLOSE_TREND_PATH)
    return SP500_CLOSE_TREND_PATH


def plot_sp500_daily_returns(df: pd.DataFrame) -> Path:
    """Plot S&P 500 daily returns over time."""
    plot_df = df.dropna(subset=["sp500_daily_return"]).copy()

    plt.figure(figsize=(12, 6))
    plt.plot(plot_df["date"], plot_df["sp500_daily_return"] * 100, linewidth=0.6)

    plt.title("S&P 500 Daily Returns Over Time")
    plt.xlabel("Date")
    plt.ylabel("Daily Return (%)")
    plt.grid(True, alpha=0.3)

    save_current_figure(SP500_DAILY_RETURNS_PATH)
    return SP500_DAILY_RETURNS_PATH


def plot_fed_funds_rate_vs_sp500_return(df: pd.DataFrame) -> Path:
    """Scatter plot of Federal Funds Rate level and S&P 500 daily return."""
    plot_df = df.dropna(
        subset=[
            "federal_funds_rate",
            "sp500_daily_return",
        ]
    ).copy()

    plt.figure(figsize=(10, 6))
    plt.scatter(
        plot_df["federal_funds_rate"],
        plot_df["sp500_daily_return"] * 100,
        s=8,
        alpha=0.35,
    )

    plt.title("Federal Funds Rate vs. S&P 500 Daily Return")
    plt.xlabel("Federal Funds Effective Rate (%)")
    plt.ylabel("S&P 500 Daily Return (%)")
    plt.grid(True, alpha=0.3)

    save_current_figure(RATE_VS_RETURN_PATH)
    return RATE_VS_RETURN_PATH


def plot_average_return_by_rate_direction(
    df: pd.DataFrame,
    rate_change_analysis: pd.DataFrame | None,
) -> Path:
    """
    Plot average daily return by Federal Funds Rate direction.

    Uses results/rate_change_analysis.csv if available. Otherwise, computes
    the same grouped statistic directly from the integrated dataset.
    """
    if rate_change_analysis is not None:
        plot_df = rate_change_analysis.copy()

        if "average_daily_return_percent" not in plot_df.columns:
            plot_df["average_daily_return_percent"] = (
                plot_df["average_daily_return"] * 100
            )

        direction_col = "federal_funds_rate_direction"
        value_col = "average_daily_return_percent"

    else:
        plot_df = (
            df.dropna(subset=["sp500_daily_return"])
            .groupby("federal_funds_rate_direction")
            .agg(
                average_daily_return_percent=(
                    "sp500_daily_return",
                    lambda x: x.mean() * 100,
                )
            )
            .reset_index()
        )

        direction_col = "federal_funds_rate_direction"
        value_col = "average_daily_return_percent"

    order = ["decrease", "first_observation", "increase", "no_change"]
    plot_df["sort_order"] = plot_df[direction_col].apply(
        lambda value: order.index(value) if value in order else len(order)
    )
    plot_df = plot_df.sort_values("sort_order")

    plt.figure(figsize=(10, 6))
    plt.bar(plot_df[direction_col], plot_df[value_col])

    plt.title("Average S&P 500 Daily Return by Federal Funds Rate Direction")
    plt.xlabel("Federal Funds Rate Direction")
    plt.ylabel("Average Daily Return (%)")
    plt.grid(True, axis="y", alpha=0.3)

    save_current_figure(RETURN_BY_RATE_DIRECTION_PATH)
    return RETURN_BY_RATE_DIRECTION_PATH


# -----------------------------------------------------------------------------
# Summary outputs
# -----------------------------------------------------------------------------

def build_visualization_summary(
    figure_paths: list[Path],
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Build a machine-readable summary of generated figures."""
    figure_descriptions = {
        FED_FUNDS_TREND_PATH.name: (
            "Line chart showing the Federal Funds Effective Rate over the "
            "integrated date range."
        ),
        SP500_CLOSE_TREND_PATH.name: (
            "Line chart showing the S&P 500 closing index level over the "
            "integrated date range."
        ),
        SP500_DAILY_RETURNS_PATH.name: (
            "Line chart showing daily S&P 500 returns over time."
        ),
        RATE_VS_RETURN_PATH.name: (
            "Scatter plot comparing Federal Funds Rate level with S&P 500 "
            "daily return."
        ),
        RETURN_BY_RATE_DIRECTION_PATH.name: (
            "Bar chart comparing average S&P 500 daily return across Federal "
            "Funds Rate direction categories."
        ),
    }

    rows = []

    for path in figure_paths:
        rows.append(
            {
                "figure_file": relative(path),
                "exists": path.exists(),
                "description": figure_descriptions.get(path.name, ""),
                "input_file": relative(INTEGRATED_PATH),
                "date_range": format_date_range(df),
                "observation_count": len(df),
            }
        )

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(VISUALIZATION_SUMMARY_PATH, index=False)

    return summary_df


def write_visualization_doc(
    figure_paths: list[Path],
    df: pd.DataFrame,
    correlation_results: pd.DataFrame | None,
) -> Path:
    """Write human-readable visualization documentation."""

    corr_level_text = "not available"
    corr_change_text = "not available"

    if correlation_results is not None:
        level_match = correlation_results[
            (correlation_results["x_variable"] == "federal_funds_rate")
            & (correlation_results["y_variable"] == "sp500_daily_return")
        ]

        change_match = correlation_results[
            (correlation_results["x_variable"] == "federal_funds_rate_change")
            & (correlation_results["y_variable"] == "sp500_daily_return")
        ]

        if not level_match.empty:
            corr_level_text = f"{float(level_match['correlation'].iloc[0]):.6f}"

        if not change_match.empty:
            corr_change_text = f"{float(change_match['correlation'].iloc[0]):.6f}"

    figure_list = "\n".join(
        f"- `{relative(path)}`" for path in figure_paths
    )

    content = f"""# Visualization Summary

Generated by `scripts/visualize_data.py` on `{utc_now_iso()}`.

## Scope

This document summarizes visualizations generated from the final integrated dataset. The figures are descriptive and exploratory. They do not establish causal relationships between Federal Funds Rate movements and S&P 500 returns.

## Input Files

- `{relative(INTEGRATED_PATH)}`
- `{relative(RATE_CHANGE_ANALYSIS_PATH)}` if available
- `{relative(CORRELATION_RESULTS_PATH)}` if available

## Output Files

{figure_list}

- `{relative(VISUALIZATION_SUMMARY_PATH)}`

## Dataset Coverage

The visualizations use the final integrated dataset.

Observation count: {len(df)}

Date range: {format_date_range(df)}

## Figure Descriptions

### Federal Funds Rate Trend

`{relative(FED_FUNDS_TREND_PATH)}` shows the Federal Funds Effective Rate over time. This figure helps describe major changes in the monetary policy environment across the integrated period.

### S&P 500 Close Trend

`{relative(SP500_CLOSE_TREND_PATH)}` shows the S&P 500 closing level over time. This figure provides the long-run market-performance context for the project.

### S&P 500 Daily Returns

`{relative(SP500_DAILY_RETURNS_PATH)}` shows daily S&P 500 returns over time. The plot highlights periods of higher and lower market volatility.

### Federal Funds Rate vs. S&P 500 Daily Return

`{relative(RATE_VS_RETURN_PATH)}` is a scatter plot comparing the Federal Funds Rate level with S&P 500 daily returns.

Pearson correlation between Federal Funds Rate level and S&P 500 daily return: {corr_level_text}

Pearson correlation between Federal Funds Rate change and S&P 500 daily return: {corr_change_text}

These values are descriptive correlations only and should not be interpreted as causal estimates.

### Average Return by Rate Direction

`{relative(RETURN_BY_RATE_DIRECTION_PATH)}` compares average S&P 500 daily returns across Federal Funds Rate direction categories. This figure supports the exploratory findings section by summarizing market returns on rate-increase, rate-decrease, and no-change days.

## Interpretation for Final Report

The figures support a cautious descriptive interpretation. The project successfully creates a reproducible integrated dataset that can be used to examine how interest-rate conditions and equity market performance align over time. However, the visualizations do not prove that Federal Funds Rate movements cause S&P 500 returns. Future work would need lagged models, macroeconomic controls, and stronger econometric design to address causal questions.
"""

    VISUALIZATION_DOC_PATH.write_text(content, encoding="utf-8")
    return VISUALIZATION_DOC_PATH


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def main() -> None:
    """Run visualization generation."""

    print("=" * 72)
    print("IS 477 Final Project: Visualization")
    print("=" * 72)

    ensure_output_directories()

    print("Loading integrated dataset...")
    df = load_integrated_data()
    print(f"Loaded integrated dataset: {len(df)} rows")
    print(f"Date range: {format_date_range(df)}")

    print("\nLoading optional analysis outputs...")
    rate_change_analysis = load_rate_change_analysis()
    correlation_results = load_correlation_results()

    if rate_change_analysis is not None:
        print(f"Loaded: {relative(RATE_CHANGE_ANALYSIS_PATH)}")
    else:
        print("Rate-change analysis file not found; computing grouped values directly.")

    if correlation_results is not None:
        print(f"Loaded: {relative(CORRELATION_RESULTS_PATH)}")
    else:
        print("Correlation results file not found; visualization documentation will omit correlations.")

    print("\nGenerating figures...")

    figure_paths = []

    path = plot_fed_funds_rate_trend(df)
    figure_paths.append(path)
    print(f"Saved: {relative(path)}")

    path = plot_sp500_close_trend(df)
    figure_paths.append(path)
    print(f"Saved: {relative(path)}")

    path = plot_sp500_daily_returns(df)
    figure_paths.append(path)
    print(f"Saved: {relative(path)}")

    path = plot_fed_funds_rate_vs_sp500_return(df)
    figure_paths.append(path)
    print(f"Saved: {relative(path)}")

    path = plot_average_return_by_rate_direction(df, rate_change_analysis)
    figure_paths.append(path)
    print(f"Saved: {relative(path)}")

    print("\nWriting visualization summary...")
    summary_df = build_visualization_summary(figure_paths, df)
    print(f"Saved: {relative(VISUALIZATION_SUMMARY_PATH)}")

    print("\nWriting visualization documentation...")
    doc_path = write_visualization_doc(
        figure_paths=figure_paths,
        df=df,
        correlation_results=correlation_results,
    )
    print(f"Saved: {relative(doc_path)}")

    print("\nVisualization step complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()