# Schema Context

_Generated: 2026-05-31T08:17:18.610237_

## Summary

- **Total files:** 233
- **Standard schema:** 233
- **Non-standard schema:** 0

## Encoding

| Encoding | Count |
|---|---|
| `utf-8` | 233 |

## Delimiter

| Delimiter | Count |
|---|---|
| `';'` | 233 |

## Standard Schema Pattern

```
Unnamed: 0 ; _time ; _value ; _field ; _measurement
```

- `Unnamed: 0` — empty index (InfluxDB export artifact)
- `_time` — UTC ISO 8601 timestamp (e.g. `2022-12-07T14:11:41Z`)
- `_value` — float measurement
- `_field` — always `value`
- `_measurement` — BMS signal name

## Non-Standard Files

None — all files follow the standard schema.

## Top 20 Files by Estimated Rows

| File | Est. Rows |
|---|---|
| `green_t2.csv` | 7088428 |
| `green_t1.csv` | 7050161 |
| `green_t3.csv` | 7035099 |
| `green_bat.csv` | 5468138 |
| `realIstTempKaltWasOben.csv` | 5438636 |
| `greal_WMZ_Kalt.csv` | 5240582 |
| `real_E_VerlustEnFa.csv` | 5193092 |
| `greal_K_WMZ_P_GF.csv` | 5164329 |
| `greal_K_WMZ_P_Server.csv` | 5080336 |
| `greal_K_WMZ_TR_Altbau.csv` | 5047251 |
| `greal_K_WMZ_TV_Altbau.csv` | 5047226 |
| `greal_LeistungGebaeude.csv` | 4913970 |
| `greal_K_WMZ_P_Altbau.csv` | 4899152 |
| `greal_K_WMZ_TR_Sued.csv` | 4888012 |
| `greal_K_WMZ_TV_Sued.csv` | 4887812 |
| `greal_K_WMZ_P_Bespr.csv` | 4866051 |
| `real_VerlustleistungEnFa.csv` | 4852143 |
| `realIstTempWarmWasUnt.csv` | 4793659 |
| `greal_W_WMZ_TV_bhkw1.csv` | 4766120 |
| `greal_W_WMZ_TR_bhkw1.csv` | 4765681 |
