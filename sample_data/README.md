# MASS-ADK Smoke Sample Data

This folder contains tiny synthetic datasets for package smoke tests.

The data is intentionally small and artificial. It exists only so reviewers can run the integrated MASS engine without downloading or accessing the full research dataset.

Available datasets:

```text
ih_smoke/      # default China-style smoke dataset used by --stock_pool ih
sp500_smoke/   # default US-style smoke dataset used by --stock_pool sp500
```

Do not use this data for research conclusions, portfolio decisions, or performance claims.

Regenerate with:

```bash
python scripts/create_smoke_sample_data.py
```

Each dataset uses the same generic macro filenames:

```text
macro_data/policy_rate.csv
macro_data/cpi_yoy.csv
macro_data/equity_index_pe_ttm.csv
macro_data/market_sentiment.csv
macro_data/ten_year_government_bond_yield.csv
```

The generic names are intentional so the same copied MASS engine code can run
China-style and SP500-style smoke cases without country-specific file-name
assumptions.
