# Decisions Log

| Date | Decision | Reason | Impact |
|---|---|---|---|
| 2026-05-31 | Use semicolon as delimiter for all CSV files | Observed sample header `Unnamed: 0;_time;_value;_field;_measurement` confirms semicolon separation | Prevents Excel-style single-column misread |
| 2026-05-31 | Treat `_time` as UTC (timezone Z suffix) | Timestamp format is ISO 8601 with `Z` = UTC | Must convert to CET/CEST for German local-time analysis; document conversion, never do silently |
| 2026-05-31 | Use system Python (3.10) with available packages; no venv pip install | Sandbox has no internet access; pandas, numpy, matplotlib, charset_normalizer, dateutil are available | Scripts must use only these packages; note polars/duckdb/tqdm unavailable in sandbox |
| 2026-05-31 | Never modify files in `data/` | CLAUDE.md constraint; raw data is read-only | All outputs go to reports/, context/, data/processed/, data/samples/ |
| 2026-05-31 | Do not load full 40.5 GB dataset into memory | Dataset is significantly larger than estimated; loading would be infeasible | Use chunked reading and sampling strategies in all scripts |
