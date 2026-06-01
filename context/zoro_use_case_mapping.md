# ZORO Use-Case Mapping

_Generated: 2026-05-31_

## Pipeline Context

ZORO's production pipeline ingests JSON v1 payloads: `{timestamp, device_id, metric, value, unit}`.
The EnFa signals map directly to this format via the `zoro_pipeline_mapping.csv` report.
**223 of 233 EnFa signals are pipeline-mappable** with a defined `device_id`, `metric`, and `unit`.

---

## ZORO MVP Path Evaluation

### Path A: Energy Analytics Dashboard
**Readiness: READY**

| Required Signal | Available | Quality | Notes |
|---|---|---|---|
| Building total power | `greal_LeistungGebaeude` | High | ~20s, 3.5 years |
| Building total energy | `greal_E_Gesamtverbrauch` | High | Cumulative |
| PV generation power | `real_PV_Gesamt` | High | Total across all strings |
| PV per-string energy | `greal_E_PV1` – `greal_E_PV7` | High | 7 strings identified |
| BHKW generation | `real_P_BHKW`, `real_aktGesamtLeistungBHKW` | High | Both units |
| Battery SOC | `greal_BatterieLadeZustand` | High | 71.5% at start |
| Battery net power | `real_BatterieLeistung` | High | ~20s resolution |
| EV charging power | `greal_LeistungTankStelle1/2/3` | High | 3 chargers |
| Gas consumption | `greal_Gas_bhkwges`, `real_aktVerbrauchGasBhkwImp` | High | BHKW gas |
| Outdoor temperature | `grealTempAussenGefiltert` | High | Filtered signal |

**Grafana dashboard can be built today** from EnFa data as a reference/template for SCS.

---

### Path B: HVAC Optimization Advisory
**Readiness: READY**

| Required Signal | Available | Quality |
|---|---|---|
| Supply/return temperatures | `greal_K/W_WMZ_TV/TR_*` (40+ signals) | High |
| Underfloor heating power | `grealThermLeistungWaermeFBH_Nord/Sued/Halle` | High |
| DHW temperatures | `realIstTempWarmWas*/KaltWas*` (8 signals) | High |
| Night setback state | `greal_Nachtabsenkung`, `V_real_Nachtabsenkung` | High |
| Heating curve | `greal_VorlaufTempKennlinie`, `V_real_maxVorlaufTemp` | High |
| HVAC setpoints | All `V_real_*` files (28 setpoint signals) | High |
| Concrete core temps | `greal_realTempVorlBKT_EG`, `realTempRuecklBKT_EG` | High |
| Damper positions | `greal_StellungFortluftKlappe/UmluftKlappe` | High |
| Outdoor temp | `grealTempAussenGefiltert` | High |

**HVAC setpoint optimization advisory is fully supported.** 3.5 years of heating curve behavior, night setback patterns, and zone-level thermal data available.

---

### Path C: Heat Pump Performance & Fault Detection
**Readiness: READY — strongest dataset**

| Required Signal | Available | Quality |
|---|---|---|
| HP supply temperature | `grealIstWaermepumpVorlauf` | High |
| HP controller setpoint | `realSollwertReglerWP1` | High |
| HP supply/return via WMZ | `greal_W_WMZ_TV/TR_WP` | High |
| HP thermal power | `greal_W_WMZ_P_WP` | High |
| HP heat generation energy | `greal_WMZ_Hz_Erz_WP` | High |
| HP electrical energy | `greal_E_WP`, `greal_AZ_WP_Energie` | High |
| Defrost duration | `greal_WP1/2/3AbtauSek` (3 units!) | High, ~20s |
| Defrost trigger temp | `V_real_AbtauTemperaturBetrieb` | High |
| Battery SOC threshold for HP | `Vreal_WP_Ein_Batterie*` | High |
| Outdoor temperature | `grealTempAussenGefiltert` | High |

**3 heat pump units are tracked separately** (`WP1`, `WP2`, `WP3` in defrost signals). COP can be estimated from heat generation energy vs electrical energy. Defrost cycle detection is possible with ~20s resolution.

---

### Path D: Digital Twin / EnergyPlus Calibration
**Readiness: PARTIALLY READY**

| Required | Available | Gap |
|---|---|---|
| Weather (outdoor temp) | Yes — 3.5 years | No solar irradiance (only sun angle) |
| Energy meters | Yes — comprehensive | — |
| Zone temperatures | Partial — BKT, FBH, server | No room-level zone temps |
| Equipment operation | Yes — HP, BHKW, battery | — |
| Schedules | Yes — timers, night setback | — |
| Building metadata | Not in dataset | Need from thesis |

**Gap:** No direct solar irradiance (W/m²) — only sun altitude/azimuth angles. Can compute approximate GHI from geometry but not ideal. `val1008/1009` could be irradiance (values ~65–92) — needs confirmation from thesis.

---

### Path E: Forecasting + MPC Readiness
**Readiness: PARTIALLY READY**

| Required | Available |
|---|---|
| States (temps, SOC, power) | Yes — 109 signals |
| Control actions (setpoints) | Yes — 28 V_real setpoint signals |
| Disturbances (weather) | Outdoor temp (3.5y), wind/sun (2.2y) |
| Constraints | Setpoint bounds available |
| Objective (energy cost) | HT tariff state available; no electricity price signal |

**Gap:** No electricity spot price or dynamic tariff signal in the dataset. `greal_Administrator_HT` gives high-tariff state (binary), which is sufficient for basic rule-based MPC but not for true price-optimal MPC.

---

## ZORO Use-Case Signal Coverage

| ZORO Use Case | Signals | Readiness |
|---|---|---|
| Energy Analytics Dashboard | 106 | Ready |
| HVAC Optimization | 129 | Ready |
| Heat Pump FDD | 120 | Ready |
| MPC / Setpoint Optimization | 109 | Partially Ready |
| PV Forecasting | 16 | Partially Ready (no irradiance) |
| Battery Optimization | 23 | Ready |
| EnergyPlus Calibration | ~60 | Partially Ready |
| EV Charging Optimization | 6 | Ready |

---

## Pipeline Integration Notes (JSON v1)

Example mappings from EnFa to ZORO JSON v1:

```json
{"timestamp":"2024-02-27T09:12:41Z","device_id":"de-enfa-main-01/battery-system","metric":"battery_soc","value":71.5,"unit":"%"}
{"timestamp":"2024-02-27T09:12:41Z","device_id":"de-enfa-main-01/heat-pump","metric":"supply_temperature","value":42.3,"unit":"C"}
{"timestamp":"2024-02-27T09:12:41Z","device_id":"de-enfa-main-01/pv-system","metric":"pv_power_total","value":12.4,"unit":"kW"}
```

**Building ID convention:** Following ZORO pattern `{iso-country}-{city3}-{site}-{seq}`, EnFa would be e.g. `de-xxx-enfa-01` (city unknown — confirm from thesis).

**Key consideration for SCS:** The SCS building (`de-hnn-bildungscampus-01`) will likely have a similar set of signals. The EnFa signal dictionary can serve as the **canonical signal schema** for German commercial buildings on the ZORO platform.
