"""
storage_and_organization.py

Organize project files and document the repository structure for the
IS 477 final project.

This script performs four main tasks:

1. Creates the standard final-project directory structure.
2. Verifies that expected raw data and key project files exist.
3. Writes README files for major artifact folders.
4. Generates repository documentation:
   - docs/DATA_STRUCTURE.md
   - docs/file_inventory.csv
   - results/storage_status.json

Expected raw inputs, created by scripts/acquire_data.py:
- data/raw/fred_dff_raw.json
- data/raw/fred_dff.csv
- data/raw/sp500_raw.csv
- data/raw/CHECKSUMS.sha256
- data/raw/acquisition_metadata.json

Usage from repository root:

    python scripts/storage_and_organization.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import csv
import json
from typing import Iterable


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

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DOCS_DIR = PROJECT_ROOT / "docs"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
METADATA_DIR = PROJECT_ROOT / "metadata"

EXPECTED_ROOT_FILES = [
    PROJECT_ROOT / "Snakefile",
    PROJECT_ROOT / "requirements.txt",
    PROJECT_ROOT / "pip_freeze.txt",
    PROJECT_ROOT / "LICENSE",
    PROJECT_ROOT / "LICENSE-DOCUMENTATION.md",
    PROJECT_ROOT / "CITATION.cff",
]

EXPECTED_RAW_FILES = [
    RAW_DIR / "fred_dff_raw.json",
    RAW_DIR / "fred_dff.csv",
    RAW_DIR / "sp500_raw.csv",
    RAW_DIR / "CHECKSUMS.sha256",
    RAW_DIR / "acquisition_metadata.json",
]

EXPECTED_PROCESSED_FILES = [
    PROCESSED_DIR / "fred_dff_clean.csv",
    PROCESSED_DIR / "sp500_clean.csv",
    PROCESSED_DIR / "integrated_fred_sp500.csv",
]

EXPECTED_SCRIPT_FILES = [
    SCRIPTS_DIR / "acquire_data.py",
    SCRIPTS_DIR / "storage_and_organization.py",
    SCRIPTS_DIR / "data_quality.py",
    SCRIPTS_DIR / "data_cleaning.py",
    SCRIPTS_DIR / "data_integration.py",
    SCRIPTS_DIR / "analyze_data.py",
    SCRIPTS_DIR / "visualize_data.py",
]

EXPECTED_RESULT_FILES = [
    RESULTS_DIR / "storage_status.json",
    RESULTS_DIR / "checksum_verification.csv",
    RESULTS_DIR / "data_quality_summary.csv",
    RESULTS_DIR / "missingness_summary.csv",
    RESULTS_DIR / "date_coverage_summary.csv",
    RESULTS_DIR / "schema_summary.csv",
    RESULTS_DIR / "temporal_alignment_profile.csv",
    RESULTS_DIR / "cleaning_summary.csv",
    RESULTS_DIR / "cleaning_decisions.csv",
    RESULTS_DIR / "integration_summary.csv",
    RESULTS_DIR / "integration_quality_checks.csv",
    RESULTS_DIR / "summary_statistics.csv",
    RESULTS_DIR / "correlation_results.csv",
    RESULTS_DIR / "rate_change_analysis.csv",
    RESULTS_DIR / "period_summary.csv",
    RESULTS_DIR / "analysis_findings_summary.csv",
    RESULTS_DIR / "visualization_summary.csv",
]

EXPECTED_FIGURE_FILES = [
    FIGURES_DIR / "fed_funds_rate_trend.png",
    FIGURES_DIR / "sp500_close_trend.png",
    FIGURES_DIR / "sp500_daily_returns.png",
    FIGURES_DIR / "fed_funds_rate_vs_sp500_return.png",
    FIGURES_DIR / "average_return_by_rate_direction.png",
]

EXPECTED_DOC_FILES = [
    DOCS_DIR / "DATA_STRUCTURE.md",
    DOCS_DIR / "file_inventory.csv",
    DOCS_DIR / "WORKFLOW.md",
    DOCS_DIR / "data_dictionary.md",
    DOCS_DIR / "data_quality_profile.md",
    DOCS_DIR / "cleaning_provenance.md",
    DOCS_DIR / "INTEGRATION_SUMMARY.md",
    DOCS_DIR / "ANALYSIS_SUMMARY.md",
    DOCS_DIR / "VISUALIZATION_SUMMARY.md",
]

EXPECTED_METADATA_FILES = [
    METADATA_DIR / "metadata.json",
]

STANDARD_DIRECTORIES = [
    DATA_DIR,
    RAW_DIR,
    PROCESSED_DIR,
    SCRIPTS_DIR,
    DOCS_DIR,
    RESULTS_DIR,
    FIGURES_DIR,
    METADATA_DIR,
]

INVENTORY_TARGET_DIRS = [
    DATA_DIR,
    SCRIPTS_DIR,
    DOCS_DIR,
    RESULTS_DIR,
    FIGURES_DIR,
    METADATA_DIR,
]

EXCLUDE_FILE_NAMES = {
    ".DS_Store",
}

EXCLUDE_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".ipynb_checkpoints",
    ".snakemake",
    "venv",
    ".venv",
    "env",
    ".env",
}


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------

def utc_now_iso() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def relative(path: Path) -> str:
    """Return a repository-relative POSIX path."""
    return path.relative_to(PROJECT_ROOT).as_posix()


def file_size_label(size_bytes: int) -> str:
    """Return a human-readable file size label."""
    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"

    return f"{size_bytes / (1024 ** 2):.1f} MB"


def should_include_file(path: Path) -> bool:
    """Return True if a file should be included in the inventory."""
    if path.name in EXCLUDE_FILE_NAMES:
        return False

    for part in path.parts:
        if part in EXCLUDE_DIR_NAMES:
            return False

    return path.is_file()


def write_managed_text(path: Path, content: str) -> None:
    """
    Write managed text documentation.

    This overwrites managed documentation files so repository documentation
    stays consistent with the current workflow.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def missing_files(paths: Iterable[Path]) -> list[Path]:
    """Return files from a path list that do not exist."""
    return [path for path in paths if not path.exists()]


def paths_to_relative(paths: Iterable[Path]) -> list[str]:
    """Return repository-relative paths for a list of Path objects."""
    return [relative(path) for path in paths]


# -----------------------------------------------------------------------------
# Directory setup and validation
# -----------------------------------------------------------------------------

def ensure_directories() -> None:
    """Create the standard project directory structure."""
    for directory in STANDARD_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


def verify_required_files() -> dict[str, list[Path]]:
    """
    Verify expected project files.

    Returns a dictionary of missing files by category. The workflow treats
    missing raw files as fatal, because downstream steps cannot run without
    input data. Other categories are documented for final review.
    """
    return {
        "root_files": missing_files(EXPECTED_ROOT_FILES),
        "raw_files": missing_files(EXPECTED_RAW_FILES),
        "processed_files": missing_files(EXPECTED_PROCESSED_FILES),
        "script_files": missing_files(EXPECTED_SCRIPT_FILES),
        "result_files": missing_files(EXPECTED_RESULT_FILES),
        "figure_files": missing_files(EXPECTED_FIGURE_FILES),
        "doc_files": missing_files(EXPECTED_DOC_FILES),
        "metadata_files": missing_files(EXPECTED_METADATA_FILES),
    }


# -----------------------------------------------------------------------------
# README files for artifact directories
# -----------------------------------------------------------------------------

def write_directory_readmes() -> None:
    """Write short README files for major artifact directories."""

    readmes = {
        RAW_DIR / "README.md": """# Raw Data

This directory contains source-level data acquired from external providers.

Expected files:
- `fred_dff_raw.json`: Raw JSON response from the FRED API for the Federal Funds Effective Rate (`DFF`) series.
- `fred_dff.csv`: CSV version of the FRED observations for easier inspection.
- `sp500_raw.csv`: Raw S&P 500 index data acquired through `yfinance`.
- `CHECKSUMS.sha256`: SHA-256 checksums for the raw data files.
- `acquisition_metadata.json`: Metadata describing when and how raw data were acquired.

Raw files should not be manually edited. Downstream scripts read these files and write cleaned or derived outputs to `data/processed/`, `results/`, and `figures/`.
""",
        PROCESSED_DIR / "README.md": """# Processed Data

This directory contains cleaned, standardized, and integrated datasets generated by project scripts.

Expected files:
- `fred_dff_clean.csv`: Cleaned Federal Funds Effective Rate data.
- `sp500_clean.csv`: Cleaned S&P 500 trading-day data.
- `integrated_fred_sp500.csv`: Final integrated dataset used for analysis and visualization.

Files in this directory are generated artifacts and can be recreated from the raw data through the Snakemake workflow.
""",
        RESULTS_DIR / "README.md": """# Results

This directory contains machine-readable tabular outputs generated by the workflow.

Expected files:
- `storage_status.json`
- `checksum_verification.csv`
- `data_quality_summary.csv`
- `missingness_summary.csv`
- `date_coverage_summary.csv`
- `schema_summary.csv`
- `temporal_alignment_profile.csv`
- `cleaning_summary.csv`
- `cleaning_decisions.csv`
- `integration_summary.csv`
- `integration_quality_checks.csv`
- `summary_statistics.csv`
- `correlation_results.csv`
- `rate_change_analysis.csv`
- `period_summary.csv`
- `analysis_findings_summary.csv`
- `visualization_summary.csv`

These files provide numeric evidence used in the final project report.
""",
        FIGURES_DIR / "README.md": """# Figures

This directory contains visualizations generated from the integrated dataset.

Expected files:
- `fed_funds_rate_trend.png`
- `sp500_close_trend.png`
- `sp500_daily_returns.png`
- `fed_funds_rate_vs_sp500_return.png`
- `average_return_by_rate_direction.png`

Figures are generated by `scripts/visualize_data.py` and should not be edited manually.
""",
        DOCS_DIR / "README.md": """# Documentation

This directory contains supporting documentation for the project.

Expected files:
- `DATA_STRUCTURE.md`: Repository structure and storage strategy.
- `file_inventory.csv`: Machine-readable inventory of project files.
- `WORKFLOW.md`: Snakemake workflow and reproduction instructions.
- `data_dictionary.md`: Definitions of fields in the cleaned and integrated datasets.
- `data_quality_profile.md`: Raw data quality profiling documentation.
- `cleaning_provenance.md`: Explanation of cleaning steps and provenance decisions.
- `INTEGRATION_SUMMARY.md`: Documentation of the data integration strategy and merge results.
- `ANALYSIS_SUMMARY.md`: Documentation of numeric analysis outputs.
- `VISUALIZATION_SUMMARY.md`: Documentation of generated figures.
""",
        METADATA_DIR / "README.md": """# Metadata

This directory contains machine-readable project metadata.

Expected files:
- `metadata.json`: Descriptive project metadata following a lightweight Schema.org/DCAT-style structure.

The metadata file supports FAIR principles by making the project easier to find, understand, and reuse.
""",
    }

    for path, content in readmes.items():
        write_managed_text(path, content)


# -----------------------------------------------------------------------------
# Documentation generation
# -----------------------------------------------------------------------------

def write_data_structure_doc() -> Path:
    """Write a detailed markdown document describing storage and organization."""

    doc_path = DOCS_DIR / "DATA_STRUCTURE.md"

    content = f"""# Data Structure and Organization

Generated by `scripts/storage_and_organization.py` on `{utc_now_iso()}`.

## Purpose

This repository is organized to support transparency, provenance tracking, and reproducibility for the IS 477 final project. The project separates raw data, processed data, scripts, results, figures, documentation, and metadata so that each stage of the data lifecycle can be inspected and rerun.

## Directory Layout

Indented directory structure:

    Team-Accountants/
    ├── README.md
    ├── Snakefile
    ├── requirements.txt
    ├── pip_freeze.txt
    ├── LICENSE
    ├── LICENSE-DOCUMENTATION.md
    ├── CITATION.cff
    ├── ProjectPlan.md
    ├── StatusReport.md
    ├── scripts/
    │   ├── acquire_data.py
    │   ├── storage_and_organization.py
    │   ├── data_quality.py
    │   ├── data_cleaning.py
    │   ├── data_integration.py
    │   ├── analyze_data.py
    │   └── visualize_data.py
    ├── data/
    │   ├── raw/
    │   │   ├── fred_dff_raw.json
    │   │   ├── fred_dff.csv
    │   │   ├── sp500_raw.csv
    │   │   ├── CHECKSUMS.sha256
    │   │   └── acquisition_metadata.json
    │   └── processed/
    │       ├── fred_dff_clean.csv
    │       ├── sp500_clean.csv
    │       └── integrated_fred_sp500.csv
    ├── results/
    │   ├── storage_status.json
    │   ├── checksum_verification.csv
    │   ├── data_quality_summary.csv
    │   ├── missingness_summary.csv
    │   ├── date_coverage_summary.csv
    │   ├── schema_summary.csv
    │   ├── temporal_alignment_profile.csv
    │   ├── cleaning_summary.csv
    │   ├── cleaning_decisions.csv
    │   ├── integration_summary.csv
    │   ├── integration_quality_checks.csv
    │   ├── summary_statistics.csv
    │   ├── correlation_results.csv
    │   ├── rate_change_analysis.csv
    │   ├── period_summary.csv
    │   ├── analysis_findings_summary.csv
    │   └── visualization_summary.csv
    ├── figures/
    │   ├── fed_funds_rate_trend.png
    │   ├── sp500_close_trend.png
    │   ├── sp500_daily_returns.png
    │   ├── fed_funds_rate_vs_sp500_return.png
    │   └── average_return_by_rate_direction.png
    ├── docs/
    │   ├── DATA_STRUCTURE.md
    │   ├── file_inventory.csv
    │   ├── WORKFLOW.md
    │   ├── data_dictionary.md
    │   ├── data_quality_profile.md
    │   ├── cleaning_provenance.md
    │   ├── INTEGRATION_SUMMARY.md
    │   ├── ANALYSIS_SUMMARY.md
    │   └── VISUALIZATION_SUMMARY.md
    └── metadata/
        └── metadata.json

Some files listed above are generated by workflow steps and may not exist until the full workflow has been run.

## Storage Strategy

### `data/raw/`

The `data/raw/` directory stores source-level data acquired from external providers. Raw files are preserved for transparency and should not be manually edited. The project uses these files as the starting point for quality profiling, cleaning, integration, analysis, and visualization.

Expected raw files:
- `fred_dff_raw.json`
- `fred_dff.csv`
- `sp500_raw.csv`
- `CHECKSUMS.sha256`
- `acquisition_metadata.json`

### `data/processed/`

The `data/processed/` directory stores cleaned and integrated datasets generated by scripts. These files are derived artifacts and can be recreated from the raw files.

Expected processed files:
- `fred_dff_clean.csv`
- `sp500_clean.csv`
- `integrated_fred_sp500.csv`

### `scripts/`

The `scripts/` directory stores executable Python scripts used in the workflow. These scripts use repository-relative paths so that the workflow can be rerun on another machine.

Expected script sequence:
1. `acquire_data.py` for optional live acquisition.
2. `data_quality.py` for raw data quality profiling.
3. `data_cleaning.py` for cleaning and standardization.
4. `data_integration.py` for date-based integration.
5. `analyze_data.py` for numeric exploratory analysis.
6. `visualize_data.py` for generated figures.
7. `storage_and_organization.py` for repository documentation and inventory.

### `results/`

The `results/` directory stores machine-readable tabular outputs, including checksum verification, quality summaries, cleaning summaries, integration summaries, descriptive statistics, correlations, and visualization summaries.

### `figures/`

The `figures/` directory stores generated visualizations used in the final report.

### `docs/`

The `docs/` directory stores human-readable project documentation, including workflow instructions, data structure notes, data dictionaries, quality profiles, cleaning provenance, integration summaries, analysis summaries, and visualization summaries.

### `metadata/`

The `metadata/` directory stores machine-readable descriptive metadata for the project.

## Workflow Automation

The project uses Snakemake for workflow automation. The workflow file is:

- `Snakefile`

The recommended frozen-data reproduction command is:

    snakemake --cores 1

The optional live-data command is:

    snakemake --cores 1 --config mode=live --forceall

Frozen mode uses the raw data already included in `data/raw/`. Live mode reacquires data and may produce different results because external data sources update over time.

## Naming Conventions

The project uses the following naming conventions:

- Lowercase file names for generated data artifacts.
- Words separated with underscores.
- Source and content reflected in file names.
- Raw files include `_raw` when appropriate.
- Cleaned files include `_clean`.
- Integrated files include `integrated`.
- Documentation files use descriptive uppercase names when they summarize workflow stages.

Examples:
- `fred_dff_raw.json`
- `fred_dff_clean.csv`
- `sp500_raw.csv`
- `sp500_clean.csv`
- `integrated_fred_sp500.csv`
- `data_quality_summary.csv`
- `INTEGRATION_SUMMARY.md`

## Provenance Strategy

The workflow preserves provenance through:

1. Separate raw and processed data folders.
2. SHA-256 checksums for raw input files.
3. Checksum verification output in `results/checksum_verification.csv`.
4. Script-generated outputs rather than manual editing.
5. File inventory documentation.
6. Cleaning, integration, analysis, and visualization documentation.
7. Snakemake workflow automation through `Snakefile`.
8. Reproducible commands described in `docs/WORKFLOW.md` and the final `README.md`.

## Important Integration Note

The project integrates two time-series datasets using the `date` field. However, the Federal Funds Effective Rate is reported on a calendar-day basis, while the S&P 500 is observed only on trading days. The final integrated dataset uses S&P 500 trading days as the base timeline and attaches the corresponding Federal Funds Effective Rate for those dates. This avoids creating artificial stock market observations for weekends and holidays.
"""

    write_managed_text(doc_path, content)
    return doc_path


def generate_file_inventory() -> Path:
    """
    Generate a CSV inventory of key project files.

    The inventory includes file paths, directories, suffixes, file sizes, and
    last modified times. It is useful for transparency and final review.
    """
    inventory_path = DOCS_DIR / "file_inventory.csv"

    rows: list[dict[str, str | int]] = []

    for base_dir in INVENTORY_TARGET_DIRS:
        if not base_dir.exists():
            continue

        for path in sorted(base_dir.rglob("*")):
            if not should_include_file(path):
                continue

            stat = path.stat()

            rows.append(
                {
                    "relative_path": relative(path),
                    "parent_directory": relative(path.parent),
                    "file_name": path.name,
                    "suffix": path.suffix,
                    "size_bytes": stat.st_size,
                    "size_label": file_size_label(stat.st_size),
                    "modified_time_utc": datetime.fromtimestamp(
                        stat.st_mtime,
                        tz=timezone.utc,
                    ).isoformat(),
                }
            )

    with inventory_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "relative_path",
                "parent_directory",
                "file_name",
                "suffix",
                "size_bytes",
                "size_label",
                "modified_time_utc",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return inventory_path


def write_storage_status_report(missing_by_category: dict[str, list[Path]]) -> Path:
    """Write a JSON status report for storage validation."""

    status_path = RESULTS_DIR / "storage_status.json"

    missing_relative = {
        category: paths_to_relative(paths)
        for category, paths in missing_by_category.items()
    }

    required_missing_count = sum(
        len(paths)
        for category, paths in missing_by_category.items()
        if category in {
            "raw_files",
            "script_files",
        }
    )

    total_missing_count = sum(len(paths) for paths in missing_by_category.values())

    status = {
        "generated_at_utc": utc_now_iso(),
        "project_root": str(PROJECT_ROOT),
        "standard_directories": paths_to_relative(STANDARD_DIRECTORIES),
        "expected_root_files": paths_to_relative(EXPECTED_ROOT_FILES),
        "expected_raw_files": paths_to_relative(EXPECTED_RAW_FILES),
        "expected_processed_files": paths_to_relative(EXPECTED_PROCESSED_FILES),
        "expected_script_files": paths_to_relative(EXPECTED_SCRIPT_FILES),
        "expected_result_files": paths_to_relative(EXPECTED_RESULT_FILES),
        "expected_figure_files": paths_to_relative(EXPECTED_FIGURE_FILES),
        "expected_doc_files": paths_to_relative(EXPECTED_DOC_FILES),
        "expected_metadata_files": paths_to_relative(EXPECTED_METADATA_FILES),
        "missing_files_by_category": missing_relative,
        "total_missing_file_count": total_missing_count,
        "status": "ok" if required_missing_count == 0 else "missing_required_files",
        "note": (
            "Missing root, result, figure, doc, or metadata files may indicate "
            "that optional documentation or later workflow outputs have not yet "
            "been generated. Missing raw or script files prevent reproduction."
        ),
    }

    with status_path.open("w", encoding="utf-8") as file:
        json.dump(status, file, indent=2)

    return status_path


def print_missing_summary(missing_by_category: dict[str, list[Path]]) -> None:
    """Print missing-file summary to the console."""
    any_missing = False

    for category, paths in missing_by_category.items():
        if not paths:
            continue

        any_missing = True
        print(f"\nMissing {category}:")
        for path in paths:
            print(f"- {relative(path)}")

    if not any_missing:
        print("All expected files are present.")


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def main() -> None:
    """Run storage setup and documentation generation."""

    print("=" * 72)
    print("IS 477 Final Project: Storage and Organization")
    print("=" * 72)

    ensure_directories()
    print("Standard directories checked or created.")

    missing_by_category = verify_required_files()
    print_missing_summary(missing_by_category)

    write_directory_readmes()
    print("Directory README files written.")

    structure_doc = write_data_structure_doc()
    print(f"Data structure documentation written to: {relative(structure_doc)}")

    inventory_file = generate_file_inventory()
    print(f"File inventory written to: {relative(inventory_file)}")

    status_report = write_storage_status_report(missing_by_category)
    print(f"Storage status report written to: {relative(status_report)}")

    print("\nStorage and organization step complete.")
    print("=" * 72)

    fatal_missing = (
        missing_by_category["raw_files"]
        + missing_by_category["script_files"]
    )

    if fatal_missing:
        missing_list = "\n".join(f"- {relative(path)}" for path in fatal_missing)
        raise FileNotFoundError(
            "One or more required raw or script files are missing:\n"
            f"{missing_list}\n"
            "Run the relevant workflow steps before continuing."
        )


if __name__ == "__main__":
    main()