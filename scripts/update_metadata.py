"""
Generate machine-readable project metadata for the IS 477 final project.

This script creates metadata/metadata.json from the current repository contents.
It is designed to be reproducible and live-mode aware: temporalCoverage and
dataset statistics are calculated from the current integrated dataset rather
than hard-coded.

Expected input:
    data/processed/integrated_fred_sp500.csv

Expected output:
    metadata/metadata.json
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"
RESULTS_DIR = PROJECT_ROOT / "results"
METADATA_DIR = PROJECT_ROOT / "metadata"
METADATA_PATH = METADATA_DIR / "metadata.json"

INTEGRATED_DATA_PATH = DATA_PROCESSED_DIR / "integrated_fred_sp500.csv"


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def relative_path(path: Path) -> str:
    """Return a POSIX-style path relative to the project root."""
    return path.relative_to(PROJECT_ROOT).as_posix()


def file_size_bytes(path: Path) -> Optional[int]:
    """Return file size in bytes if the file exists, otherwise None."""
    if path.exists():
        return path.stat().st_size
    return None


def make_data_download(
    name: str,
    path: Path,
    encoding_format: str,
    description: str,
) -> Dict[str, Any]:
    """
    Create a Schema.org DataDownload object.

    Missing files are still listed because the metadata documents the expected
    repository structure, but fileSize is only included when the file exists.
    """
    item: Dict[str, Any] = {
        "@type": "schema:DataDownload",
        "name": name,
        "encodingFormat": encoding_format,
        "contentUrl": relative_path(path),
        "description": description,
    }

    size = file_size_bytes(path)
    if size is not None:
        item["contentSize"] = f"{size} bytes"

    return item


def read_integrated_profile(path: Path) -> Dict[str, Any]:
    """
    Read the integrated dataset and return metadata-relevant profile values.

    Raises FileNotFoundError if the integrated dataset does not exist because
    metadata should reflect an actual generated project artifact.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Integrated dataset not found: {path}. "
            "Run the workflow through data integration before generating metadata."
        )

    df = pd.read_csv(path)

    if "date" not in df.columns:
        raise ValueError(
            f"Integrated dataset is missing required 'date' column: {path}"
        )

    dates = pd.to_datetime(df["date"], errors="coerce")

    if dates.isna().all():
        raise ValueError(
            "The 'date' column in the integrated dataset could not be parsed."
        )

    start_date = dates.min().date().isoformat()
    end_date = dates.max().date().isoformat()

    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": list(df.columns),
        "start_date": start_date,
        "end_date": end_date,
        "temporal_coverage": f"{start_date}/{end_date}",
    }


def build_variable_metadata(columns: List[str]) -> List[Dict[str, str]]:
    """
    Build variableMeasured metadata.

    Known columns receive detailed descriptions. Any additional columns are
    still included so that the metadata stays valid if the integrated dataset
    changes in live mode.
    """
    descriptions = {
        "date": (
            "Date used as the integration key. In the integrated dataset, "
            "each row represents one S&P 500 trading day."
        ),
        "federal_funds_rate": (
            "Federal Funds Effective Rate matched to the S&P 500 trading date. "
            "Unit: percent."
        ),
        "federal_funds_rate_change": (
            "Change in the Federal Funds Effective Rate from the previous "
            "integrated trading-day observation. Unit: percentage points."
        ),
        "federal_funds_rate_direction": (
            "Categorical direction of Federal Funds Rate change: increase, "
            "decrease, no_change, or first_observation."
        ),
        "sp500_open": "S&P 500 opening index level on the trading date.",
        "sp500_high": "S&P 500 highest index level on the trading date.",
        "sp500_low": "S&P 500 lowest index level on the trading date.",
        "sp500_close": "S&P 500 closing index level on the trading date.",
        "sp500_adj_close": (
            "S&P 500 adjusted closing index level on the trading date, if "
            "provided by the source."
        ),
        "sp500_volume": "Reported S&P 500 trading volume from the source data.",
        "sp500_daily_return": (
            "Daily simple return calculated from S&P 500 closing index levels."
        ),
        "sp500_log_return": (
            "Daily log return calculated from S&P 500 closing index levels."
        ),
        "sp500_zero_volume_flag": (
            "Binary flag identifying rows where the original S&P 500 volume "
            "field was reported as zero."
        ),
    }

    variable_metadata = []
    for col in columns:
        variable_metadata.append(
            {
                "@type": "schema:PropertyValue",
                "name": col,
                "description": descriptions.get(
                    col,
                    "Column included in the integrated analysis-ready dataset.",
                ),
            }
        )

    return variable_metadata


def build_metadata(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Construct the full metadata dictionary."""
    today = date.today().isoformat()

    metadata: Dict[str, Any] = {
        "@context": {
            "schema": "https://schema.org/",
            "dcat": "https://www.w3.org/ns/dcat#",
            "dct": "http://purl.org/dc/terms/",
        },
        "@type": "schema:Dataset",
        "name": "Federal Funds Rate and S&P 500 Market Performance",
        "alternateName": "FRED DFF and S&P 500 Integrated Dataset",
        "description": (
            "This project creates a reproducible data curation and exploratory "
            "analysis workflow integrating the Federal Funds Effective Rate from "
            "FRED with S&P 500 market data from Yahoo Finance through yfinance. "
            "The workflow documents data acquisition, checksum verification, raw "
            "data quality profiling, cleaning, temporal alignment, integration, "
            "analysis, visualization, and workflow automation using Snakemake. "
            "The main curation challenge is aligning a calendar-day interest-rate "
            "series with a trading-day stock market series."
        ),
        "keywords": [
            "Federal Funds Effective Rate",
            "FRED",
            "DFF",
            "S&P 500",
            "Yahoo Finance",
            "yfinance",
            "data curation",
            "data integration",
            "time series",
            "reproducibility",
            "Snakemake",
            "IS 477",
        ],
        "creator": [
            {
                "@type": "schema:Person",
                "name": "Weimo Song",
            },
            {
                "@type": "schema:Person",
                "name": "Andy Dong",
            },
        ],
        "contributor": [
            {
                "@type": "schema:Person",
                "name": "Weimo Song",
            },
            {
                "@type": "schema:Person",
                "name": "Andy Dong",
            },
        ],
        "license": [
            {
                "@type": "schema:CreativeWork",
                "name": "MIT License for project code",
                "url": "https://opensource.org/license/mit/",
            },
            {
                "@type": "schema:CreativeWork",
                "name": "CC BY 4.0 License for project documentation",
                "url": "https://creativecommons.org/licenses/by/4.0/",
            },
        ],
        "isBasedOn": [
            {
                "@type": "schema:Dataset",
                "name": "Federal Funds Effective Rate",
                "alternateName": "FRED DFF",
                "identifier": "DFF",
                "publisher": {
                    "@type": "schema:Organization",
                    "name": "Federal Reserve Bank of St. Louis",
                },
                "url": "https://fred.stlouisfed.org/series/DFF",
                "description": (
                    "Daily Federal Funds Effective Rate observations acquired "
                    "from the FRED API."
                ),
            },
            {
                "@type": "schema:Dataset",
                "name": "S&P 500 Index",
                "alternateName": "^GSPC",
                "publisher": {
                    "@type": "schema:Organization",
                    "name": "Yahoo Finance",
                },
                "url": "https://finance.yahoo.com/quote/%5EGSPC/",
                "description": (
                    "S&P 500 market data acquired through the yfinance Python package."
                ),
            },
        ],
        "temporalCoverage": profile["temporal_coverage"],
        "spatialCoverage": {
            "@type": "schema:Place",
            "name": "United States",
        },
        "variableMeasured": build_variable_metadata(profile["columns"]),
        "distribution": [
            make_data_download(
                "FRED DFF raw JSON",
                DATA_RAW_DIR / "fred_dff_raw.json",
                "application/json",
                "Raw JSON response from the FRED API.",
            ),
            make_data_download(
                "FRED DFF raw CSV",
                DATA_RAW_DIR / "fred_dff.csv",
                "text/csv",
                "Raw Federal Funds Effective Rate observations converted to CSV.",
            ),
            make_data_download(
                "S&P 500 raw CSV",
                DATA_RAW_DIR / "sp500_raw.csv",
                "text/csv",
                "Raw S&P 500 market data acquired through yfinance.",
            ),
            make_data_download(
                "Cleaned FRED DFF dataset",
                DATA_PROCESSED_DIR / "fred_dff_clean.csv",
                "text/csv",
                "Cleaned Federal Funds Effective Rate dataset.",
            ),
            make_data_download(
                "Cleaned S&P 500 dataset",
                DATA_PROCESSED_DIR / "sp500_clean.csv",
                "text/csv",
                "Cleaned S&P 500 market dataset.",
            ),
            make_data_download(
                "Integrated FRED and S&P 500 dataset",
                INTEGRATED_DATA_PATH,
                "text/csv",
                "Final analysis-ready integrated dataset.",
            ),
            make_data_download(
                "Data dictionary",
                DOCS_DIR / "data_dictionary.md",
                "text/markdown",
                "Human-readable data dictionary for project datasets and variables.",
            ),
            make_data_download(
                "Workflow documentation",
                DOCS_DIR / "WORKFLOW.md",
                "text/markdown",
                "Documentation explaining how the workflow is organized and executed.",
            ),
            make_data_download(
                "Raw data quality profile",
                DOCS_DIR / "data_quality_profile.md",
                "text/markdown",
                "Human-readable summary of raw data quality assessment results.",
            ),
            make_data_download(
                "Cleaning provenance documentation",
                DOCS_DIR / "cleaning_provenance.md",
                "text/markdown",
                "Human-readable documentation of data cleaning decisions and provenance.",
            ),
            make_data_download(
                "Integration summary",
                DOCS_DIR / "integration_summary.md",
                "text/markdown",
                "Documentation of dataset alignment and integration results.",
            ),
            make_data_download(
                "Checksum verification results",
                RESULTS_DIR / "checksum_verification.csv",
                "text/csv",
                "CSV record of SHA-256 checksum verification results.",
            ),
            make_data_download(
                "Analysis summary",
                RESULTS_DIR / "analysis_summary.md",
                "text/markdown",
                "Summary of analysis results generated by the analysis script.",
            ),
        ],
        "measurementTechnique": [
            "Programmatic data acquisition using Python requests and yfinance",
            "SHA-256 checksum generation and verification",
            "Raw data quality profiling",
            "Script-based data cleaning",
            "Date-key integration using S&P 500 trading days as the base timeline",
            "Exploratory descriptive analysis",
            "Visualization generation using matplotlib",
            "Snakemake workflow automation",
        ],
        "softwareRequirements": [
            "Python 3.10 or higher",
            "pandas",
            "numpy",
            "matplotlib",
            "requests",
            "yfinance",
            "snakemake",
        ],
        "programmingLanguage": "Python",
        "runtimePlatform": "Python 3",
        "includedInDataCatalog": {
            "@type": "schema:DataCatalog",
            "name": "IS 477 Final Project Repository",
        },
        "hasPart": [
            {
                "@type": "schema:SoftwareSourceCode",
                "name": "Data acquisition script",
                "programmingLanguage": "Python",
                "codeRepository": "scripts/acquire_data.py",
            },
            {
                "@type": "schema:SoftwareSourceCode",
                "name": "Raw data quality profiling script",
                "programmingLanguage": "Python",
                "codeRepository": "scripts/data_quality.py",
            },
            {
                "@type": "schema:SoftwareSourceCode",
                "name": "Data cleaning script",
                "programmingLanguage": "Python",
                "codeRepository": "scripts/data_cleaning.py",
            },
            {
                "@type": "schema:SoftwareSourceCode",
                "name": "Data integration script",
                "programmingLanguage": "Python",
                "codeRepository": "scripts/data_integration.py",
            },
            {
                "@type": "schema:SoftwareSourceCode",
                "name": "Data analysis script",
                "programmingLanguage": "Python",
                "codeRepository": "scripts/analyze_data.py",
            },
            {
                "@type": "schema:SoftwareSourceCode",
                "name": "Visualization script",
                "programmingLanguage": "Python",
                "codeRepository": "scripts/visualize_data.py",
            },
            {
                "@type": "schema:SoftwareSourceCode",
                "name": "Project metadata generation script",
                "programmingLanguage": "Python",
                "codeRepository": "scripts/update_metadata.py",
            },
            {
                "@type": "schema:SoftwareSourceCode",
                "name": "Snakemake workflow",
                "programmingLanguage": "Snakemake",
                "codeRepository": "Snakefile",
            },
        ],
        "mainEntity": {
            "@type": "schema:Dataset",
            "name": "Integrated FRED DFF and S&P 500 Dataset",
            "encodingFormat": "text/csv",
            "contentUrl": relative_path(INTEGRATED_DATA_PATH),
            "description": (
                "Final analysis-ready dataset containing one row per S&P 500 "
                "trading day within the FRED DFF date range."
            ),
            "temporalCoverage": profile["temporal_coverage"],
            "numberOfItems": profile["row_count"],
            "numberOfVariables": profile["column_count"],
        },
        "additionalProperty": [
            {
                "@type": "schema:PropertyValue",
                "name": "row_count",
                "value": profile["row_count"],
                "description": "Number of rows in the integrated analysis-ready dataset.",
            },
            {
                "@type": "schema:PropertyValue",
                "name": "column_count",
                "value": profile["column_count"],
                "description": "Number of columns in the integrated analysis-ready dataset.",
            },
            {
                "@type": "schema:PropertyValue",
                "name": "workflow_mode",
                "value": "frozen by default; live mode optional",
                "description": (
                    "The default workflow reproduces results from repository-included "
                    "raw data. Live mode can reacquire current data when internet "
                    "access and required API credentials are available."
                ),
            },
        ],
        "dateCreated": "2026-05-06",
        "dateModified": today,
        "version": "1.0",
        "inLanguage": "en-US",
        "educationalUse": "IS 477 final project",
        "isAccessibleForFree": True,
        "conditionsOfAccess": (
            "Raw and processed input data are included in the repository for "
            "reproducibility. Live data reacquisition may require internet access "
            "and a FRED API key."
        ),
        "citation": [
            (
                "Federal Reserve Bank of St. Louis. Federal Funds Effective Rate "
                "[DFF]. FRED, Federal Reserve Bank of St. Louis."
            ),
            (
                "Yahoo Finance. S&P 500 Index (^GSPC). Accessed through the "
                "yfinance Python package."
            ),
            "The pandas development team. pandas: Powerful Python data analysis toolkit.",
            "Mölder, F., et al. Sustainable data analysis with Snakemake.",
        ],
    }

    return metadata


def main() -> None:
    """Generate metadata/metadata.json."""
    profile = read_integrated_profile(INTEGRATED_DATA_PATH)
    metadata = build_metadata(profile)

    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    with METADATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Metadata written to {relative_path(METADATA_PATH)}")
    print(f"Temporal coverage: {profile['temporal_coverage']}")
    print(
        "Integrated dataset profile: "
        f"{profile['row_count']:,} rows, {profile['column_count']} columns"
    )


if __name__ == "__main__":
    main()