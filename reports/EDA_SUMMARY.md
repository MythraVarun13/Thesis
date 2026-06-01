# EnFa Data Analysis Summary for ZORO Energy

_Generated: 2026-05-31 | Analyst: ZORO AI Data Scientist_

---

## 1. Executive Summary

The EnFa dataset is a **high-quality, 3.5-year operational time series** from a multi-source German commercial building energy system. It contains 233 signals at ~20-second resolution covering heat pumps, BHKW/CHP, PV (7 strings), battery storage (4 clusters), DHW, underfloor heating, EV charging, and weather.

**223 of 233 signals map directly to the ZORO JSON v1 pipeline format** (`device_id`, `metric`, `unit`). Three ZORO MVP paths are immediately actionable: Energy Analytics Dashboard, HVAC Optimization Advisory, and Heat Pump FDD. The dataset is live — data runs to **2026-05-27**, making it current operational data, not just historical.

**Recommended first MVP:** Heat Pump Performance & Fault Detection (Path C). It has the richest signal coverage, the longest time history, and the clearest value proposition for facility managers.

---

## 2. Dataset Overview

| Property | Value |
|---|---|
| Total files | 233 CSV |
| Total size | ~40.5 GB |
| Format | InfluxDB semicolon-delimited CSV |
| Encoding | UTF-8 (all files) |
| Columns | `Unnamed:0 ; _time ; _value ; _field ; _measurement` |
| Timestamp format | ISO 8601 UTC (`2022-12-07T14:11:41Z`) |
| Signal name location | `_measurement` column |
| Dominant sampling interval | ~20 seconds (169 files) |
| Date range (BMS) | 2022-12-07 → 2026-05-27 (~3.5 years) |
| Date range (weather) | 2024-02-27 → 2026-05-27 (~2.2 years) |
| Data status | **Live / operational** |

---

## 3. File Inventory

All 233 files are valid CSVs with zero empty files and zero non-CSV files. File sizes range from ~7 KB (commissioning snapshots) to ~338 MB (high-frequency signals).

**15 files are commissioning-only snapshots** (6–8 rows, single day Dec 2022): DHW storage setpoints and BHKW/WP heat meter snapshots captured during initial setup. These are not time series and should be excluded from modeling.

**3 files are non-energy artifacts:** `pilot.csv` (CPU monitoring strings), `A.csv` and `_value.csv` (ramp test counters). Excluded from all analysis.

---

## 4. CSV Format and Parsing Notes

The format is consistent InfluxDB CSV export:

- Delimiter: **semicolon** — not comma. Excel will misread as single-column without explicit delimiter setting.
- `Unnamed: 0` column is always empty (InfluxDB export artifact — ignore).
- `_field` column is always `value` — single-field measurements throughout.
- Timestamps are UTC. Germany is CET (UTC+1) / CEST (UTC+2). Convert for scheduling/occupancy analysis but document conversion explicitly.
- All files: UTF-8 encoding, no BOM issues.

---

## 5. Schema Summary

100% of files follow a single standard schema. No schema variants detected across 233 files. This is exceptional consistency for a BMS/SCADA export.

Signal naming conventions:

| Prefix | Meaning | Example |
|---|---|---|
| `V_real` / `Vreal` | Setpoint / configuration parameter | `V_real_maxVorlaufTemp` |
| `greal` | Calculated / aggregated value | `greal_LeistungGebaeude` |
| `real` | Measured raw value | `real_BatterieLeistung` |
| `green` | Battery cluster raw data | `green_bat`, `green_t1` |
| `dint` | Counter / pulse integral | `dintVolGasVerbrauchBhkwImp1` |
| `grealCluster` | Battery cluster aggregated | `grealCluster_1_Spannung` |

---

## 6. Time Coverage and Sampling

**Two distinct data populations:**

BMS operational signals (228 files) run from Dec 2022 to May 2026 — median duration 1254 days. Weather and forecast signals (5 files: `wind_now`, `wind_tomorrow`, `sun_alt`, `sun_azi`, `realLeistungGebSystem`) start Feb 2024, covering 820 days.

**Sampling interval breakdown:**

| Interval | Files | Key signals |
|---|---|---|
| ~20s | 169 | All core BMS: temperatures, power, battery, energy meters |
| ~1hr | 28 | `V_real*` setpoints (sparse by design — only write on change) |
| ~5min | 23 | Key HVAC aggregates: HP flow temp, thermal power, schedules |
| ~5s | 7 | Battery cluster charge (`grealCluster_1_Ladung`) + artifacts |
| Irregular | 4 | `green_bat/t1/t2/t3` — battery cluster raw data, minutes apart |

The 71 files showing "gaps" in head sampling are almost entirely `V_real*` setpoint files — this is expected behaviour, not missing data. Setpoints only write to the database when their value changes.

---

## 7. Data Quality Findings

**Strengths:**
- Consistent format, encoding, and delimiter across all 233 files
- Zero empty files
- 3.5 years of continuous operation — no evidence of extended outages in head/tail checks
- Battery, heat pump, and energy meter signals all show clean numeric values in expected physical ranges

**Known gaps and limitations:**
- **No direct solar irradiance signal confirmed.** `sun_alt` and `sun_azi` give geometry only. `val1008/val1009` (values ~65–92, 5s interval) are candidates — requires thesis confirmation.
- **15 commissioning snapshot files** with 6–8 rows only — not useful for modeling.
- **No electricity spot price signal.** `greal_Administrator_HT` provides binary HT flag only.
- **No confirmed indoor zone temperature sensors** beyond server room and BKT ground floor.
- **`val1006/val1007`** — ternary state (-1/0/1) at 5s intervals — meaning unknown without thesis or BMS tag list.
- Full gap and duplicate analysis (requiring complete file scans) deferred — impractical at 40.5 GB with current tooling. Recommend running on a sampled subset or with DuckDB.

---

## 8. Signal Classification

| Category | Count |
|---|---|
| Thermal energy (WMZ) | 26 |
| Thermal power (WMZ) | 20 |
| Heating return temperature | 17 |
| Heating supply temperature | 17 |
| PV energy (per string + total) | 8 |
| DHW temperature | 8 |
| HVAC setpoints | 8 |
| Heating curve parameters | 8 |
| CHP/BHKW gas | 8 |
| HP setpoints | 7 |
| Battery (SOC/power/energy) | ~15 |
| Phase current RMS | 6 |
| Building power/energy | 10 |
| Outdoor/weather | 6 |
| EV charging | 6 |
| Excluded (artifacts) | 3 |
| Unknown | 5 |
| **Pipeline-ready (JSON v1)** | **223** |

---

## 9. Physical System Interpretation

The EnFa building operates a **multi-source energy system** with active energy management:

**Heat generation:** 3 air-source heat pumps (WP1/2/3) + 2 BHKW/CHP units (bhkw1/bhkw2). Both heat sources serve DHW storage and building zones. BHKW also exports electricity.

**Electricity:** 7-string PV system + BHKW electrical output + grid import/export. 4-cluster battery storage mediates between generation and load. 3 EV charging stations add flexible load.

**Distribution:** Underfloor heating (FBH) in 3 zones (Nord, Sued, Halle) + concrete core activation (BKT) in ground floor + old building buffer tank.

**Controls:** Heating curve (supply temp vs outdoor temp), night setback, weekend mode, battery-HP interlock, high-tariff demand shifting. This is a complete multi-source EMS — an ideal reference architecture for ZORO's supervisory layer.

---

## 10. Thesis Context Connection

The German thesis PDF (Guillet, 2016) is the primary domain reference for signal interpretation. Key connections:

- Signal naming (`WP`, `BHKW`, `WMZ`, `FBH`, `BKT`, `AT`, `VL`, `RL`) follows standard German HVAC/BMS conventions described in the thesis.
- The EnFa system (Energieeffizienzfabrik or similar) described in the thesis matches the multi-source topology observed in the data.
- Thesis appendix likely contains the BMS tag dictionary needed to resolve the 5 remaining unknown signals and confirm `val1008/val1009` as irradiance.
- Thesis modeling equations for HP COP and heating curve are directly applicable to the available signals.

_Full thesis parsing deferred to a dedicated session._

---

## 11. ZORO MVP Use-Case Readiness

| MVP Path | Readiness | Recommended First |
|---|---|---|
| A: Energy Analytics Dashboard | **Ready** | Yes |
| B: HVAC Optimization Advisory | **Ready** | Yes |
| C: Heat Pump FDD | **Ready** | **Yes — top recommendation** |
| D: EnergyPlus Calibration | Partially Ready | No (missing zone temps, irradiance) |
| E: MPC / Forecasting | Partially Ready | No (missing spot price signal) |
| Battery Optimization | **Ready** | Secondary |
| EV Charging Optimization | **Ready** | Secondary |
| PV Forecasting | Partially Ready | No (missing irradiance confirmation) |
| FDD (general) | **Ready** | Secondary |

---

## 12. Recommended First MVP Path

**Path C: Heat Pump Performance Monitoring & Fault Detection**

**Why:**

The heat pump dataset is the most complete in the entire collection. Three HP units are individually tracked with defrost duration at 20-second resolution — a level of granularity that most BMS platforms never expose. COP can be estimated immediately from `greal_WMZ_Hz_Erz_WP` (heat output) divided by `greal_E_WP` (electrical input). Three and a half years of defrost cycle history enables statistical baselines for anomaly detection.

This is also the highest-value use case for facility managers: heat pump degradation is expensive, slow-moving, and almost never caught until a breakdown. An alert that says "WP2 defrost duration has increased 40% over the past 3 months" is immediately actionable and has clear ROI.

**Concrete first deliverables:**
1. HP COP time series (daily/weekly rolling) — computed from existing signals, no new sensors needed
2. Defrost cycle counter and duration trend per unit (WP1/WP2/WP3)
3. Supply temperature deviation from heating curve — early indicator of performance loss
4. Anomaly flags when defrost duration or COP exceeds statistical thresholds

**Ingestion path to ZORO pipeline:** All required signals are JSON v1-ready. `device_id` pattern: `de-enfa-main-01/heat-pump` (or per-unit suffix). No parser changes needed.

---

## 13. Modeling Opportunities

**Immediately feasible (no additional data):**
- HP COP estimation — ratio of thermal to electrical energy
- Defrost cycle detection and duration trending — threshold on `greal_WP*AbtauSek`
- Heating curve deviation scoring — compare actual supply temp vs computed curve
- Battery charge/discharge efficiency — ratio of charge to discharge energy
- BHKW electrical efficiency — electrical output vs gas input
- Energy balance per source (PV + BHKW vs building load + battery)

**Feasible with minor additions:**
- Load forecasting — outdoor temp available for 3.5 years; need occupancy schedule
- PV generation forecasting — sun geometry available; add irradiance or use clearsky model
- Night setback optimisation — setpoint + supply temp + outdoor temp all available

**Requires additional data:**
- Room-level thermal comfort model — no room temperature sensors confirmed
- Price-optimal battery/HP dispatch — needs electricity spot price feed
- EnergyPlus calibration — needs building geometry + confirmed irradiance

---

## 14. Missing Data and Risks

| Gap | Impact | Mitigation |
|---|---|---|
| No solar irradiance (W/m²) | PV model less accurate | Use clearsky model from sun geometry; confirm val1008/val1009 from thesis |
| No room temperature sensors | Cannot model thermal comfort | Check thesis for additional sensors; use supply/return delta as proxy |
| No electricity spot price | MPC limited to rule-based | Add Tibber or ENTSO-E feed to ZORO pipeline |
| 15 snapshot-only files | Cannot use for modeling | Already excluded from pipeline mapping |
| val1006/val1007 unknown | Potential control signals missed | Parse thesis appendix |
| Weather data starts Feb 2024 | 14-month gap for weather-ML | Use outdoor temp from grealTempAussenGefiltert (full 3.5 years) as proxy |
| Full gap/duplicate scan not done | Unknown data holes in mid-series | Run DuckDB-based full scan on sampled signals before modeling |

---

## 15. Recommended Next Steps

**Immediate (this week):**
1. Parse thesis PDF appendix — resolve val1006/val1007/val1008/val1009 and confirm irradiance
2. Write `06_generate_samples.py` — extract clean 30-day samples for the top 20 signals into `data/samples/` for rapid prototyping
3. Build HP COP calculator — daily COP from `greal_WMZ_Hz_Erz_WP` / `greal_E_WP`

**Short term (2–4 weeks):**
4. Build ZORO pipeline replay script — convert EnFa CSV to JSON v1 and replay into TimescaleDB for end-to-end pipeline validation with real building data
5. Defrost cycle detector — rule-based anomaly flag on `greal_WP*AbtauSek`
6. Build EnFa Grafana dashboard as reference template for SCS onboarding

**Medium term:**
7. Electricity spot price integration — Tibber API or ENTSO-E as new pipeline data source
8. Signal registry table in TimescaleDB — formalise EnFa signal dictionary as reusable schema
9. Format adapter plugin refactor — support multiple customer parser formats without redeployment

---

## 16. Appendix: Important Signal Dictionary

See `context/signal_dictionary.md` for full 233-signal table.
See `reports/zoro_pipeline_mapping.csv` for 223 signals with JSON v1 `device_id`, `metric`, `unit` fields.
See `reports/zoro_mvp_readiness_matrix.csv` for per-use-case readiness scoring.

**Top 20 signals for ZORO MVP (Heat Pump FDD path):**

| Signal | English Meaning | Unit | Interval |
|---|---|---|---|
| `greal_BatterieLadeZustand` | Battery SOC | % | ~20s |
| `real_BatterieLeistung` | Battery net power | kW | ~20s |
| `grealIstWaermepumpVorlauf` | Heat pump supply temperature | °C | ~5min |
| `greal_WP1AbtauSek` | HP unit 1 defrost duration | s | ~20s |
| `greal_WP2AbtauSek` | HP unit 2 defrost duration | s | ~20s |
| `greal_WP3AbtauSek` | HP unit 3 defrost duration | s | ~20s |
| `greal_E_WP` | Heat pump electrical energy | kWh | ~20s |
| `greal_WMZ_Hz_Erz_WP` | Heat pump heat generation energy | kWh | ~20s |
| `greal_W_WMZ_TV_WP` | HP circuit supply temperature | °C | ~20s |
| `greal_W_WMZ_TR_WP` | HP circuit return temperature | °C | ~20s |
| `greal_W_WMZ_P_WP` | HP circuit thermal power | kW | ~20s |
| `grealTempAussenGefiltert` | Outdoor temperature | °C | ~20s |
| `greal_VorlaufTempKennlinie` | Heating curve supply temp | °C | ~5min |
| `real_PV_Gesamt` | PV total power | kW | ~20s |
| `greal_LeistungGebaeude` | Building electrical demand | kW | ~20s |
| `real_P_BHKW` | BHKW electrical power | kW | ~20s |
| `greal_Gas_bhkwges` | BHKW total gas consumption | m³ | ~20s |
| `realSollwertReglerWP1` | HP controller setpoint | °C | ~20s |
| `greal_Nachtabsenkung` | Night setback active | — | ~1hr |
| `greal_Administrator_HT` | High-tariff state | — | ~1hr |
