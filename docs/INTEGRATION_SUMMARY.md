# Integration Summary

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

- Overlapping start date: 1954-07-01
- Overlapping end date: 2026-03-20

## Row counts

- Original FRED rows: 26198
- Original S&P 500 rows: 24671
- FRED rows in overlapping period: 26196
- S&P 500 rows in overlapping period: 18051
- Integrated rows: 18051

## Completeness note

Because the final integrated dataset uses trading days as the observation unit, non-trading-day Federal Funds Rate observations are excluded from the final table.

Rows with missing federal funds rate after integration: 0

## Output

- `data/processed/integrated_fred_sp500.csv`
