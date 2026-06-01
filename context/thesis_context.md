# Thesis Context

_Source: Guillet, Claire — Master's Thesis 2016 (German) — EnFa Building Energy System_
_Parsed: 2026-05-31_

---

## Building: EnFa (Energiefabrik / Energy Factory)

A German research building designed for near-energy-autonomy. Located in Germany (~49°N latitude). Equipped with a full multi-source energy system: PV (7 strings, ~95 kWp), 4-cluster battery storage, 2 BHKW/CHP units (Viessmann Vitobloc 200, biogas), 3 heat pumps, DHW storage, underfloor heating, concrete core activation (BKT), EV charging stations.

---

## Data Sources (Original System — 2015/2016 era)

The original EnFa data system exported four file types:

| File | Source | Contents |
|---|---|---|
| `.sma` | SMA devices (SunnySensorBox + Sunny Island inverters) | Total irradiance, cluster voltage, cluster power, cluster SOC, cluster current per inverter |
| `.knx` | Suntracer KNX-GPS weather station (roof) | Outdoor temperature, brightness, rain, wind speed, sun position |
| `.bur` | Building meters (15-min and 1-hour intervals) | Flow/return temps, buffer storage temps, underfloor heating, PV energy, HP energy, CHP energy (15-min) |
| `.sws` | Forecast system | Weather forecasts (sunlight, humidity), daily work schedule |

The live InfluxDB system (Dec 2022 onwards) consolidates all of these into a single semicolon-CSV export per signal at ~20-second resolution — a significant upgrade from the 2016 hourly data.

---

## Irradiance — Confirmed Findings

**Instrument:** SMA Sunny SensorBox, roof-mounted horizontally between east- and west-facing modules.
- Type: ASI-PV cell (amorphous silicon)
- Range: 0–1,500 W/m²
- Accuracy: ±8%
- Resolution: 1 W/m²
- Measures **global horizontal irradiance (GHI)**

**In the 2016 thesis:** Irradiance was stored in the `.sma` file as `dblTotalRadiation`, measured **hourly**. The thesis explicitly notes that hourly sampling is insufficient for winter accuracy.

**In the live InfluxDB dataset (2022+):** There is **no confirmed continuous irradiance signal**. The `sun_alt` and `sun_azi` signals are **calculated sun geometry** (altitude and azimuth angles computed from GPS/time) — not measured irradiance. They come from the Suntracer KNX-GPS weather station's built-in sun-position calculator, not from a pyranometer.

**`val1008` / `val1009` analysis:** Both signals show values ~65–94 at 5-second intervals, lasting only 0.7 days (2022-11-30). They are **identical to each other** (same values at same timestamps). At 14:40–15:20 UTC on Nov 30 in Germany (lat 49°N), GHI of 65–94 W/m² is physically plausible for a partly cloudy winter afternoon. **Most probable interpretation: these are test exports of the SMA SunnySensorBox irradiance signal during InfluxDB commissioning in November 2022.** The two duplicate signals suggest the same source was accidentally exported to two measurement names. After the commissioning test, the irradiance signal was not integrated into the continuous InfluxDB export. **Not available for production use.**

**Irradiance gap conclusion:** The EnFa InfluxDB dataset does **not** contain a continuous irradiance signal. For PV forecasting and EnergyPlus calibration, either:
1. A clearsky irradiance model from `sun_alt` + `sun_azi` can be computed (sufficient for summer, less accurate for winter)
2. A weather API feed (Open-Meteo, Solcast) should be added to the ZORO pipeline as a new data source

---

## val1006 / val1007 — Resolved

**Confirmed: commissioning pipeline test signals. Exclude from all analysis.**

Pattern analysis:
- Both start with identical values: 1, 0, 0, 1, -1, 0, -1, 1 (first 8 rows are a ternary test sequence)
- Then val1006 transitions to a counter incrementing by +5 per 5-second step (8, 13, 18, 23, 28, 2, 7, 12...) — cycling modulo ~30
- val1007 diverges after row 8 (values differ)
- Duration: val1006 = 5.1 days, val1007 = 0.9 days
- These were injected into InfluxDB to verify the ingestion pipeline timing and data flow during Nov–Dec 2022 system commissioning
- **Not building energy data. Exclude permanently.**

---

## Battery System — Confirmed from Thesis

- **4 strings (clusters)** of battery cells, each controlled by 3 SMA Sunny Island SI8.0H off-grid inverters (1 master + 2 slaves per string)
- **Lead-acid battery cells** (24 cells per string)
- SMA system tracks per-cluster: voltage, power, SOC, and current per inverter connection
- These map to our `grealCluster_1-4_Spannung` (voltage), `grealCluster_1-4_Ladung` (charge), `green_bat/t1/t2/t3` (likely current or raw cluster state from SMA)
- IU0U charging strategy (standard SMA setting)
- Battery SOH tracking built into Sunny Island firmware

## PV System — Confirmed from Thesis

- **~95 kWp total**, east- and west-facing roof modules
- **SMA Sunny Tripower** solar inverters (12000TL type primarily)
- **7 PV strings** confirmed — matches our `greal_E_PV1` through `greal_E_PV7`
- Irradiance sensor (SunnySensorBox) positioned horizontally on roof

## BHKW/CHP — Confirmed from Thesis

- **2 CHP units** — Viessmann Vitobloc 200 type EM-20/39, biogas-fuelled
- Each unit: ~20 kWel / 39 kWth
- Both units tracked individually in `.bur` data → confirmed by our `greal_LeistungBHKW1/2`, `greal_E_bhkw1/2`
- Heat-led operation primary mode; electricity export secondary

## Heat Pump — Confirmed from Thesis

- **3 heat pump units** (WP1, WP2, WP3)
- Air-source (defrost cycles confirm)
- Max flow temperature used in simulation: 45°C (thesis notes higher temps are rare given good insulation)
- CHP and HP cannot operate simultaneously (EMS constraint — confirmed by interlock logic in signal data)
- HP switches off below ~-5°C outdoor temp (COP too poor)

## EMS Logic — Confirmed from Thesis

1. Heating curve: supply temp computed from outdoor temp
2. Night setback: reduced setpoints outside occupied hours
3. HP-CHP interlock: they don't run simultaneously
4. Battery-HP interlock: HP disabled below SOC threshold (confirmed by `Vreal_WP_Ein_Batterie*` signals)
5. High-tariff demand management: `greal_Administrator_HT`
6. Heat surplus goes to old building buffer tank

## Key Database Variables (Table 25 from Thesis)

| Thesis Variable | File | Meaning | Our Signal |
|---|---|---|---|
| `dblStromErzgPvGesamtkWh` | .bur | Total PV energy generation | `greal_E_PV_Gesamt` |
| `dblStromZWaermepumpeKwh` | .bur | HP electrical consumption | `greal_E_WP` |
| `dblWaermeZWaermepumpe` | .bur | HP heat generation | `greal_WMZ_Hz_Erz_WP` |
| `dblWaermeMengeZBHKW1` | .bur | CHP1 heat output | `greal_WMZ_Hz_Erz_BHKW` |
| `dblStromErzZaehlerBhkwKwh1` | .bur | CHP1 electrical generation | `greal_E_bhkw1` |
| `dblTotalRadiation` | .sma | Global horizontal irradiance | NOT in InfluxDB continuously |
| `dblSOCCluster1` | .sma | Battery cluster 1 SOC | `greal_BatterieLadeZustand` (system-level) |
| `dblPWCluster1` | .sma | Battery cluster 1 power | `grealCluster_1_Ladung` / `green_bat` |
| Outside temperature | .knx | Outdoor temp from KNX station | `grealTempAussenGefiltert` |
