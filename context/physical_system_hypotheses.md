# Physical System Hypotheses

_Generated: 2026-05-31_

## Building: EnFa (Energieeffizienzfabrik or similar)

A German research/commercial building with a multi-source energy system. Based on signal analysis:

- **Multiple heating zones:** Altbau (old building), Nord, Sued, Halle (hall), Bespr (conference), Server room
- **Building core activation (BKT):** Betonkerntemperierung — concrete thermal mass used for heating/cooling
- **Underfloor heating (FBH):** Floor heating in multiple zones (Nord, Sued, Halle, upper floor OG)
- **Ventilation:** Controlled exhaust (Fortluft) and recirculation (Umluft) dampers
- **EV charging:** 3 charging stations (Tankstellen)

---

## Heat Pump System (WP — Wärmepumpe)

- **3 heat pump units** (WP1, WP2, WP3 — confirmed from `greal_WP1/2/3AbtauSek`)
- **Defrost cycles:** All 3 units have defrost duration tracking at ~20s resolution
- **Supply temperature:** Controlled via heating curve (`greal_VorlaufTempKennlinie`)
- **Heating curve parameters:** `V_real_maxVorlaufTemp`, `V_real_minVorlaufTemp`, `V_real_maxAT`, `V_real_minAT`
- **Night setback:** Active — `V_real_Nachtabsenkung` is the setpoint
- **Battery interlock:** HP is disabled below a battery SOC threshold (`Vreal_WP_Ein_Batterie*`)
- **Hypothesis:** Air-source heat pump (defrost cycles confirm outdoor air source)
- **COP estimation:** Possible — heat generation energy (`greal_WMZ_Hz_Erz_WP`) / electrical energy (`greal_E_WP`)

---

## BHKW / CHP System (Blockheizkraftwerk)

- **2 BHKW units** (`bhkw1`, `bhkw2` — confirmed from WMZ signals and power signals)
- **Gas consumption:** Tracked via pulse counters (`dintVolGasVerbrauchBhkwImp1/2`) and active rate (`real_aktVerbrauchGasBhkwImp`)
- **Electrical output:** `real_P_BHKW`, `real_aktGesamtLeistungBHKW`, `greal_LeistungBHKW1/2`
- **Heat output:** Via WMZ heat meters per unit
- **Loss tracking:** `real_aktVerlustLeistungBHKW`, `real_E_Verlustbhkw1/2`
- **DHW integration:** BHKW controls DHW storage (`VrealSpeicherWW_BHKW_Ein/Aus` — 50°C setpoint confirmed)

---

## PV System (Photovoltaik)

- **7 PV strings** (confirmed: `greal_E_PV1` through `greal_E_PV7`)
- **Total system:** `real_PV_Gesamt` (power), `greal_E_PV_Gesamt` (energy)
- **Forecast:** `greal_PV_Ges_prog` — PV production prognosis exists
- **Sun tracking:** `sun_alt` (altitude), `sun_azi` (azimuth) — from 2024-02-27
- **Missing:** No direct irradiance (W/m²) signal confirmed. `val1008/val1009` (values ~65–92, 5s interval) are candidates — could be irradiance in W/m² × 10 or some other analog signal

---

## Battery Energy Storage System (BESS)

- **4 battery clusters** (confirmed: `grealCluster_1-4_Spannung/Ladung`)
- **Individual cluster:** Voltage (V), charge (Ah) per cluster
- **Raw cluster data:** `green_bat`, `green_t1/t2/t3` — irregular interval (~5 min), likely current or state per cluster
- **System-level:** SOC (`greal_BatterieLadeZustand`), net power (`real_BatterieLeistung`), charge/discharge power separate
- **Loss tracking:** Battery losses tracked (`real_BatterieVerlustLeistung/Energie`)
- **HP interlock:** Battery SOC gates heat pump operation — energy management logic present

---

## DHW / Thermal Storage System

- **Warm water storage:** 4 temperature sensors at different heights (`ObenMitte`, `UntMitte`, `Oben`, `Unt`)
- **Cold water storage:** Same 4-point profile
- **Buffer tank (Pufferspeicher):** `realIstTempPuffAltbau`, `realIstTempRuecklPuffAltbau` — separate buffer for old building
- **Storage fill level:** `greal_Speicher_WW_Prozent` — percentage signal
- **BHKW setpoints:** DHW storage is heated by BHKW with on/off temperature setpoints

---

## Weather / Forecast

- **Outdoor temperature:** `grealTempAussenGefiltert` — filtered signal, continuous since Dec 2022
- **Wind (current):** `wind_now` — since Feb 2024
- **Wind (forecast):** `wind_tomorrow` — since Feb 2024
- **Sun geometry:** `sun_alt`, `sun_azi` — since Feb 2024
- **Gap:** No solar irradiance or cloud cover signal confirmed

---

## Electrical Grid / Metering

- **Phase currents:** At least 2 electrical panels (`ST24`, `ST25`) with 3-phase current RMS
- **Power factor:** Per panel
- **Net metering:** `real_WirkleistungEnFa` — net active power (import/export)
- **Generation metering:** `real_WirkleistungErzeugungEnFa`
- **Tariff management:** `greal_Administrator_HT` — high-tariff state flag

---

## Energy Management System (EMS) Logic

From setpoint signals, the EMS implements:
1. **Heating curve** — supply temp varies with outdoor temp (standard German HVAC control)
2. **Night setback** — reduced setpoint outside occupied hours
3. **Weekend mode** — `greal_Wochenendwert` weekend setpoint
4. **Battery-HP interlock** — HP disabled when battery SOC below threshold
5. **BHKW-DHW coupling** — BHKW heats DHW storage to defined setpoints
6. **High-tariff avoidance** — HT flag available for demand shifting logic

This is a **complete multi-source EMS** — ideal reference architecture for ZORO's supervisory optimization layer.
