# Open Questions

_Last updated: 2026-05-31_

## Data Source

1. ~~What system exported these CSV files?~~ **RESOLVED: InfluxDB** — confirmed from semicolon-delimited format with `_time`, `_value`, `_field`, `_measurement` columns, consistent with InfluxDB line protocol CSV export.
2. ~~Is the `_field` column always `value`?~~ **RESOLVED: Yes** — all sampled files show `_field = value`. Single-field measurements.
3. What is the actual time coverage (start/end dates) across all files?
4. Are all files from the same time range, or do some cover different periods?
5. What is the actual sampling interval for each signal? (Appears 5-min from sample, but needs verification)

## Signal Interpretation

6. Are units documented anywhere in the thesis appendix or BMS documentation?
7. ~~What does `green` prefix mean?~~ **PARTIALLY RESOLVED:** `green_bat` values are small floats (~0.05 to 4.99), irregular intervals (minutes apart) — likely battery cluster current or state variable. `green_t1/t2/t3` have similar irregular timing and ~0–4.8 range. Likely temperature or current per battery cluster. Need thesis confirmation.
8. ~~`val1006`, `val1007`~~ **RESOLVED: Commissioning test signals.** val1006/val1007 are InfluxDB ingestion test signals injected during Nov 2022 commissioning — counter patterns and ternary sequences. Not building data. Exclude permanently.
   ~~`val1008`, `val1009`~~ **RESOLVED: SMA SunnySensorBox irradiance test exports (~65–94 W/m²) during commissioning Nov 2022.** Identical values confirm same sensor exported to two measurement names. Only 0.7 days — not integrated into continuous InfluxDB export. Irradiance is NOT available as a continuous signal.
9. ~~`A.csv`~~ — values ramp 20→25→30→35...→60→... at ~5-second intervals starting 2022-11-30. Likely a test/calibration ramp signal, not a real building measurement. Low priority.
10. ~~`pilot.csv`~~ — **RESOLVED: system monitoring signal.** Values are strings like `"node cpu usage: 3.00%"` — this is a node/server CPU monitoring export, not building energy data. Should be excluded from energy analysis.
11. ~~`_value.csv`~~ — values ramp 29→30→31→32... at 1-second intervals starting 2022-11-30. Appears to 