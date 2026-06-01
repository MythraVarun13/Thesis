"""
zoro_eda.signal_rules
=====================
Signal classification rules for the EnFa building energy dataset.

This module contains **only data** — no business logic.  The matching
logic lives in ``05_classify_signals.py`` (or ``zoro_eda.classify``).

Two lookup structures are provided:

``DIRECT_MAP``
    Exact signal-stem → classification tuple.  Used first so edge cases
    (underscores, German umlaut variants, casing mismatches) are handled
    explicitly without fragile pattern matching.

``PATTERN_RULES``
    Ordered list of (substrings, ...) rules applied when no direct match
    is found.  All substrings must be present (case-insensitive) for a
    match.  Evaluated top-to-bottom; first match wins.

Tuple schema (both structures)
-------------------------------
(category, english_meaning, unit_hypothesis, confidence,
 zoro_device_id_suffix, zoro_metric, zoro_unit,
 exclude, use_cases)

where ``use_cases`` is a list of strings from:
    energy | hvac | heatpump | pv | battery | weather | fdd | mpc
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Type alias for a classification tuple
# ---------------------------------------------------------------------------
# (category, english, unit, confidence, device_suffix, metric, zoro_unit,
#  exclude, use_cases)
ClassificationTuple = tuple[
    str, str, str, str,           # category, english, unit, confidence
    str | None, str | None, str | None,  # device_suffix, metric, zoro_unit
    bool, list[str],              # exclude, use_cases
]

# ---------------------------------------------------------------------------
# Direct map — exact signal stem (filename without .csv) → tuple
# ---------------------------------------------------------------------------
DIRECT_MAP: dict[str, ClassificationTuple] = {
    # ── Commissioning test artifacts (exclude) ──────────────────────────────
    "A":      ("EXCLUDE", "Ramp test artifact", "", "high", None, None, None, True, []),
    "_value": ("EXCLUDE", "Counter ramp test artifact", "", "high", None, None, None, True, []),
    "pilot":  ("EXCLUDE", "CPU monitoring — not energy data", "", "high", None, None, None, True, []),
    "val1006": ("EXCLUDE", "Commissioning pipeline test signal (counter pattern)", "", "high", None, None, None, True, []),
    "val1007": ("EXCLUDE", "Commissioning pipeline test signal (counter pattern)", "", "high", None, None, None, True, []),
    "val1008": ("EXCLUDE", "SMA irradiance commissioning test (0.7 days only)", "", "high", None, None, None, True, []),
    "val1009": ("EXCLUDE", "SMA irradiance commissioning test (0.7 days only, duplicate of val1008)", "", "high", None, None, None, True, []),

    # ── Heat pump (casing / umlaut edge cases) ──────────────────────────────
    "grealIstWaermepumpVorlauf": (
        "hp_supply_temp", "Heat pump supply temperature", "C", "high",
        "heat-pump", "supply_temperature", "C", False,
        ["heatpump", "hvac", "mpc", "fdd"],
    ),
    "realSollwertReglerWP1": (
        "hp_setpoint", "Heat pump 1 controller setpoint", "C", "high",
        "heat-pump", "controller_setpoint", "C", False,
        ["heatpump", "hvac", "mpc"],
    ),
    "V_realHysWP": (
        "hp_setpoint", "Heat pump hysteresis setpoint", "K", "high",
        "heat-pump", "hysteresis_setpoint", "K", False,
        ["heatpump", "hvac"],
    ),
    "V_realMaxVL_WP": (
        "hp_setpoint", "Max supply temp setpoint (HP)", "C", "high",
        "heat-pump", "max_supply_temp_setpoint", "C", False,
        ["heatpump", "hvac", "mpc"],
    ),
    "V_realMinVL_WPcool": (
        "hp_setpoint", "Min supply temp setpoint (HP cooling)", "C", "high",
        "heat-pump", "min_supply_temp_cool_setpoint", "C", False,
        ["heatpump", "hvac", "mpc"],
    ),

    # ── PV per-string ───────────────────────────────────────────────────────
    "greal_E_PV1": ("pv_energy", "PV string 1 energy", "kWh", "high", "pv-string-1", "pv_energy", "kWh", False, ["energy", "pv"]),
    "greal_E_PV2": ("pv_energy", "PV string 2 energy", "kWh", "high", "pv-string-2", "pv_energy", "kWh", False, ["energy", "pv"]),
    "greal_E_PV3": ("pv_energy", "PV string 3 energy", "kWh", "high", "pv-string-3", "pv_energy", "kWh", False, ["energy", "pv"]),
    "greal_E_PV4": ("pv_energy", "PV string 4 energy", "kWh", "high", "pv-string-4", "pv_energy", "kWh", False, ["energy", "pv"]),
    "greal_E_PV5": ("pv_energy", "PV string 5 energy", "kWh", "high", "pv-string-5", "pv_energy", "kWh", False, ["energy", "pv"]),
    "greal_E_PV6": ("pv_energy", "PV string 6 energy", "kWh", "high", "pv-string-6", "pv_energy", "kWh", False, ["energy", "pv"]),
    "greal_E_PV7": ("pv_energy", "PV string 7 energy", "kWh", "high", "pv-string-7", "pv_energy", "kWh", False, ["energy", "pv"]),
    "greal_E_PV_Gesamt": ("pv_energy", "PV total energy all strings", "kWh", "high", "pv-system", "pv_energy_total", "kWh", False, ["energy", "pv", "mpc"]),
    "greal_PV_Ges_prog": ("pv_forecast", "PV generation forecast", "kWh", "high", "pv-system", "pv_energy_forecast", "kWh", False, ["pv", "mpc", "weather"]),

    # ── EV charging ─────────────────────────────────────────────────────────
    "greal_E_Tankstelle1": ("ev_energy", "EV charger 1 energy", "kWh", "high", "ev-charger-1", "energy", "kWh", False, ["energy"]),
    "greal_E_Tankstelle2": ("ev_energy", "EV charger 2 energy", "kWh", "high", "ev-charger-2", "energy", "kWh", False, ["energy"]),
    "greal_E_Tankstelle3": ("ev_energy", "EV charger 3 energy", "kWh", "high", "ev-charger-3", "energy", "kWh", False, ["energy"]),
    "greal_LeistungTankStelle1": ("ev_power", "EV charger 1 power", "kW", "high", "ev-charger-1", "power", "kW", False, ["energy", "mpc"]),
    "greal_LeistungTankStelle2": ("ev_power", "EV charger 2 power", "kW", "high", "ev-charger-2", "power", "kW", False, ["energy", "mpc"]),
    "greal_LeistungTankStelle3": ("ev_power", "EV charger 3 power", "kW", "high", "ev-charger-3", "power", "kW", False, ["energy", "mpc"]),

    # ── BHKW individual units ───────────────────────────────────────────────
    "greal_LeistungBHKW1": ("chp_power", "BHKW unit 1 power", "kW", "high", "bhkw-1", "electrical_power", "kW", False, ["energy", "fdd"]),
    "greal_LeistungBHKW2": ("chp_power", "BHKW unit 2 power", "kW", "high", "bhkw-2", "electrical_power", "kW", False, ["energy", "fdd"]),
    "greal_E_bhkw1": ("chp_energy", "BHKW unit 1 electrical energy", "kWh", "high", "bhkw-1", "electrical_energy", "kWh", False, ["energy"]),
    "greal_E_bhkw2": ("chp_energy", "BHKW unit 2 electrical energy", "kWh", "high", "bhkw-2", "electrical_energy", "kWh", False, ["energy"]),
    "greal_Gas_bhkw1": ("chp_gas", "BHKW unit 1 gas consumption", "m3", "high", "bhkw-1", "gas_volume", "m3", False, ["energy", "fdd"]),
    "greal_Gas_bhkw2": ("chp_gas", "BHKW unit 2 gas consumption", "m3", "high", "bhkw-2", "gas_volume", "m3", False, ["energy", "fdd"]),
    "greal_Gas_bhkwges": ("chp_gas", "BHKW total gas consumption", "m3", "high", "bhkw", "gas_volume_total", "m3", False, ["energy", "mpc"]),
    "greal_E_WP": ("hp_energy", "Heat pump total electrical energy", "kWh", "high", "heat-pump", "electrical_energy", "kWh", False, ["heatpump", "energy", "fdd"]),

    # ── Heat meter energy per zone (heating circuit) ─────────────────────────
    "greal_W_WMZ_E_Altbau": ("thermal_energy", "Heating energy old building", "kWh", "high", "heat-meter-altbau", "thermal_energy", "kWh", False, ["hvac", "energy"]),
    "greal_W_WMZ_E_Halle":  ("thermal_energy", "Heating energy hall",         "kWh", "high", "heat-meter-halle",  "thermal_energy", "kWh", False, ["hvac", "energy"]),
    "greal_W_WMZ_E_Nord":   ("thermal_energy", "Heating energy north zone",   "kWh", "high", "heat-meter-nord",   "thermal_energy", "kWh", False, ["hvac", "energy"]),
    "greal_W_WMZ_E_Sued":   ("thermal_energy", "Heating energy south zone",   "kWh", "high", "heat-meter-sued",   "thermal_energy", "kWh", False, ["hvac", "energy"]),
    "greal_W_WMZ_E_WP":     ("thermal_energy", "Heating energy heat pump circuit", "kWh", "high", "heat-meter-wp", "thermal_energy", "kWh", False, ["hvac", "heatpump", "energy"]),
    "greal_W_WMZ_E_bhkw1":  ("thermal_energy", "Heating energy BHKW 1 circuit", "kWh", "high", "heat-meter-bhkw1", "thermal_energy", "kWh", False, ["hvac", "energy"]),
    "greal_W_WMZ_E_bhkw2":  ("thermal_energy", "Heating energy BHKW 2 circuit", "kWh", "high", "heat-meter-bhkw2", "thermal_energy", "kWh", False, ["hvac", "energy"]),

    # ── Heat generation totals ───────────────────────────────────────────────
    "greal_WMZ_Hz_Erz_BHKW": ("thermal_energy", "Heat generation energy from BHKW", "kWh", "high", "bhkw", "heat_generation_energy", "kWh", False, ["energy", "fdd"]),
    "greal_WMZ_Hz_Erz_WP":   ("thermal_energy", "Heat generation energy from heat pump", "kWh", "high", "heat-pump", "heat_generation_energy", "kWh", False, ["energy", "heatpump", "fdd"]),
    "greal_WMZ_Hz_Erz_ges":  ("thermal_energy", "Total heat generation energy", "kWh", "high", "building-system", "heat_generation_energy_total", "kWh", False, ["energy", "mpc"]),
    "greal_WMZ_Warm":        ("thermal_energy", "Total heating circuit energy", "kWh", "high", "heat-meter", "heating_energy_total", "kWh", False, ["hvac", "energy"]),
    "greal_E__WMZ_BHKW":     ("thermal_energy", "BHKW heat meter total energy", "kWh", "high", "heat-meter-bhkw", "thermal_energy", "kWh", False, ["energy", "fdd"]),
    "greal_E__WMZ_WWout":    ("thermal_energy", "DHW heat meter output energy", "kWh", "high", "heat-meter-dhw", "dhw_output_energy", "kWh", False, ["energy", "hvac"]),

    # ── DHW storage ─────────────────────────────────────────────────────────
    "greal_Speicher_WW_Prozent": ("dhw_level", "DHW storage fill level", "%", "high", "dhw-storage", "fill_level_percent", "%", False, ["hvac", "fdd", "mpc"]),

    # ── Underfloor heating temps (underscores break pattern matching) ────────
    "greal_RL_TempFBH_OG": ("zone_return_temp", "Underfloor heating return temp upper floor", "C", "high", "underfloor-heating-og", "return_temperature", "C", False, ["hvac", "fdd"]),
    "greal_VL_TempFBH_OG": ("zone_supply_temp", "Underfloor heating supply temp upper floor", "C", "high", "underfloor-heating-og", "supply_temperature", "C", False, ["hvac", "fdd", "mpc"]),

    # ── Concrete core activation (BKT) ───────────────────────────────────────
    "greal_realTempVorlBKT_EG": ("zone_supply_temp", "Concrete core supply temp ground floor", "C", "high", "bkt-eg", "supply_temperature", "C", False, ["hvac", "fdd", "mpc"]),
    "realTempRuecklBKT_EG":     ("zone_return_temp", "Concrete core return temp ground floor", "C", "high", "bkt-eg", "return_temperature", "C", False, ["hvac", "fdd"]),

    # ── Ventilation dampers (underscores break pattern matching) ─────────────
    "greal_StellungFortluftKlappe": ("damper_position", "Exhaust air damper position", "%", "high", "ventilation", "exhaust_damper_position", "%", False, ["hvac", "fdd"]),
    "greal_StellungUmluftKlappe":   ("damper_position", "Recirculation damper position", "%", "high", "ventilation", "recirculation_damper_position", "%", False, ["hvac", "fdd"]),
}

# ---------------------------------------------------------------------------
# Pattern rules — ordered; first matching rule wins
# Each entry: (substrings_list, *classification_tuple_fields)
# ALL substrings must be present in the lowercased signal name.
# ---------------------------------------------------------------------------
PATTERN_RULES: list[tuple[list[str], ClassificationTuple]] = [
    # ── Weather ─────────────────────────────────────────────────────────────
    (["wind_now"],      ("weather",          "Wind speed current",          "m/s", "high",   "weather-station", "wind_speed_now",           "m/s",  False, ["weather", "mpc", "pv"])),
    (["wind_tomorrow"], ("weather_forecast", "Wind speed tomorrow forecast", "m/s", "high",  "weather-station", "wind_speed_forecast",       "m/s",  False, ["weather", "mpc", "pv"])),
    (["sun_alt"],       ("solar",            "Sun altitude angle",           "deg", "high",   "weather-station", "sun_altitude",             "deg",  False, ["weather", "pv", "mpc"])),
    (["sun_azi"],       ("solar",            "Sun azimuth angle",            "deg", "high",   "weather-station", "sun_azimuth",              "deg",  False, ["weather", "pv", "mpc"])),
    (["grealtempaussen"], ("outdoor_temp",   "Outdoor temperature filtered", "C",   "high",   "weather-station", "outdoor_temperature",      "C",    False, ["weather", "hvac", "mpc", "heatpump"])),
    (["v_real_maxat"],  ("hvac_setpoint",    "Max outdoor temp threshold HP","C",   "high",   "heat-pump-controller", "max_outdoor_temp_threshold", "C", False, ["hvac", "heatpump"])),
    (["v_real_minat"],  ("hvac_setpoint",    "Min outdoor temp threshold HP","C",   "high",   "heat-pump-controller", "min_outdoor_temp_threshold", "C", False, ["hvac", "heatpump"])),

    # ── PV ──────────────────────────────────────────────────────────────────
    (["real_pv_gesamt"],        ("pv_generation", "PV total power output",        "kW",  "high",   "pv-system",         "pv_power_total",           "kW",  False, ["energy", "pv", "mpc"])),
    (["greal_e_erzeugung"],     ("pv_generation", "PV total energy generated",    "kWh", "high",   "pv-system",         "pv_energy_total",          "kWh", False, ["energy", "pv"])),
    (["real_wirkleistungerzeugung"], ("pv_generation", "Active power generation PV+BHKW", "kW", "medium", "generation-system", "active_power_generation", "kW", False, ["energy", "pv", "fdd"])),
    (["real_wirkleistungenfa"],      ("building_power", "Building active power net", "kW", "medium", "building-meter", "active_power_net", "kW", False, ["energy", "hvac", "mpc"])),
    (["greal_leistunggebaeude"],     ("building_power", "Building electrical power demand", "kW", "high", "building-meter", "electrical_power_demand", "kW", False, ["energy", "hvac", "mpc", "fdd"])),
    (["realleistunggeb"],            ("building_power", "Building zone electrical power", "kW", "medium", "building-meter", "zone_electrical_power", "kW", False, ["energy"])),
    (["greal_e_gebaeude"],           ("building_energy", "Building electrical energy", "kWh", "high", "building-meter", "electrical_energy_total", "kWh", False, ["energy"])),
    (["greal_e_gesamtverbrauch"],    ("building_energy", "Total energy consumption", "kWh", "high", "building-meter", "total_energy_consumption", "kWh", False, ["energy", "mpc"])),

    # ── Battery ──────────────────────────────────────────────────────────────
    (["greal_batterieladezustand"],   ("battery_soc",     "Battery state of charge",        "%",   "high",   "battery-system",  "battery_soc",             "%",   False, ["battery", "energy", "mpc"])),
    (["real_batterieleistung"],       ("battery_power",   "Battery net power",               "kW",  "high",   "battery-system",  "battery_power_net",       "kW",  False, ["battery", "energy", "mpc", "fdd"])),
    (["real_batterieladeleis"],       ("battery_power",   "Battery charge power",            "kW",  "high",   "battery-system",  "battery_charge_power",    "kW",  False, ["battery", "energy", "mpc"])),
    (["real_batterieabgabeleis"],     ("battery_power",   "Battery discharge power",         "kW",  "high",   "battery-system",  "battery_discharge_power", "kW",  False, ["battery", "energy", "mpc"])),
    (["real_batterieverlustleis"],    ("battery_power",   "Battery loss power",              "kW",  "high",   "battery-system",  "battery_loss_power",      "kW",  False, ["battery", "fdd"])),
    (["real_batterieverlustenergie"], ("battery_energy",  "Battery loss energy",             "kWh", "high",   "battery-system",  "battery_loss_energy",     "kWh", False, ["battery", "fdd"])),
    (["greal_e_batterieladen"],       ("battery_energy",  "Battery energy charged",          "kWh", "high",   "battery-system",  "battery_energy_charged",  "kWh", False, ["battery", "energy"])),
    (["greal_e_batterieabgabe"],      ("battery_energy",  "Battery energy discharged",       "kWh", "high",   "battery-system",  "battery_energy_discharged","kWh",False, ["battery", "energy"])),
    (["grealcluster", "spannung"],    ("battery_voltage", "Battery cluster voltage",         "V",   "high",   "battery-cluster", "battery_cluster_voltage", "V",   False, ["battery", "fdd"])),
    (["grealcluster", "ladung"],      ("battery_charge",  "Battery cluster charge",          "Ah",  "medium", "battery-cluster", "battery_cluster_charge",  "Ah",  False, ["battery", "fdd"])),
    (["green_bat"],                   ("battery_current", "Battery cluster current raw",     "A",   "medium", "battery-cluster", "battery_cluster_current", "A",   False, ["battery", "fdd"])),
    (["green_t"],                     ("battery_temp",    "Battery cluster temperature",     "C",   "medium", "battery-cluster", "battery_cluster_temp",    "C",   False, ["battery", "fdd"])),
    (["vreal_wp_ein_batterie"],       ("battery_setpoint","Battery SOC threshold for HP",   "%",   "high",   "battery-controller", "hp_enable_battery_soc_threshold", "%", False, ["battery", "heatpump", "mpc"])),

    # ── Heat pump ────────────────────────────────────────────────────────────
    (["v_real_hyswp"],   ("hp_setpoint", "Heat pump hysteresis setpoint",         "K",  "high",   "heat-pump", "hysteresis_setpoint",           "K",  False, ["heatpump", "hvac"])),
    (["v_real_maxvl"],   ("hp_setpoint", "Max supply temp setpoint HP",            "C",  "high",   "heat-pump", "max_supply_temp_setpoint",      "C",  False, ["heatpump", "hvac", "mpc"])),
    (["v_real_minvl"],   ("hp_setpoint", "Min supply temp cool setpoint HP",       "C",  "high",   "heat-pump", "min_supply_temp_cool_setpoint", "C",  False, ["heatpump", "hvac", "mpc"])),
    (["greal_wp", "abtau"], ("hp_defrost", "Heat pump defrost duration",           "s",  "high",   "heat-pump", "defrost_duration",              "s",  False, ["heatpump", "fdd"])),
    (["v_real_abtau"],   ("hp_defrost",  "Heat pump defrost trigger temp",         "C",  "high",   "heat-pump", "defrost_trigger_temp",          "C",  False, ["heatpump", "fdd"])),
    (["greal_az_wp_energie"], ("hp_energy", "Heat pump compressor energy",         "kWh","high",   "heat-pump", "compressor_energy",             "kWh",False, ["heatpump", "energy", "fdd"])),
    (["v_realaz"],       ("hp_setpoint", "HP runtime setpoint",                    "h",  "medium", "heat-pump", "runtime_setpoint",              "h",  False, ["heatpump"])),
    (["v_realsolltempaz"], ("hp_setpoint", "HP max setpoint temp for runtime",     "C",  "medium", "heat-pump", "max_setpoint_temp_runtime",     "C",  False, ["heatpump"])),

    # ── BHKW / CHP ───────────────────────────────────────────────────────────
    (["real_p_bhkw"],              ("chp_power", "BHKW electrical power output",  "kW",  "high",   "bhkw", "electrical_power",       "kW",  False, ["energy", "fdd", "mpc"])),
    (["real_aktgesamtleistungbhkw"],("chp_power","BHKW total active power",       "kW",  "high",   "bhkw", "total_active_power",     "kW",  False, ["energy", "fdd"])),
    (["real_aktverlustleistungbhkw"],("chp_loss","BHKW loss power",               "kW",  "high",   "bhkw", "loss_power",             "kW",  False, ["fdd"])),
    (["real_e_verlustbhkw"],        ("chp_loss", "BHKW loss energy",              "kWh", "high",   "bhkw", "loss_energy",            "kWh", False, ["fdd"])),
    (["real_aktverbrauchgasbhkw"],  ("chp_gas",  "BHKW gas consumption rate",     "m3/h","medium", "bhkw", "gas_consumption_rate",   "m3/h",False, ["energy", "fdd"])),
    (["dintvolgas"],                 ("chp_gas",  "BHKW gas volume counter",       "m3",  "medium", "bhkw", "gas_volume_counter",     "m3",  False, ["energy"])),
    (["real_verlustleistungenfa"],   ("system_loss","EnFa system loss power",      "kW",  "medium", "building-system","system_loss_power","kW",  False, ["energy", "fdd"])),
    (["real_e_verlust"],             ("system_loss","EnFa system loss energy",     "kWh", "medium", "building-system","system_loss_energy","kWh",False, ["energy", "fdd"])),

    # ── Heat meters (WMZ) ────────────────────────────────────────────────────
    (["greal_k_wmz_tr"], ("heating_return_temp", "Heating return temp cooling circuit", "C",   "high", "heat-meter", "return_temperature", "C",   False, ["hvac", "heatpump", "fdd", "mpc"])),
    (["greal_k_wmz_tv"], ("heating_supply_temp", "Heating supply temp cooling circuit", "C",   "high", "heat-meter", "supply_temperature", "C",   False, ["hvac", "heatpump", "fdd", "mpc"])),
    (["greal_k_wmz_p"],  ("thermal_power",       "Thermal power cooling circuit",       "kW",  "high", "heat-meter", "thermal_power",      "kW",  False, ["hvac", "energy", "fdd", "mpc"])),
    (["greal_k_wmz_e"],  ("thermal_energy",      "Thermal energy cooling circuit",      "kWh", "high", "heat-meter", "thermal_energy",     "kWh", False, ["hvac", "energy"])),
    (["greal_w_wmz_tr"], ("heating_return_temp", "Heating return temp heating circuit", "C",   "high", "heat-meter", "return_temperature", "C",   False, ["hvac", "heatpump", "fdd", "mpc"])),
    (["greal_w_wmz_tv"], ("heating_supply_temp", "Heating supply temp heating circuit", "C",   "high", "heat-meter", "supply_temperature", "C",   False, ["hvac", "heatpump", "fdd", "mpc"])),
    (["greal_w_wmz_p"],  ("thermal_power",       "Thermal power heating circuit",       "kW",  "high", "heat-meter", "thermal_power",      "kW",  False, ["hvac", "energy", "fdd", "mpc"])),
    (["greal_wmz_kalt"], ("thermal_energy",      "Heat meter energy cooling total",     "kWh", "high", "heat-meter", "cooling_energy_total","kWh",False, ["hvac", "energy"])),
    (["greal_ek_wmz"],   ("thermal_energy",      "Heat meter energy DHW output",        "kWh", "high", "heat-meter", "dhw_energy_output",  "kWh", False, ["hvac", "energy"])),

    # ── DHW / thermal storage ─────────────────────────────────────────────────
    (["realisttempwarmwas"],    ("dhw_temp",         "DHW warm water temperature",       "C",   "high",   "dhw-storage",       "dhw_temperature",                  "C",  False, ["hvac", "fdd", "mpc"])),
    (["realisttempkaltwas"],    ("dhw_temp",         "Cold water temperature",           "C",   "high",   "dhw-storage",       "cold_water_temperature",           "C",  False, ["hvac", "fdd"])),
    (["realisttempruecklpuff"], ("buffer_temp",      "Buffer tank return temperature",   "C",   "high",   "buffer-tank",       "return_temperature",               "C",  False, ["hvac", "fdd"])),
    (["realisttemppuff"],       ("buffer_temp",      "Buffer tank temperature",          "C",   "high",   "buffer-tank",       "temperature",                      "C",  False, ["hvac", "fdd"])),
    (["vrealspeicherww"],       ("dhw_setpoint",     "DHW storage setpoint",            "C",   "high",   "dhw-controller",    "dhw_setpoint",                     "C",  False, ["hvac", "mpc"])),
    (["vreal_maxspeicher"],     ("storage_setpoint", "Max storage setpoint",            "C",   "medium", "storage-controller","max_storage_setpoint",             "C",  False, ["hvac", "mpc"])),
    (["vreal_minspeicher"],     ("storage_setpoint", "Min storage setpoint",            "C",   "medium", "storage-controller","min_storage_setpoint",             "C",  False, ["hvac", "mpc"])),
    (["vreal_maxtempspeicher"], ("storage_setpoint", "Max temp lower storage setpoint", "C",   "medium", "storage-controller","max_temp_lower_storage_setpoint",  "C",  False, ["hvac"])),

    # ── Underfloor heating / thermal zones ────────────────────────────────────
    (["grealthermleistungwaermefbh_nord"], ("thermal_power", "Underfloor heating power North", "kW", "high", "underfloor-heating-nord", "thermal_power", "kW", False, ["hvac", "energy", "mpc"])),
    (["grealthermleistungwaermefbh_sued"], ("thermal_power", "Underfloor heating power South", "kW", "high", "underfloor-heating-sued", "thermal_power", "kW", False, ["hvac", "energy", "mpc"])),
    (["grealthermleistungwaermehalle"],    ("thermal_power", "Underfloor heating power Hall",  "kW", "high", "underfloor-heating-hall", "thermal_power", "kW", False, ["hvac", "energy", "mpc"])),
    (["greal_soll_t_bkt"],  ("zone_setpoint",   "Concrete core activation setpoint",        "C",  "high",   "bkt-controller", "setpoint",          "C",  False, ["hvac", "mpc"])),

    # ── Heating curve / control parameters ────────────────────────────────────
    (["greal_vorlauftempkennlinie"], ("heating_curve", "Heating curve supply temp calculated", "C", "high", "heat-pump-controller", "heating_curve_supply_temp", "C", False, ["hvac", "mpc"])),
    (["v_real_maxvorlauftemp"],      ("heating_curve", "Heating curve max supply temp setpoint", "C", "high", "heat-pump-controller", "max_supply_temp_setpoint", "C", False, ["hvac", "mpc"])),
    (["v_real_minvorlauftemp"],      ("heating_curve", "Heating curve min supply temp setpoint", "C", "high", "heat-pump-controller", "min_supply_temp_setpoint", "C", False, ["hvac", "mpc"])),
    (["greal_nachtabsenkung"],  ("night_setback", "Night setback active state",  "",  "high", "hvac-controller", "night_setback_active",  "bool", False, ["hvac", "mpc"])),
    (["v_real_nachtabsenkung"], ("night_setback", "Night setback setpoint",      "C", "high", "hvac-controller", "night_setback_setpoint", "C",   False, ["hvac", "mpc"])),
    (["greal_solltempazplus"],  ("hvac_setpoint", "Heating setpoint AZ+",        "C", "medium","hvac-controller","heating_setpoint_az_plus","C",  False, ["hvac", "mpc"])),
    (["greal_wochenendwert"],   ("hvac_setpoint", "Weekend setpoint value",       "C", "medium","hvac-controller","weekend_setpoint",        "C",  False, ["hvac", "mpc"])),

    # ── Room / server temperatures ─────────────────────────────────────────────
    (["greal_t_server"],  ("indoor_temp",    "Server room temperature",          "C",  "high",   "zone-sensor-server", "indoor_temperature", "C",  False, ["hvac", "fdd"])),

    # ── Ventilation ───────────────────────────────────────────────────────────
    (["greal_jalousien"],  ("control_param", "Blind shading max wind threshold", "m/s","medium", "shading-controller", "max_wind_threshold", "m/s", False, ["hvac"])),

    # ── Electrical metering ───────────────────────────────────────────────────
    (["realipharms"],      ("current_rms",  "Phase A current RMS", "A", "high", "electrical-meter", "phase_a_current_rms", "A", False, ["energy", "fdd"])),
    (["realiphbrms"],      ("current_rms",  "Phase B current RMS", "A", "high", "electrical-meter", "phase_b_current_rms", "A", False, ["energy", "fdd"])),
    (["realiph"],          ("current_rms",  "Phase current RMS",   "A", "high", "electrical-meter", "phase_current_rms",   "A", False, ["energy", "fdd"])),
    (["realleistungsfaktor"], ("power_factor", "Power factor", "", "high", "electrical-meter", "power_factor", "", False, ["energy", "fdd"])),

    # ── Timers / schedules ────────────────────────────────────────────────────
    (["timerruecklauf"],        ("timer_schedule", "Return flow timer schedule", "", "medium", "hvac-timer",      "return_flow_timer",  "bool", False, ["hvac", "mpc"])),
    (["greal_administrator_ht"],("control_param",  "Administrator high-tariff state","","medium","energy-manager","high_tariff_state", "bool", False, ["energy", "mpc"])),
]
