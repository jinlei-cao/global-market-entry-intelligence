# Data directory

`data/raw` and `data/processed` are intentionally excluded from Git (except `.gitkeep`).

- Use `marketintel demo` to generate **synthetic** `data/processed/synthetic_demo.csv` and matching `.manifest.json`.
- Use `marketintel fetch` to download **observed World Bank** records and corresponding data manifest.
- Source data may have gaps, revised values and different observation years. Check `reports/latest/source_observations.csv` and `data_completeness.csv`.
- Do not claim the demo's fictional numbers are World Bank statistics.

World Bank sources and attribution: see `docs/DATA_DICTIONARY.md`.
