# Data Structure and Organization

## Directory layout

- `data/raw/`
  - Original data acquired from external sources
  - Includes source-preserving files and integrity checksums
- `data/processed/`
  - Cleaned, standardized, and integrated datasets
- `data/output/`
  - Analysis outputs such as tables, charts, and derived results
- `docs/`
  - Supporting project documentation

## Naming conventions

- Lowercase file names
- Words separated with underscores
- Source and content reflected in file names
- Examples:
  - `fred_dff_raw.json`
  - `fred_dff.csv`
  - `sp500_raw.csv`

## Storage strategy

This project separates raw, processed, and output artifacts to support:
- transparency
- reproducibility
- easier workflow automation
- clearer provenance tracking
