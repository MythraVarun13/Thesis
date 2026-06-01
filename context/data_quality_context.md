# Data Quality Context

_Generated: 2026-05-31T08:20:38.144215_

## Time Coverage Summary

- **Earliest start:** `2022-11-29T09:47:22+00:00`
- **Latest end:** `2026-05-27T07:03:18.429000+00:00`
- **BMS signals (pre-2024):** 228 files
- **Weather/forecast signals (2024+):** 5 files

Note: Two distinct time periods observed. BMS data starts ~Dec 2022. Weather/forecast data starts ~Feb 2024. These likely reflect different data collection phases or the weather integration was added later.

## Sampling Interval Groups

| Interval | Count | Notes |
|---|---|---|
| `~20s` | 169 | Standard BMS polling interval |
| `~1hr` | 28 | Hourly aggregates |
| `~5min` | 23 | Typical energy meter interval |
| `~5s` | 7 | Very high frequency — likely battery/power electronics |
| `~63min` | 2 |  |
| `~78min` | 1 |  |
| `~79min` | 1 |  |
| `~15min` | 1 | Standard utility metering |
| `~1min` | 1 | Medium frequency signals |

## Gap Detection (head sample only)

Files with irregular gaps in first 30 rows:

- `TimerRuecklaufAltbau.csv`
- `V_realAZmax.csv`
- `V_realAZmin.csv`
- `V_realHysWP.csv`
- `V_realMaxVL_WP.csv`
- `V_realMinVL_WPcool.csv`
- `V_realSollTempAZmax.csv`
- `V_real_AbtauTemperaturBetrieb.csv`
- `V_real_Nachtabsenkung.csv`
- `V_real_NachtabsenkungY4.csv`
- `V_real_maxAT.csv`
- `V_real_maxATY4.csv`
- `V_real_maxAT_K.csv`
- `V_real_maxVorlaufTemp.csv`
- `V_real_maxVorlaufTempK.csv`
- `V_real_maxVorlaufTempY4.csv`
- `V_real_minAT.csv`
- `V_real_minATY4.csv`
- `V_real_minAT_K.csv`
- `V_real_minVorlaufTemp.csv`
- `V_real_minVorlaufTempK.csv`
- `V_real_minVorlaufTempY4.csv`
- `Vreal_WP_Ein_Batterie.csv`
- `Vreal_WP_Ein_BatterieKritsch.csv`
- `Vreal_WP_Ein_BatterieKritschHys.csv`
- `grealIstWaermepumpVorlauf.csv`
- `greal_AZ_WP_Energie.csv`
- `greal_Administrator_HT.csv`
- `greal_JalousienMaxWind.csv`
- `greal_K_WMZ_E_Altbau.csv`
- `greal_K_WMZ_E_Halle.csv`
- `greal_K_WMZ_E_Nord.csv`
- `greal_K_WMZ_E_Sued.csv`
- `greal_K_WMZ_E_WP.csv`
- `greal_K_WMZ_P_Altbau.csv`
- `greal_K_WMZ_P_Halle.csv`
- `greal_K_WMZ_P_Nord.csv`
- `greal_K_WMZ_P_Sued.csv`
- `greal_K_WMZ_P_WP.csv`
- `greal_K_WMZ_TR_Altbau.csv`
- `greal_K_WMZ_TR_Halle.csv`
- `greal_K_WMZ_TR_Nord.csv`
- `greal_K_WMZ_TR_Sued.csv`
- `greal_K_WMZ_TV_Altbau.csv`
- `greal_K_WMZ_TV_Halle.csv`
- `greal_K_WMZ_TV_Nord.csv`
- `greal_K_WMZ_TV_Sued.csv`
- `greal_Nachtabsenkung.csv`
- `greal_SollTempAZplus.csv`
- `greal_T_Server_EG.csv`
- `greal_VorlaufTempKennlinie.csv`
- `greal_VorlaufTempKennlinie_K.csv`
- `greal_WP1AbtauSek.csv`
- `greal_WP2AbtauSek.csv`
- `greal_WP3AbtauSek.csv`
- `greal_Wochenendwert.csv`
- `green_bat.csv`
- `green_t1.csv`
- `green_t2.csv`
- `green_t3.csv`
- `realIstTempPuffAltbau.csv`
- `realIstTempRuecklPuffAltbau.csv`
- `realSollwertReglerWP1.csv`
- `real_E_VerlustEnFa.csv`
- `real_E_Verlustbhkw1.csv`
- `real_E_Verlustbhkw2.csv`
- `real_VerlustleistungEnFa.csv`
- `real_aktVerlustLeistungBHKW.csv`
- `val1006.csv`
- `val1007.csv`
- `wind_now.csv`

## Tiny/Snapshot Files (≤8 data rows — single-day commissioning snapshots, not time series)

`VrealSpeicherWW_BHKW_Aus/Ein`, `Vreal_maxSpeicher`, `Vreal_maxTempSpeicherUnten`, `Vreal_minSpeicher` — DHW/storage setpoints captured once on 2022-12-14 (7 rows each). Reference values only.

`greal_K_WMZ_E/P/TR/TV_bhkw1/2` and `greal_K_WMZ_TR/TV_WP` — BHKW and heat pump heat meter snapshots from 2022-12-19 (6 rows each). These sensors appear to have been decommissioned or not integrated into the ongoing export. **Not useful for time-series modeling.**

## Data Quality Notes

- All 233 files: UTF-8, semicolon-delimited — no parsing issues
- Timestamps are UTC (ISO 8601 `Z` suffix); convert to CET/CEST for scheduling analysis
- **Data is live/current: runs to 2026-05-27** — this is operational data, not just historical
- `pilot.csv`: CPU monitoring strings — exclude from energy analysis
- `A.csv`, `_value.csv`: ramp/counter test signals — exclude
- `V_real*` "gaps": expected behavior — setpoint files only write when a parameter changes (hourly polling of rarely-changing values). Not missing data.
- Full gap/duplicate scan (exhaustive) is deferred — requires full-file reads, impractical at 40 GB

## Signals Sorted by Start Date (earliest 20)

| File | Start UTC | Duration (days) | Interval |
|---|---|---|---|
| `pilot.csv` | `2022-11-29T09:47:22` | 0.0 | ~20s |
| `A.csv` | `2022-11-30T10:20:49` | 0.0 | ~5s |
| `_value.csv` | `2022-11-30T10:41:18` | 0.0 | ~5s |
| `val1006.csv` | `2022-11-30T10:57:08` | 5.1 | ~5s |
| `val1007.csv` | `2022-11-30T10:57:08` | 0.9 | ~5s |
| `val1008.csv` | `2022-11-30T14:40:03` | 0.7 | ~5s |
| `val1009.csv` | `2022-11-30T14:40:03` | 0.7 | ~5s |
| `grealCluster_1_Ladung.csv` | `2022-12-06T16:04:43` | 1267.6 | ~5s |
| `grealCluster_1_Spannung.csv` | `2022-12-06T16:21:15` | 1267.6 | ~20s |
| `grealCluster_2_Ladung.csv` | `2022-12-06T16:21:15` | 1267.6 | ~20s |
| `grealCluster_2_Spannung.csv` | `2022-12-06T16:21:15` | 1267.6 | ~20s |
| `grealCluster_3_Ladung.csv` | `2022-12-06T16:21:15` | 1267.6 | ~20s |
| `grealCluster_3_Spannung.csv` | `2022-12-06T16:21:15` | 1267.6 | ~20s |
| `grealCluster_4_Ladung.csv` | `2022-12-06T16:21:15` | 1267.6 | ~20s |
| `grealCluster_4_Spannung.csv` | `2022-12-06T16:21:15` | 1267.6 | ~20s |
| `greal_BatterieLadeZustand.csv` | `2022-12-07T08:37:18` | 1266.9 | ~20s |
| `grealTempAussenGefiltert.csv` | `2022-12-07T10:09:55` | 1266.9 | ~20s |
| `greal_LeistungBHKW1.csv` | `2022-12-07T14:11:41` | 1266.7 | ~20s |
| `greal_LeistungBHKW2.csv` | `2022-12-07T14:11:41` | 1266.7 | ~20s |
| `real_BatterieLeistung.csv` | `2022-12-07T14:11:41` | 1266.7 | ~20s |
