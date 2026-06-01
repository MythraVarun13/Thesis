# Modeling Readiness

_Generated: 2026-05-31_

## Ready Now (no additional data required)

| Model | Key Signals | Notes |
|---|---|---|
| HP COP estimation | `greal_WMZ_Hz_Erz_WP` / `greal_E_WP` | Daily/weekly rolling ratio |
| Defrost cycle detection | `greal_WP1/2/3AbtauSek` | Threshold + trend on 3 units |
| Heating curve deviation | `grealIstWaermepumpVorlauf`, `greal_VorlaufTempKennlinie`, `grealTempAussenGefiltert` | Supply temp vs expected from curve |
| BHKW electrical efficiency | `real_P_BHKW` / `greal_Gas_bhkwges` | Electrical efficiency ratio |
| Battery round-trip efficiency | `greal_E_BatterieLaden` / `greal_E_BatterieAbgabe` | Charge vs discharge energy |
| Energy balance | PV + BHKW vs building load + battery | Source accounting |
| Phase current imbalance FDD | `realIPhARms*`, `realIPhBRms*`, phase C | 2 panels (ST24, ST25) |
| WMZ thermal power cross-check | Supply/return temp delta × flow rate | Flow rate not directly available — proxy from thermal power signal |

## Feasible with Minor Additions

| Model | Gap | Solution |
|---|---|---|
| Load forecasting | Occupancy schedule | Add from thesis or building operator |
| PV generation forecasting | Irradiance (W/m²) | Confirm val1008/val1009 or use clearsky model from sun_alt/azi |
| Night setback optimisation | Occupancy start/end times | Inferable from night setback state + setpoint signals |
| HP predictive maintenance | Baseline period definition | Use Dec 2022 – Dec 2023 as training baseline |

## Requires Additional Data

| Model | What's Missing |
|---|---|
| Room thermal comfort | No room temperature sensors in dataset |
| Price-optimal battery/HP dispatch | No electricity spot price signal |
| EnergyPlus calibration | Building geometry, confirmed irradiance, zone temperatures |
| Neuberger/SCS format parsing | Awaiting first SCS payload on Kafka topic |

## Data Volume for Modeling

At ~20s sampling: approximately **1.57 million rows per signal per year**. Over 3.5 years: ~5.5M rows per signal. Recommended approach:
- Resample to 5-minute intervals for most ML models (~105K rows/year per signal)
- Keep 20s resolution for defrost cycle detection and FDD
- Use DuckDB for efficient aggregation without loading full files into memory
