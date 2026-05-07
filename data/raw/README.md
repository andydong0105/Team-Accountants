# Raw Data

This directory contains source-level data acquired from external providers.

Expected files:
- `fred_dff_raw.json`: Raw JSON response from the FRED API for the Federal Funds Effective Rate (`DFF`) series.
- `fred_dff.csv`: CSV version of the FRED observations for easier inspection.
- `sp500_raw.csv`: Raw S&P 500 index data acquired through `yfinance`.
- `CHECKSUMS.sha256`: SHA-256 checksums for the raw data files.
- `acquisition_metadata.json`: Metadata describing when and how raw data were acquired.

Raw files should not be manually edited. Downstream scripts read these files and write cleaned or derived outputs to `data/processed/`, `results/`, and `figures/`.
