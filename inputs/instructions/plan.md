# EnFa Data Science Plan — ZORO Energy
_Last updated: 2026-06-01_

---

## Primary Goal

Build a **Model Predictive Control (MPC)** system for the EnFa building energy system.

MPC is the end goal. Everything else — EDA, system characterization, individual subsystem models — is a stepping stone toward it. We do full, deep analysis of all 233 signals across all subsystems, not just heat pumps.

**Sequential path:**
```
Full EDA of all systems (all 233 signals)
  → Individual system models (HP, Battery, PV, BHKW, Building thermal)
    → State-space model assembly (states, controls, disturbances, constraints)
      → MPC prototype
        → ZORO pipeline integration
```

---

## What MPC Requires from the Data

| MPC Component | Definition | EnFa Signals Available |
|---|---|---|
| **States** | What the system currently is | Battery SOC, thermal storage temp, HP supply/return temp, outdoor temp |
| **Controls / Actuators** | What we can command | `V_real*` setpoints, HP on/off, battery charge/discharge, BHKW dispatch |
| **Disturbances** | What we cannot control but can forecast | Weather (`wind_tomorrow`, `sun_alt/azi`), PV generation, occupancy |
| **Constraints** | Hard limits | SOC min/max, temp comfort bounds, equipment capacity setpoints |
| **Objective function** | What we minimise | Energy cost (needs spot price) or carbon. Currently only binary HT flag available — spot price feed needed |

**Known gaps for MPC:**
- No confirmed indoor zone temperature sensors (needed as comfort state)
- No electricity spot price signal (needed for cost objective)
- Occupancy schedule not in dataset (needed as disturbance)

These gaps do not block EDA or system characterization — they are tracked as open requirements.

---

## Architecture

| Layer | Tool | Why |
|---|---|---|
| Raw data queries | **DuckDB** | Reads 40 GB CSV directly without loading into memory. 30x faster than pandas for aggregations at this scale |
| Processed storage | **Parquet** (via pyarrow) | Compressed columnar format. All 233 signals at hourly resolution ≈ 200 MB. Loads instantly |
| Data manipulation | **Pandas / Polars** | Pandas for processed data (fits in memory). Polars if raw file manipulation needed |
| Forecasting | **Prophet** | Handles daily, weekly, annual seasonality in load and generation automatically |
| ML / time-series | **sktime / Darts** | For MPC disturbance forecasting (PV, load). Install when MPC phase begins |
| Visualization | **Matplotlib / Seaborn** | Static plots for EDA reports |
| MVP dashboard | **Streamlit** | Interactive stakeholder demo after analysis is complete |
| ZORO pipeline | **TimescaleDB + Kafka** | Production ingestion (ZoroEnergyPlatform repo — separate work stream) |

---

## Critical Data Handling Rules

### 1. Energy signal aggregation — IMPORTANT

`greal_E_WP`, `greal_WMZ_Hz_Erz_WP`, `greal_E_BatterieLaden`, `greal_E_BatterieAbgabe`, and all other `greal_E_*` signals are **cumulative counters** — ever-increasing totals, not energy-per-20-seconds.

**Wrong:** `SUM(_value)` → produces nonsense (sum of running totals)

**Correct:** `MAX(_value) - MIN(_value)` per hour = energy consumed in that hour

```sql
-- Correct aggregation for cumulative energy counters
SELECT
    time_bucket(INTERVAL '1 hour', _time::TIMESTAMP) AS hour,
    MAX(_value) - MIN(_value) AS energy_kwh
FROM read_csv('data/greal_E_WP.csv', delim=';', header=true)
GROUP BY 1 ORDER BY 1
```

### 2. Aggregation rules by signal type

| Signal Type | Aggregation | Examples |
|---|---|---|
| Power (kW) | `MEAN` | `real_BatterieLeistung`, `greal_LeistungGebaeude`, `real_PV_Gesamt` |
| Cumulative energy (kWh) | `MAX - MIN` | `greal_E_WP`, `greal_WMZ_Hz_Erz_WP`, `greal_E_BatterieLaden` |
| Temperature (°C) | `MEAN` | All `Temp*`, `Vorlauf*`, `Ruecklauf*`, `grealTempAussen*` |
| SOC (%) | `MEAN` | `greal_BatterieLadeZustand` |
| Defrost duration (s) | `SUM` | `greal_WP1AbtauSek`, `greal_WP2AbtauSek`, `greal_WP3AbtauSek` |
| Setpoints | `LAST` + forward-fill | All `V_real*` — event-driven, only writes on change |
| Binary states (0/1) | `MAX` or `LAST` | `greal_Nachtabsenkung`, `greal_Administrator_HT` |
| Counters / pulse integral | `MAX - MIN` | `dint*` gas and volume counters |

### 3. Excluded files

Skip these files in all scripts — do not resample or profile:

**Artifact files (3):** `A.csv`, `pilot.csv`, `_value.csv`

**Commissioning snapshots (15):** DHW storage setpoints and BHKW/WP heat meter snapshots with 6–8 rows from Dec 2022 only. These are single-day setup records, not time series. Identify by: row count < 20 AND date range < 2 days.

### 4. Timezone conversion

All timestamps are **UTC**. Germany is **CET (UTC+1) / CEST (UTC+2)**.

Convert to `Europe/Berlin` **before** plotting:
- Daily load profiles
- Occupancy patterns
- Night setback analysis
- Heating curve deviation (time-of-day matters)

Document the conversion explicitly. Do not convert silently.

### 5. Setpoint forward-fill

After resampling `V_real*` setpoints to hourly, most hours will be `NaN` (no write occurred). Apply `ffill()` to propagate the last known setpoint value forward before any analysis.

---

## Implementation Phases

---

### Phase 1 — Full EDA of All Systems

**Goal:** Deep understanding of all 233 signals across all subsystems. No system left as "TBD."

#### Script 06 — Signal Quality Profiles
`scripts/06_signal_profiles.py`

For every non-excluded signal, compute via DuckDB over the full raw data:

- Min, max, mean, std, 5th/25th/50th/75th/95th percentiles
- Total row count vs expected row count (gap ratio)
- Null / NaN count
- Zero-value percentage (important for PV: how many hours producing zero?)
- Outlier count (values beyond 3σ)
- Longest continuous gap (minutes)
- Signal classification tag (from `reports/signal_classification.csv`)

Output: `reports/signal_quality_profiles.csv`

Runtime estimate: 1–2 hours on 40 GB.

#### Script 07 — Resample All Signals to Hourly Parquet
`scripts/07_resample_hourly.py`

Use DuckDB to resample all 230 valid signals (excluding 3 artifacts + 15 snapshots) from ~20s to hourly. Save as a single wide-format Parquet file.

```
data/processed/hourly.parquet
  → one row per UTC hour
  → one column per signal
  → ~30,000 rows × 230 columns
  → ~200 MB compressed
```

Apply aggregation rules from the table above per signal type.
Apply `ffill()` to all `V_real*` setpoint columns after resampling.

Runtime estimate: 30–60 minutes. Run once, then all subsequent analysis is instant.

#### Script 08 — Generate 30-day Samples
`scripts/08_generate_samples.py`

Extract clean 30-day samples for the top 30 signals into `data/samples/` for rapid prototyping and validation. Use January 2024 (representative winter) and July 2024 (representative summer).

#### Notebook 05 — Full EDA (All Systems)
`notebooks/05_full_eda.ipynb`

Load `hourly.parquet`. Build analysis for every subsystem:

**5.1 — Energy Overview (whole building)**
- Full 3.5-year 4-panel time series: outdoor temp, building power, PV total, battery SOC
- Monthly energy balance stacked bar: PV + BHKW vs building demand + battery charging
- Energy self-sufficiency ratio by month: `(PV + BHKW) / building demand`
- Annual self-sufficiency trend

**5.2 — Heat Pump System (WP1, WP2, WP3)**
- HP COP time series (daily): `greal_WMZ_Hz_Erz_WP` / `greal_E_WP` — energy delta per day
- HP COP vs outdoor temperature scatter (coloured by season)
- COP degradation trend over 3.5 years (monthly rolling)
- Defrost duration per unit (WP1/WP2/WP3) — weekly sum, 3-panel comparison
- Defrost duration vs outdoor temperature scatter per unit
- WP1 vs WP2 vs WP3 defrost ratio — asymmetric degradation flag
- Heating curve: actual supply temp vs computed curve temp vs outdoor temp
- Supply temp deviation from curve (residual over time)
- HP setpoints history: `V_realMaxVL_WP`, `V_realHysWP`, defrost trigger temp

**5.3 — Battery System (4 clusters)**
- Battery SOC histogram (full 3.5 years)
- Battery daily cycling depth by month (box plot)
- Round-trip efficiency: `greal_E_BatterieAbgabe` / `greal_E_BatterieLaden` (monthly)
- Cluster voltage divergence: `grealCluster_1/2/3/4_Spannung` multi-line time series
- Cell balance degradation flag (cluster voltage spread over time)
- Battery power vs SOC scatter (charging/discharging pattern)
- HP-battery interlock: `Vreal_WP_Ein_Batterie` threshold vs actual battery SOC

**5.4 — PV System (7 strings + total)**
- PV total generation by month (bar chart)
- PV actual vs clearsky theoretical (overlay) — use `sun_alt` + `sun_azi` for geometry
- PV performance ratio by month
- String-level comparison (if per-string signals available)
- Zero-generation hours analysis (nighttime vs cloud cover)

**5.5 — BHKW / CHP System (bhkw1, bhkw2)**
- BHKW electrical output time series
- BHKW gas consumption time series
- BHKW electrical efficiency: `real_P_BHKW` / `greal_Gas_bhkwges` (monthly)
- BHKW operation hours (daily count)
- BHKW vs HP coordination pattern

**5.6 — Building Thermal Distribution**
- Underfloor heating zones (Nord, Sued, Halle): supply/return temps
- Concrete core activation (BKT) supply/return temps
- Old building buffer tank (Altbau) temperatures
- DHW storage temperatures and setpoints
- Zone thermal response to HP supply temp changes

**5.7 — Controls and Setpoints**
- Night setback activation pattern (`greal_Nachtabsenkung`) by hour-of-day heatmap
- High-tariff flag pattern (`greal_Administrator_HT`) — demand shifting behaviour
- HP controller setpoint changes over time
- Heating curve parameter history

**5.8 — EV Charging**
- EV charging power time series (all 3 stations)
- Charging event frequency by hour-of-day
- EV load as % of building demand

**5.9 — Weather and Forecasts**
- Outdoor temperature: full 3.5-year series
- Wind speed time series (where available)
- `sun_alt` / `sun_azi` seasonal pattern
- `wind_tomorrow` forecast accuracy vs `wind_now` actuals
- Weather data availability timeline (BMS data starts Dec 2022, weather signals start Feb 2024)

**5.10 — Correlations and Cross-System Dependencies**
- Correlation heatmap: top 30 signals
- Outdoor temp vs HP supply temp scatter (heating curve validation)
- Battery SOC vs PV generation scatter (solar charging behaviour)
- Building demand vs outdoor temp scatter (thermal sensitivity)
- BHKW dispatch vs battery SOC (control logic inference)

**5.11 — Seasonal Load Profiles**
- Average daily profile by season: summer vs winter (energy, HP, PV, battery)
- Weekday vs weekend comparison
- Prophet seasonal decomposition: building demand (trend + weekly + annual)
- Prophet seasonal decomposition: HP electrical consumption

---

### Phase 2 — System Characterisation (Individual Models)

**Goal:** Build a mathematical model of each subsystem that can be used as a component in the MPC system.

#### Notebook 06 — Anomaly Detection and FDD
`notebooks/06_anomaly_detection.ipynb`

Statistical process control foundation for ZORO FDD product:

- 3σ control charts on HP COP (per unit)
- 3σ control charts on defrost duration (per unit)
- Battery cluster voltage divergence flag
- Heating curve deviation scoring (daily residual)
- BHKW efficiency drift alert

#### Notebook 07 — Heat Pump Model
`notebooks/07_hp_model.ipynb`

- COP as function of: outdoor temp, supply temp setpoint, defrost state
- Heating curve model: `supply_temp = f(outdoor_temp, curve_params)`
- Thermal power model: `P_thermal = f(outdoor_temp, flow_rate, delta_T)`
- Defrost cycle model: frequency and duration as function of outdoor temp + humidity proxy

#### Notebook 08 — Battery Model
`notebooks/08_battery_model.ipynb`

- SOC dynamics: `SOC(t+1) = SOC(t) + charge_efficiency * P_charge - P_discharge / discharge_efficiency`
- Round-trip efficiency estimation from data
- Cluster voltage balance model
- Degradation trend from 3.5-year efficiency curve

#### Notebook 09 — PV Model
`notebooks/09_pv_model.ipynb`

- PV generation as function of: sun geometry, clearsky irradiance estimate
- Performance ratio calculation
- Simple forecasting model using Prophet (sun geometry as regressor)
- Confirm whether `val1008/val1009` are irradiance — compare value ranges vs sun geometry

#### Notebook 10 — BHKW Model
`notebooks/10_bhkw_model.ipynb`

- Electrical efficiency model
- Gas consumption model
- On/off dispatch pattern inference

#### Notebook 11 — Building Thermal Model
`notebooks/11_building_thermal_model.ipynb`

- Thermal demand as function of: outdoor temp, occupancy proxy, solar gains
- Heating curve validation
- Thermal time constant estimation (how fast does the building respond to supply temp changes)
- **Note:** Limited by absence of confirmed indoor zone temperature sensors

---

### Phase 3 — MPC Development

**Goal:** Assemble individual system models into a state-space formulation and implement MPC.

#### State-Space Formulation

**States (x):**
- Battery SOC
- Thermal storage temperature (buffer tank)
- HP supply temperature
- Outdoor temperature (measured disturbance)
- Building thermal state (proxy — if zone temps unavailable, use supply/return delta)

**Controls (u):**
- HP power command (on/off or modulated)
- Battery charge/discharge power
- BHKW dispatch (on/off)
- Night setback activation
- HP supply temp setpoint

**Disturbances (d — forecasted):**
- Weather (outdoor temp, solar)
- PV generation (from PV model + forecast)
- Building load (from Prophet forecast)
- Electricity price (requires Tibber/ENTSO-E feed — open gap)

**Constraints:**
- Battery SOC: 10% ≤ SOC ≤ 95%
- Supply temp: `V_real_minVorlaufTemp` ≤ T_supply ≤ `V_real_maxVorlaufTemp`
- Outdoor temp limit for HP: `V_real_minAT` ≤ T_outdoor ≤ `V_real_maxAT`
- HP hysteresis: `V_realHysWP`
- Comfort: indoor temp within comfort band (requires zone sensors or proxy)

**Objective function:**
- Minimise: electricity cost (spot price × grid import) + gas cost (BHKW) - export revenue
- Fallback (until spot price available): minimise grid import during HT flag active hours

#### Notebook 12 — MPC Prototype
`notebooks/12_mpc_prototype.ipynb`

- Linear MPC using `cvxpy` or `scipy.optimize`
- Prediction horizon: 24 hours
- Control step: 1 hour (hourly.parquet resolution)
- Backtesting on 2024 data (use 2022–2023 as training)
- Compare: MPC vs actual historical dispatch (counterfactual)
- KPIs: energy cost reduction %, self-sufficiency improvement %, comfort violations

---

### Phase 4 — ZORO Pipeline Integration

**Goal:** Connect EnFa analysis to the ZORO production platform.

1. Replay EnFa CSV → JSON v1 → Kafka → TimescaleDB (end-to-end validation)
2. Signal registry table in TimescaleDB (formalise signal dictionary as DB schema)
3. Build reference Grafana dashboard (HP FDD + battery + energy balance panels)
4. Build Streamlit MVP demo (HP COP trend + defrost alerts + energy self-sufficiency)
5. Parser plugin registry refactor in `format_adapter.py`
6. Add electricity spot price feed: Tibber API or ENTSO-E (closes MPC objective gap)

---

## Script and Notebook Numbering

| # | File | Status | Purpose |
|---|---|---|---|
| 01 | `scripts/01_scan_files.py` | Done | File inventory |
| 02 | `scripts/02_detect_schema.py` | Done | CSV dialect detection |
| 03 | `scripts/03_profile_timeseries.py` | Done | Time-series profiling |
| 05 | `scripts/05_classify_signals.py` | Done | Signal classification |
| 06 | `scripts/06_signal_profiles.py` | **Next** | DuckDB full-data quality stats |
| 07 | `scripts/07_resample_hourly.py` | Pending | Resample 40GB → hourly.parquet |
| 08 | `scripts/08_generate_samples.py` | Pending | 30-day samples for top 30 signals |
| 01 | `notebooks/01_file_inventory.ipynb` | Done | — |
| 02 | `notebooks/02_schema_detection.ipynb` | Done | — |
| 03 | `notebooks/03_timeseries_profiling.ipynb` | Done | — |
| 04 | `notebooks/04_signal_classification.ipynb` | Done | — |
| 05 | `notebooks/05_full_eda.ipynb` | **Next** | Full EDA all systems |
| 06 | `notebooks/06_anomaly_detection.ipynb` | Pending | FDD / statistical process control |
| 07 | `notebooks/07_hp_model.ipynb` | Pending | Heat pump system model |
| 08 | `notebooks/08_battery_model.ipynb` | Pending | Battery system model |
| 09 | `notebooks/09_pv_model.ipynb` | Pending | PV generation model |
| 10 | `notebooks/10_bhkw_model.ipynb` | Pending | BHKW / CHP model |
| 11 | `notebooks/11_building_thermal_model.ipynb` | Pending | Building thermal model |
| 12 | `notebooks/12_mpc_prototype.ipynb` | Pending | MPC prototype |

---

## Python Packages — Installation Order

**Already installed (from requirements.txt):**
pandas, polars, duckdb, numpy, matplotlib, pyarrow, tqdm, charset-normalizer, python-dateutil, openpyxl

**Install now (Phase 1–2):**
```
pip install seaborn statsmodels prophet
```

**Install when Phase 3 begins (MPC):**
```
pip install cvxpy scikit-learn
```

**Install when Phase 2 forecasting begins:**
```
pip install sktime darts
```

**Install when Phase 4 begins (MVP demo):**
```
pip install streamlit plotly
```

---

## Open Gaps (Track These)

| Gap | Impact | Resolution Path |
|---|---|---|
| No indoor zone temperature sensors | Limits comfort state for MPC | Use supply/return delta as proxy; check thesis appendix |
| No electricity spot price signal | Limits MPC objective function | Add Tibber API or ENTSO-E feed to ZORO pipeline |
| `val1006`, `val1007` — unknown meaning | Potential control signals missed | Parse thesis PDF appendix |
| `val1008`, `val1009` — possible irradiance | PV model accuracy | Confirm from thesis; compare value range vs sun geometry |
| Occupancy schedule not in dataset | Needed as MPC disturbance | Infer from night setback state + setpoint patterns; get from building operator |
| Full mid-series gap scan not done | Unknown data holes in 2023–2024 | DuckDB gap scan in script 06 will surface these |
| Weather signals start Feb 2024 only | 14-month gap for weather-ML | Use `grealTempAussenGefiltert` (full 3.5 years) as outdoor temp proxy |
