# Data Dictionary

This data dictionary documents the cleaned and integrated datasets used in the IS 477 final project. Raw source files are preserved in `data/raw/`, cleaned datasets are stored in `data/processed/`, and the final integrated dataset is stored as `data/processed/integrated_fred_sp500.csv`.

## Dataset Files

| File | Description |
|---|---|
| `data/raw/fred_dff.csv` | Raw CSV version of Federal Funds Effective Rate data acquired from FRED. |
| `data/raw/sp500_raw.csv` | Raw S&P 500 data acquired through `yfinance`. |
| `data/processed/fred_dff_clean.csv` | Cleaned Federal Funds Effective Rate dataset. |
| `data/processed/sp500_clean.csv` | Cleaned S&P 500 dataset. |
| `data/processed/integrated_fred_sp500.csv` | Final integrated dataset used for analysis and visualization. |

---

## 1. Cleaned Federal Funds Effective Rate Dataset

**File:** `data/processed/fred_dff_clean.csv`

**Observation unit:** One row per calendar date

**Source:** Federal Reserve Bank of St. Louis, FRED series `DFF`

### Variables

| Variable | Type | Source | Unit | Derived? | Description |
|---|---|---|---|---|---|
| `date` | string, ISO date | FRED | Date, `YYYY-MM-DD` | No | Calendar date of the Federal Funds Effective Rate observation. |
| `federal_funds_rate` | numeric | FRED | Percent | No | Federal Funds Effective Rate for the given date. |

### Notes

The raw FRED file includes `realtime_start` and `realtime_end`, but these fields are not retained in the cleaned analysis file because the project focuses on date-based alignment between interest-rate values and S&P 500 trading days. The raw fields remain preserved in `data/raw/fred_dff.csv`.

FRED DFF is a calendar-day time series. Weekend observations are expected and are not treated as data errors.

---

## 2. Cleaned S&P 500 Dataset

**File:** `data/processed/sp500_clean.csv`

**Observation unit:** One row per S&P 500 trading day

**Source:** Yahoo Finance through the `yfinance` Python package

### Variables

| Variable | Type | Source | Unit | Derived? | Description |
|---|---|---|---|---|---|
| `date` | string, ISO date | Yahoo Finance / yfinance | Date, `YYYY-MM-DD` | No | Trading date for the S&P 500 observation. |
| `sp500_open` | numeric | Yahoo Finance / yfinance | Index level | No | S&P 500 opening index level for the trading day. |
| `sp500_high` | numeric | Yahoo Finance / yfinance | Index level | No | Highest S&P 500 index level recorded for the trading day. |
| `sp500_low` | numeric | Yahoo Finance / yfinance | Index level | No | Lowest S&P 500 index level recorded for the trading day. |
| `sp500_close` | numeric | Yahoo Finance / yfinance | Index level | No | S&P 500 closing index level for the trading day. |
| `sp500_adj_close` | numeric | Yahoo Finance / yfinance | Index level | No | Adjusted closing index level, when available. For index-level data, this is often similar or identical to close. |
| `sp500_volume` | numeric | Yahoo Finance / yfinance | Reported volume | No | Reported trading volume associated with the S&P 500 index record. |
| `sp500_zero_volume_flag` | integer | Project cleaning script | Binary flag | Yes | Equals `1` if `sp500_volume` is zero, and `0` otherwise. This flag documents early historical rows where volume is reported as zero. |

### Notes

The S&P 500 dataset is a trading-day series, not a calendar-day series. Missing calendar dates are expected because the market is closed on weekends and market holidays.

The data quality profile identified zero-volume rows in older historical records. These observations are retained because the price fields remain useful for index-level analysis, while volume is not used as a primary research variable in this project.

---

## 3. Final Integrated Dataset

**File:** `data/processed/integrated_fred_sp500.csv`

**Observation unit:** One row per S&P 500 trading day within the FRED DFF date range

**Integration key:** `date`

**Integration strategy:** The final dataset uses S&P 500 trading days as the base timeline. Federal Funds Effective Rate values are attached to matching trading dates. The workflow does not create artificial stock market observations for weekends or market holidays.

### Variables

| Variable | Type | Source | Unit | Derived? | Description |
|---|---|---|---|---|---|
| `date` | string, ISO date | FRED and S&P 500 | Date, `YYYY-MM-DD` | No | Shared date key used to align the two datasets. In the integrated dataset, each date represents an S&P 500 trading day. |
| `sp500_close` | numeric | Yahoo Finance / yfinance | Index level | No | S&P 500 closing index level on the trading date. |
| `sp500_daily_return` | numeric | Project integration script | Decimal return | Yes | Daily simple return calculated from `sp500_close` as the percentage change from the previous trading day. For example, `0.01` means a 1% daily return. |
| `sp500_log_return` | numeric | Project integration script | Log return | Yes | Daily log return calculated as `log(current sp500_close / previous sp500_close)`. |
| `sp500_zero_volume_flag` | integer | Project cleaning script | Binary flag | Yes | Equals `1` if the original S&P 500 volume value was zero, and `0` otherwise. Retained for transparency. |
| `federal_funds_rate` | numeric | FRED | Percent | No | Federal Funds Effective Rate matched to the S&P 500 trading date. |
| `federal_funds_rate_change` | numeric | Project integration script | Percentage points | Yes | Change in `federal_funds_rate` from the previous integrated trading-day observation. |
| `federal_funds_rate_direction` | string | Project integration script | Category | Yes | Direction of Federal Funds Rate change from the previous integrated observation. Possible values are `increase`, `decrease`, `no_change`, and `first_observation`. |

---

## 4. Derived Variable Definitions

### `sp500_daily_return`

Formula:

```text
sp500_daily_return_t = (sp500_close_t / sp500_close_t-1) - 1
```

Interpretation:

- `0.01` means the S&P 500 increased by 1% from the prior trading day.
- `-0.01` means the S&P 500 decreased by 1% from the prior trading day.
- The first row has a missing value because there is no prior integrated observation.

### `sp500_log_return`

Formula:

```text
sp500_log_return_t = ln(sp500_close_t / sp500_close_t-1)
```

Interpretation:

Log returns are commonly used in time-series analysis because they are additive over time. The first row has a missing value because there is no prior integrated observation.

### `federal_funds_rate_change`

Formula:

```text
federal_funds_rate_change_t = federal_funds_rate_t - federal_funds_rate_t-1
```

Interpretation:

This variable measures the change in the Federal Funds Effective Rate between consecutive integrated trading-day observations. It is measured in percentage points.

### `federal_funds_rate_direction`

Possible values:

| Value | Meaning |
|---|---|
| `increase` | The Federal Funds Rate increased from the previous integrated observation. |
| `decrease` | The Federal Funds Rate decreased from the previous integrated observation. |
| `no_change` | The Federal Funds Rate was unchanged from the previous integrated observation. |
| `first_observation` | First row of the integrated dataset; no prior observation exists for comparison. |

### `sp500_zero_volume_flag`

Possible values:

| Value | Meaning |
|---|---|
| `1` | The original S&P 500 volume field was reported as zero. |
| `0` | The original S&P 500 volume field was not zero. |

This flag is included for transparency. The project does not use volume as a primary analysis variable.

---

## 5. Integration Notes

The shared `date` field enables integration, but the two datasets have different observation schedules:

- FRED DFF is reported on a calendar-day basis.
- S&P 500 data is available only for trading days.

As a result, many FRED dates do not appear in the S&P 500 dataset because they fall on weekends or market holidays. These are expected temporal mismatches, not data collection failures.

The final integrated dataset uses S&P 500 trading days as the base timeline because the analysis focuses on daily market performance. This avoids creating artificial stock market records for non-trading days.

---

## 6. Missing Values

Expected missing values in the integrated dataset:

| Variable | Expected Missingness | Reason |
|---|---|---|
| `sp500_daily_return` | First row only | No previous S&P 500 close exists within the integrated dataset. |
| `sp500_log_return` | First row only | No previous S&P 500 close exists within the integrated dataset. |
| `federal_funds_rate_change` | First row only | No previous Federal Funds Rate exists within the integrated dataset. |

Unexpected missing values in core fields such as `date`, `sp500_close`, and `federal_funds_rate` should be treated as quality issues.

---

## 7. Data Types Summary

| Dataset | Variable | Recommended Type |
|---|---|---|
| Cleaned FRED | `date` | date or string in `YYYY-MM-DD` format |
| Cleaned FRED | `federal_funds_rate` | float |
| Cleaned S&P 500 | `date` | date or string in `YYYY-MM-DD` format |
| Cleaned S&P 500 | `sp500_open` | float |
| Cleaned S&P 500 | `sp500_high` | float |
| Cleaned S&P 500 | `sp500_low` | float |
| Cleaned S&P 500 | `sp500_close` | float |
| Cleaned S&P 500 | `sp500_adj_close` | float |
| Cleaned S&P 500 | `sp500_volume` | float or integer |
| Cleaned S&P 500 | `sp500_zero_volume_flag` | integer |
| Integrated | `date` | date or string in `YYYY-MM-DD` format |
| Integrated | `sp500_close` | float |
| Integrated | `sp500_daily_return` | float |
| Integrated | `sp500_log_return` | float |
| Integrated | `sp500_zero_volume_flag` | integer |
| Integrated | `federal_funds_rate` | float |
| Integrated | `federal_funds_rate_change` | float |
| Integrated | `federal_funds_rate_direction` | string/category |

---

## 8. Source and Provenance

| Dataset | Source | Acquisition Method | Raw File |
|---|---|---|---|
| Federal Funds Effective Rate | Federal Reserve Bank of St. Louis FRED API | `scripts/acquire_data.py` using `requests` | `data/raw/fred_dff_raw.json`, `data/raw/fred_dff.csv` |
| S&P 500 Index | Yahoo Finance through `yfinance` | `scripts/acquire_data.py` using `yfinance` | `data/raw/sp500_raw.csv` |

Raw files are preserved in `data/raw/` and should not be manually edited. Cleaned and integrated files are generated by scripts and can be recreated through the Snakemake workflow.