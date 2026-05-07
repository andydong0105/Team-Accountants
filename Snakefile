# Snakefile
#
# IS 477 Final Project Workflow
#
# Default frozen mode:
#   snakemake --cores 1
#
# This uses the frozen raw data already stored in data/raw/.
# It does NOT rerun data acquisition.
#
# Full forced rebuild from frozen raw data:
#   snakemake --cores 1 --forceall
#
# This reruns data quality, cleaning, integration, analysis, visualization,
# metadata generation, and storage documentation from the included raw files.
# It still does NOT rerun data acquisition.
#
# Optional live mode:
#   snakemake --cores 1 --config mode=live --forceall
#
# This reacquires the latest available data and then reruns the full workflow,
# including live-mode-aware metadata generation.
#
# Recommended notebook command:
#   python -m snakemake --cores 1 --config python=/path/to/python
#
# Optional dry run:
#   snakemake --cores 1 -n
#
# Optional DAG:
#   snakemake --dag | dot -Tpng > workflow_dag.png


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

MODE = config.get("mode", "frozen")
PYTHON = config.get("python", "python3")

if MODE not in ["frozen", "live"]:
    raise ValueError("Invalid mode. Use mode=frozen or mode=live.")


# -----------------------------------------------------------------------------
# Raw data files
# -----------------------------------------------------------------------------

RAW_FILES = [
    "data/raw/fred_dff_raw.json",
    "data/raw/fred_dff.csv",
    "data/raw/sp500_raw.csv",
    "data/raw/CHECKSUMS.sha256",
    "data/raw/acquisition_metadata.json",
]

ACQUIRE_MARKER = "results/provenance/acquire_data.done"


# In frozen mode, raw files are treated as existing input files.
# In live mode, raw files are produced by the acquire_data rule.
if MODE == "live":
    RAW_INPUTS = RAW_FILES + [ACQUIRE_MARKER]
else:
    RAW_INPUTS = RAW_FILES


# -----------------------------------------------------------------------------
# Workflow output groups
# -----------------------------------------------------------------------------

DATA_QUALITY_OUTPUTS = [
    "results/data_quality_summary.csv",
    "results/missingness_summary.csv",
    "results/date_coverage_summary.csv",
    "results/schema_summary.csv",
    "results/temporal_alignment_profile.csv",
    "results/checksum_verification.csv",
    "docs/data_quality_profile.md",
]

CLEANING_OUTPUTS = [
    "data/processed/fred_dff_clean.csv",
    "data/processed/sp500_clean.csv",
    "results/cleaning_summary.csv",
    "results/cleaning_decisions.csv",
    "docs/cleaning_provenance.md",
]

INTEGRATION_OUTPUTS = [
    "data/processed/integrated_fred_sp500.csv",
    "results/integration_summary.csv",
    "results/integration_quality_checks.csv",
    "docs/INTEGRATION_SUMMARY.md",
]

ANALYSIS_OUTPUTS = [
    "results/summary_statistics.csv",
    "results/correlation_results.csv",
    "results/rate_change_analysis.csv",
    "results/period_summary.csv",
    "results/analysis_findings_summary.csv",
    "docs/ANALYSIS_SUMMARY.md",
]

VISUALIZATION_OUTPUTS = [
    "figures/fed_funds_rate_trend.png",
    "figures/sp500_close_trend.png",
    "figures/sp500_daily_returns.png",
    "figures/fed_funds_rate_vs_sp500_return.png",
    "figures/average_return_by_rate_direction.png",
    "results/visualization_summary.csv",
    "docs/VISUALIZATION_SUMMARY.md",
]

METADATA_OUTPUTS = [
    "metadata/metadata.json",
]

STORAGE_OUTPUTS = [
    "results/storage_status.json",
    "docs/DATA_STRUCTURE.md",
    "docs/file_inventory.csv",
    "data/raw/README.md",
    "data/processed/README.md",
    "results/README.md",
    "figures/README.md",
    "docs/README.md",
    "metadata/README.md",
]


# -----------------------------------------------------------------------------
# Default target
# -----------------------------------------------------------------------------

rule run_all:
    input:
        DATA_QUALITY_OUTPUTS,
        CLEANING_OUTPUTS,
        INTEGRATION_OUTPUTS,
        ANALYSIS_OUTPUTS,
        VISUALIZATION_OUTPUTS,
        METADATA_OUTPUTS,
        STORAGE_OUTPUTS


# -----------------------------------------------------------------------------
# Optional live data acquisition
# -----------------------------------------------------------------------------

if MODE == "live":

    rule acquire_data:
        input:
            script="scripts/acquire_data.py"
        output:
            raw_files=RAW_FILES,
            marker=ACQUIRE_MARKER
        shell:
            """
            mkdir -p results/provenance
            DATA_MODE=live {PYTHON} scripts/acquire_data.py
            touch {output.marker}
            """


# -----------------------------------------------------------------------------
# Raw data quality profiling
# -----------------------------------------------------------------------------

rule data_quality:
    input:
        raw_inputs=RAW_INPUTS,
        script="scripts/data_quality.py"
    output:
        DATA_QUALITY_OUTPUTS
    shell:
        """
        {PYTHON} scripts/data_quality.py
        """


# -----------------------------------------------------------------------------
# Data cleaning
# -----------------------------------------------------------------------------

rule data_cleaning:
    input:
        raw_inputs=RAW_INPUTS,
        quality_outputs=DATA_QUALITY_OUTPUTS,
        script="scripts/data_cleaning.py"
    output:
        CLEANING_OUTPUTS
    shell:
        """
        {PYTHON} scripts/data_cleaning.py
        """


# -----------------------------------------------------------------------------
# Data integration
# -----------------------------------------------------------------------------

rule data_integration:
    input:
        cleaned_fred="data/processed/fred_dff_clean.csv",
        cleaned_sp500="data/processed/sp500_clean.csv",
        cleaning_outputs=CLEANING_OUTPUTS,
        script="scripts/data_integration.py"
    output:
        INTEGRATION_OUTPUTS
    shell:
        """
        {PYTHON} scripts/data_integration.py
        """


# -----------------------------------------------------------------------------
# Data analysis
# -----------------------------------------------------------------------------

rule analyze_data:
    input:
        integrated="data/processed/integrated_fred_sp500.csv",
        integration_outputs=INTEGRATION_OUTPUTS,
        script="scripts/analyze_data.py"
    output:
        ANALYSIS_OUTPUTS
    shell:
        """
        {PYTHON} scripts/analyze_data.py
        """


# -----------------------------------------------------------------------------
# Visualization
# -----------------------------------------------------------------------------

rule visualize_data:
    input:
        integrated="data/processed/integrated_fred_sp500.csv",
        rate_change_analysis="results/rate_change_analysis.csv",
        correlation_results="results/correlation_results.csv",
        analysis_outputs=ANALYSIS_OUTPUTS,
        script="scripts/visualize_data.py"
    output:
        VISUALIZATION_OUTPUTS
    shell:
        """
        {PYTHON} scripts/visualize_data.py
        """


# -----------------------------------------------------------------------------
# Machine-readable metadata generation
# -----------------------------------------------------------------------------

rule update_metadata:
    input:
        integrated="data/processed/integrated_fred_sp500.csv",
        raw_inputs=RAW_INPUTS,
        quality_outputs=DATA_QUALITY_OUTPUTS,
        cleaning_outputs=CLEANING_OUTPUTS,
        integration_outputs=INTEGRATION_OUTPUTS,
        analysis_outputs=ANALYSIS_OUTPUTS,
        visualization_outputs=VISUALIZATION_OUTPUTS,
        script="scripts/update_metadata.py"
    output:
        METADATA_OUTPUTS
    shell:
        """
        {PYTHON} scripts/update_metadata.py
        """


# -----------------------------------------------------------------------------
# Storage and organization documentation
# -----------------------------------------------------------------------------

rule storage_and_organization:
    input:
        raw_inputs=RAW_INPUTS,
        quality_outputs=DATA_QUALITY_OUTPUTS,
        cleaning_outputs=CLEANING_OUTPUTS,
        integration_outputs=INTEGRATION_OUTPUTS,
        analysis_outputs=ANALYSIS_OUTPUTS,
        visualization_outputs=VISUALIZATION_OUTPUTS,
        metadata_outputs=METADATA_OUTPUTS,
        script="scripts/storage_and_organization.py"
    output:
        STORAGE_OUTPUTS
    shell:
        """
        {PYTHON} scripts/storage_and_organization.py
        """