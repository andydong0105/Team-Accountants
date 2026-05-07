# Workflow Automation and Provenance

This project uses **Snakemake** to automate the end-to-end workflow for the IS 477 final project. The workflow coordinates raw data acquisition when needed, raw data quality profiling, data cleaning, data integration, analysis, visualization, machine-readable metadata generation, and repository storage documentation.

The main workflow file is located at:

```text
Snakefile
````

The workflow is designed to support two modes:

1. **Frozen mode**: Uses the raw data files already stored in `data/raw/`. This is the default mode and is the recommended mode for reproducing the submitted final project results.
2. **Live mode**: Reacquires updated data from the original sources before rerunning the full workflow. This mode may produce different results because the source datasets may update over time.

---

## 1. Workflow Overview

The project workflow follows this sequence:

1. `data_quality`
2. `data_cleaning`
3. `data_integration`
4. `analyze_data`
5. `visualize_data`
6. `update_metadata`
7. `storage_and_organization`
8. `run_all`

In **live mode**, the workflow also runs:

```text
acquire_data
```

before the downstream profiling, cleaning, integration, analysis, visualization, and documentation steps.

The default target rule is:

```text
run_all
```

This means that running Snakemake from the repository root will attempt to produce all final expected outputs listed in the `run_all` rule.

---

## 2. Recommended Reproduction Mode: Frozen Raw Data

The submitted project results are based on the frozen raw data already included in the repository under:

```text
data/raw/
```

To reproduce the submitted results, run the following command from the repository root:

```bash
snakemake --cores 1
```

This command uses the existing raw files and regenerates downstream outputs if they are missing or outdated.

Frozen mode is the recommended reproduction path because it avoids differences caused by updated external data sources. In this mode, no FRED API key is required because the workflow uses the raw input files already included in the repository.

---

## 3. Full Forced Rebuild from Frozen Raw Data

To force Snakemake to rerun all workflow rules using the frozen raw data, run:

```bash
snakemake --cores 1 --forceall
```

This is useful for testing whether the full workflow can be regenerated from the existing raw files.

This mode does not reacquire data from the internet unless the workflow is explicitly configured to use live mode.

---

## 4. Optional Live Data Mode

To reacquire the latest available data from the original sources and rerun the full workflow, use:

```bash
snakemake --cores 1 --config mode=live --forceall
```

Live mode runs the acquisition script:

```text
scripts/acquire_data.py
```

This script retrieves:

* Federal Funds Effective Rate data from the FRED API
* S&P 500 data through `yfinance`

Live mode may produce different row counts, date ranges, checksums, analysis results, visualizations, and metadata because the source datasets may update after the final project submission.

For this reason, the final report should be interpreted as describing the frozen submitted version unless otherwise stated.

---

## 5. Dry Run

To check the workflow structure without executing any jobs, run:

```bash
snakemake --cores 1 -n
```

A dry run is useful for confirming that Snakemake can find the `Snakefile`, build the DAG, and identify which jobs would run.

---

## 6. Workflow Rules

### `run_all`

The `run_all` rule is the default rule. It does not run a script directly. Instead, it lists all final outputs that should exist after the workflow completes.

Main expected outputs include:

```text
results/data_quality_summary.csv
results/missingness_summary.csv
results/date_coverage_summary.csv
results/schema_summary.csv
results/temporal_alignment_profile.csv
results/checksum_verification.csv
docs/data_quality_profile.md

data/processed/fred_dff_clean.csv
data/processed/sp500_clean.csv
results/cleaning_summary.csv
results/cleaning_decisions.csv
docs/cleaning_provenance.md

data/processed/integrated_fred_sp500.csv
results/integration_summary.csv
results/integration_quality_checks.csv
docs/INTEGRATION_SUMMARY.md

results/summary_statistics.csv
results/correlation_results.csv
results/rate_change_analysis.csv
results/period_summary.csv
results/analysis_findings_summary.csv
docs/ANALYSIS_SUMMARY.md

figures/fed_funds_rate_trend.png
figures/sp500_close_trend.png
figures/sp500_daily_returns.png
figures/fed_funds_rate_vs_sp500_return.png
figures/average_return_by_rate_direction.png
results/visualization_summary.csv
docs/VISUALIZATION_SUMMARY.md

metadata/metadata.json

results/storage_status.json
docs/DATA_STRUCTURE.md
docs/file_inventory.csv
data/raw/README.md
data/processed/README.md
results/README.md
figures/README.md
docs/README.md
metadata/README.md
```

---

### `acquire_data`

This rule is used only when running the workflow in live mode.

Script:

```text
scripts/acquire_data.py
```

Main outputs:

```text
data/raw/fred_dff_raw.json
data/raw/fred_dff.csv
data/raw/sp500_raw.csv
data/raw/CHECKSUMS.sha256
data/raw/acquisition_metadata.json
results/provenance/acquire_data.done
```

Purpose:

* Programmatically acquires raw data.
* Saves a source-preserving raw JSON response for FRED.
* Saves raw CSV files for FRED and S&P 500.
* Generates SHA-256 checksums for raw files.
* Records acquisition metadata.
* Creates a provenance marker showing that live acquisition completed.

Notes:

* In frozen mode, this rule is not needed because raw data files are already included in the repository.
* In live mode, this rule requires access to the internet.
* FRED acquisition may require a FRED API key through either the `FRED_API_KEY` environment variable or a local `apikey.txt` file.
* A local `apikey.txt` file should not be committed to GitHub.

---

### `data_quality`

Script:

```text
scripts/data_quality.py
```

Inputs:

```text
data/raw/fred_dff.csv
data/raw/sp500_raw.csv
data/raw/CHECKSUMS.sha256
```

In live mode, the rule also depends on the live acquisition marker:

```text
results/provenance/acquire_data.done
```

Outputs:

```text
results/data_quality_summary.csv
results/missingness_summary.csv
results/date_coverage_summary.csv
results/schema_summary.csv
results/temporal_alignment_profile.csv
results/checksum_verification.csv
docs/data_quality_profile.md
```

Purpose:

* Profiles raw data before cleaning.
* Verifies raw-file checksums.
* Assesses schema, missingness, date coverage, duplicate dates, invalid dates, numeric validity, and temporal alignment.
* Documents that FRED is a calendar-day series while the S&P 500 is a trading-day series.
* Identifies the temporal alignment issue that later drives the integration strategy.

This rule does not depend on any cleaned or integrated data.

---

### `data_cleaning`

Script:

```text
scripts/data_cleaning.py
```

Inputs:

```text
data/raw/fred_dff.csv
data/raw/sp500_raw.csv
results/data_quality_summary.csv
results/missingness_summary.csv
results/date_coverage_summary.csv
results/schema_summary.csv
results/temporal_alignment_profile.csv
results/checksum_verification.csv
docs/data_quality_profile.md
```

Outputs:

```text
data/processed/fred_dff_clean.csv
data/processed/sp500_clean.csv
results/cleaning_summary.csv
results/cleaning_decisions.csv
docs/cleaning_provenance.md
```

Purpose:

* Standardizes column names.
* Parses date fields.
* Converts numeric fields to stable numeric types.
* Renames variables to analysis-ready names.
* Removes invalid, missing, or duplicate core records if present.
* Retains FRED weekend observations because they are expected for calendar-day data.
* Retains and flags S&P 500 zero-volume rows because volume is not a primary analysis variable.
* Documents cleaning decisions and cleaning provenance.

---

### `data_integration`

Script:

```text
scripts/data_integration.py
```

Inputs:

```text
data/processed/fred_dff_clean.csv
data/processed/sp500_clean.csv
results/cleaning_summary.csv
results/cleaning_decisions.csv
docs/cleaning_provenance.md
```

Outputs:

```text
data/processed/integrated_fred_sp500.csv
results/integration_summary.csv
results/integration_quality_checks.csv
docs/INTEGRATION_SUMMARY.md
```

Purpose:

* Integrates cleaned FRED and S&P 500 datasets using `date` as the key.
* Uses S&P 500 trading days as the base timeline.
* Restricts the S&P 500 data to the date range covered by FRED.
* Avoids creating artificial stock-market observations for weekends or holidays.
* Calculates S&P 500 daily returns and log returns.
* Calculates Federal Funds Rate changes and rate-change direction.
* Produces an analysis-ready integrated dataset.

Final integrated columns include:

```text
date
sp500_close
sp500_daily_return
sp500_log_return
sp500_zero_volume_flag
federal_funds_rate
federal_funds_rate_change
federal_funds_rate_direction
```

---

### `analyze_data`

Script:

```text
scripts/analyze_data.py
```

Input:

```text
data/processed/integrated_fred_sp500.csv
```

Outputs:

```text
results/summary_statistics.csv
results/correlation_results.csv
results/rate_change_analysis.csv
results/period_summary.csv
results/analysis_findings_summary.csv
docs/ANALYSIS_SUMMARY.md
```

Purpose:

* Computes descriptive statistics.
* Calculates exploratory correlations.
* Summarizes S&P 500 returns by Federal Funds Rate direction.
* Summarizes long-run patterns by period and interest-rate environment.
* Produces numeric findings for the final report.

The analysis is exploratory and does not establish causality.

---

### `visualize_data`

Script:

```text
scripts/visualize_data.py
```

Inputs:

```text
data/processed/integrated_fred_sp500.csv
results/rate_change_analysis.csv
results/correlation_results.csv
results/summary_statistics.csv
results/analysis_findings_summary.csv
docs/ANALYSIS_SUMMARY.md
```

Outputs:

```text
figures/fed_funds_rate_trend.png
figures/sp500_close_trend.png
figures/sp500_daily_returns.png
figures/fed_funds_rate_vs_sp500_return.png
figures/average_return_by_rate_direction.png
results/visualization_summary.csv
docs/VISUALIZATION_SUMMARY.md
```

Purpose:

* Generates visualizations for the final project report.
* Plots Federal Funds Rate trends.
* Plots S&P 500 closing levels.
* Plots S&P 500 daily returns.
* Visualizes the exploratory relationship between interest rates and market returns.
* Summarizes average market returns by Federal Funds Rate direction.

---

### `update_metadata`

Script:

```text
scripts/update_metadata.py
```

Inputs:

```text
data/processed/integrated_fred_sp500.csv

data/raw/fred_dff_raw.json
data/raw/fred_dff.csv
data/raw/sp500_raw.csv
data/raw/CHECKSUMS.sha256
data/raw/acquisition_metadata.json

results/data_quality_summary.csv
results/missingness_summary.csv
results/date_coverage_summary.csv
results/schema_summary.csv
results/temporal_alignment_profile.csv
results/checksum_verification.csv
docs/data_quality_profile.md

data/processed/fred_dff_clean.csv
data/processed/sp500_clean.csv
results/cleaning_summary.csv
results/cleaning_decisions.csv
docs/cleaning_provenance.md

results/integration_summary.csv
results/integration_quality_checks.csv
docs/INTEGRATION_SUMMARY.md

results/summary_statistics.csv
results/correlation_results.csv
results/rate_change_analysis.csv
results/period_summary.csv
results/analysis_findings_summary.csv
docs/ANALYSIS_SUMMARY.md

figures/fed_funds_rate_trend.png
figures/sp500_close_trend.png
figures/sp500_daily_returns.png
figures/fed_funds_rate_vs_sp500_return.png
figures/average_return_by_rate_direction.png
results/visualization_summary.csv
docs/VISUALIZATION_SUMMARY.md
```

Output:

```text
metadata/metadata.json
```

Purpose:

* Generates machine-readable project metadata.
* Documents the project using Schema.org / DCAT-style fields.
* Records creators, contributors, source datasets, licenses, distributions, variables, software requirements, and workflow components.
* Reads the current integrated dataset to calculate row count, column count, and temporal coverage.
* Keeps metadata consistent with frozen mode and optional live mode outputs.

This rule is important because live mode can change the integrated dataset’s end date, row count, file sizes, and temporal coverage. Generating metadata through a script avoids outdated hard-coded metadata.

---

### `storage_and_organization`

Script:

```text
scripts/storage_and_organization.py
```

Inputs:

* Raw data files
* Data quality outputs
* Cleaning outputs
* Integration outputs
* Analysis outputs
* Visualization outputs
* Metadata output

Outputs:

```text
results/storage_status.json
docs/DATA_STRUCTURE.md
docs/file_inventory.csv
data/raw/README.md
data/processed/README.md
results/README.md
figures/README.md
docs/README.md
metadata/README.md
```

Purpose:

* Verifies required raw files.
* Creates or confirms standard project directories.
* Writes directory-level README files.
* Generates a file inventory.
* Documents the storage and organization strategy.
* Ensures that the metadata folder is included in the documented repository structure.

This rule runs near the end of the workflow so that the file inventory reflects the current state of the repository after analysis, visualization, and metadata generation.

---

## 7. Provenance and Integrity

The workflow preserves provenance in several ways:

1. Raw files are stored separately in `data/raw/`.
2. Cleaned and integrated files are written to `data/processed/`.
3. Results and figures are generated by scripts rather than manually edited.
4. SHA-256 checksums are generated for raw input files.
5. Raw-file checksum verification results are written to:

```text
results/checksum_verification.csv
```

6. Cleaning decisions are documented in:

```text
results/cleaning_decisions.csv
docs/cleaning_provenance.md
```

7. Integration decisions are documented in:

```text
results/integration_summary.csv
docs/INTEGRATION_SUMMARY.md
```

8. Analysis results are documented in:

```text
results/analysis_findings_summary.csv
docs/ANALYSIS_SUMMARY.md
```

9. Visualization outputs are documented in:

```text
results/visualization_summary.csv
docs/VISUALIZATION_SUMMARY.md
```

10. Machine-readable metadata is generated in:

```text
metadata/metadata.json
```

11. Repository structure and file inventory are documented in:

```text
docs/DATA_STRUCTURE.md
docs/file_inventory.csv
```

12. Snakemake records job-level execution metadata in its `.snakemake/` directory when the workflow is run locally.

The `.snakemake/` directory is a local execution artifact and does not need to be included in the final GitHub submission.

---

## 8. Configuration

The workflow supports an optional Snakemake configuration variable:

```text
mode
```

Accepted values:

```text
frozen
live
```

Default value:

```text
frozen
```

Example:

```bash
snakemake --cores 1 --config mode=live --forceall
```

In frozen mode, Snakemake uses the raw files already stored in the repository.

In live mode, Snakemake reruns data acquisition and may overwrite raw files with newly acquired data. Because live mode may change row counts, date ranges, checksums, analysis results, visualizations, and metadata, frozen mode should be used to reproduce the submitted final project results.

The workflow also supports an optional `python` configuration value in the `Snakefile`. This can be useful if a user wants Snakemake to run scripts with a specific Python executable.

Example:

```bash
snakemake --cores 1 --config python=/path/to/python
```

---

## 9. Expected Software Environment

The workflow requires:

* Python 3.10 or higher
* Snakemake
* pandas
* numpy
* matplotlib
* requests
* yfinance

Install project dependencies with:

```bash
pip install -r requirements.txt
```

If Snakemake is not included in the requirements file or is not available in the environment, install it separately:

```bash
pip install snakemake
```

The repository also includes:

```text
pip_freeze.txt
```

This file records the package versions from the development environment and supports more detailed reproducibility.

---

## 10. Common Commands

### Dry run

```bash
snakemake --cores 1 -n
```

### Run default frozen workflow

```bash
snakemake --cores 1
```

### Force full rebuild using frozen raw data

```bash
snakemake --cores 1 --forceall
```

### Reacquire latest data and rebuild

```bash
snakemake --cores 1 --config mode=live --forceall
```

### Run with a specific Python executable

```bash
snakemake --cores 1 --config python=/path/to/python
```

### Unlock the workflow if interrupted

```bash
snakemake --unlock
```

### Generate a workflow DAG

If Graphviz is installed, run:

```bash
snakemake --dag | dot -Tpng > workflow_dag.png
```

---

## 11. Notes for Reproducibility

The final submitted results should be reproduced using frozen mode:

```bash
snakemake --cores 1
```

or, for a complete forced rebuild from included raw files:

```bash
snakemake --cores 1 --forceall
```

Live mode is provided for transparency and extensibility, but it may produce different results after the submission date because external data sources can update.

For grading and reproduction, the frozen raw data in `data/raw/` should be treated as the submitted input dataset.

The expected final integrated dataset is:

```text
data/processed/integrated_fred_sp500.csv
```

For the submitted frozen project, this dataset contains one row per S&P 500 trading day within the FRED date range. The corresponding machine-readable metadata is:

```text
metadata/metadata.json
```

The metadata should report the same temporal coverage and integrated dataset statistics as the current integrated dataset.

---

## 12. Reproduction Checklist

Use the following checklist to verify successful reproduction:

* [ ] Repository is cloned successfully.
* [ ] Python environment is created and activated.
* [ ] Dependencies are installed from `requirements.txt`.
* [ ] Raw input files are present in `data/raw/`.
* [ ] Dry run completes with `snakemake --cores 1 -n`.
* [ ] Frozen workflow completes with `snakemake --cores 1`.
* [ ] Cleaned datasets are present in `data/processed/`.
* [ ] Integrated dataset is present at `data/processed/integrated_fred_sp500.csv`.
* [ ] Analysis outputs are present in `results/`.
* [ ] Visualizations are present in `figures/`.
* [ ] Machine-readable metadata is present at `metadata/metadata.json`.
* [ ] Repository documentation files are present in `docs/`.
* [ ] Metadata temporal coverage matches the integrated dataset date range.
* [ ] No local execution artifacts such as `.snakemake/` are needed for the final GitHub submission.
