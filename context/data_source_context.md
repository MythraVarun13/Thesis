# Data Source Context

_Last updated: 2026-05-31_

## Project Root

`C:\Users\dellg\OneDrive\Documents\ZE`

## Raw Data Folder

`C:\Users\dellg\OneDrive\Documents\ZE\data`

## File Inventory

- **Total files:** 233 CSV files
- **Total size:** ~40.5 GB (43,499,778,587 bytes)
- **Empty files:** 0
- **Non-CSV files:** 0 (plus 2 sub-folders: `external/`, `processed/`, `samples/`)

## Known Export Format

Suspected InfluxDB export format. Observed sample row:

```
Unnamed: 0;_time;_value;_field;_measurement
;2022-12-14T14:40:41Z;241;value;greal_WP2AbtauSek
```

- **Delimiter:** semicolon (`;`)
- **Timestamp column:** `_time` (ISO 8601 UTC, `Z` suffix)
- **Value column:** `_value`
- **Field column:** `_field` (always `value` based on sample)
- **Measurement/signal column:** `_measurement`
- **Index column:** `Unnamed: 0` (empty, artifact of export)

## Suspected Source System

InfluxDB time-series database (BMS or SCADA export). Consistent with typical InfluxDB CSV export format using semicolons.

## Signal Naming Prefixes Observed

| Prefix | Hypothesis | Example |
|---|---|---|
| `V_real` | Setpoint / configuration parameter | `V_real_maxVorlaufTemp` |
| `Vreal` | Setpoint / configuration parameter (alternate) | `Vreal_maxSpeicher` |
| `greal` | Calculated / aggregated real value | `greal_LeistungGebaeude` |
| `real` | Measured real value | `real_BatterieLeistung` |
| `green` | Battery cluster data | `green_bat`, `green_t1` |
| `dint` | Counter / integral / pulse count | `dintVolGasVerbrauchBhkwImp1` |
| `grealCluster` | Battery cluster aggregated | `grealCluster_1_Spannung` |
| `grealIst` | Actual (Ist) calculated value | `grealIstWaermepumpVorlauf` |
| `realIst` | Actual measured value | `realIstTempWarmWasOben` |

## Known Timestamp Format

`2022-12-14T14:40:41Z` — ISO 8601 UTC.

Timezone note: EnFa is a German building, so local time is CET (UTC+1) or CEST (UTC+2). Conversion needed for scheduling analysis but should be documented, not done silently.
