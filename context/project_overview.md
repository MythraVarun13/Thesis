# Project Overview

_Last updated: 2026-05-31_

## Goal

Analyze the EnFa building energy dataset to determine how it can support a ZORO Energy AI-driven supervisory optimization MVP for commercial buildings.

## ZORO Energy Context

ZORO Energy is building an AI-driven supervisory optimization platform for commercial buildings, focusing on HVAC optimization, predictive control (MPC), energy forecasting, PV/battery management, fault detection, and explainable analytics for facility managers.

## Dataset Purpose

The EnFa dataset is a historical export from the EnFa research building (Germany). It covers multiple energy sub-systems: heat pump, BHKW/CHP, PV, battery, building thermal zones, DHW storage, weather, and electrical grid metering.

## Current Stage

**Step 1 complete: File Inventory**

- 233 CSV files, all valid, no empty files
- Total size: ~40.5 GB (significantly larger than initially estimated 2.5 GB)
- All files use .csv extension
- Signal names are in German, following BMS tag conventions

## Important Constraints

- Raw data folder is read-only; never modify files in `data/`
- Do not load full dataset into memory; use sampling and aggregation scripts
- No separate BMS tag dictionary available; must infer from names and value ranges
- Python environment in sandbox has no internet; packages available: pandas, numpy, matplotlib, charset_normalizer, dateutil

## Current Conclusions

- Dataset is substantially larger than initially estimated (40.5 GB vs 2.5 GB)
- All 233 files are non-empty CSVs with meaningful signal names
- Signal naming prefixes appear systematic: `V_real` = setpoint/parameter, `greal` = calculated/aggregated real, `real` = measured real, `green` = battery cluster, `dint` = counter/integral
- Multiple ZORO-relevant subsystems are clearly present: BHKW, WP (heat pump), PV, battery, DHW, thermal storage, weather (wind/sun), building zones
