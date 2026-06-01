"""
tests/test_match_signal.py
==========================
Unit tests for signal classification using known EnFa signal stems.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from zoro_eda.classify import classify_signal


def test_direct_battery_soc():
    result = classify_signal("greal_BatterieLadeZustand.csv")
    assert result.category == "battery_soc"
    assert result.zoro_metric == "battery_soc"
    assert result.zoro_unit == "%"
    assert result.exclude is False
    assert result.use_battery is True
    assert result.use_mpc is True


def test_direct_hp_supply_temp():
    """Umlaut variant — must be in DIRECT_MAP."""
    result = classify_signal("grealIstWaermepumpVorlauf.csv")
    assert result.category == "hp_supply_temp"
    assert result.zoro_unit == "C"
    assert result.confidence == "high"
    assert result.use_heatpump is True
    assert result.use_fdd is True


def test_direct_pv_string_1():
    result = classify_signal("greal_E_PV1.csv")
    assert result.category == "pv_energy"
    assert "pv-string-1" in result.zoro_device_id_suffix
    assert result.use_pv is True


def test_direct_val1006_excluded():
    result = classify_signal("val1006.csv")
    assert result.exclude is True
    assert result.category == "EXCLUDE"


def test_direct_val1008_excluded():
    result = classify_signal("val1008.csv")
    assert result.exclude is True


def test_direct_pilot_excluded():
    result = classify_signal("pilot.csv")
    assert result.exclude is True


def test_direct_a_excluded():
    result = classify_signal("A.csv")
    assert result.exclude is True


def test_pattern_wind_now():
    result = classify_signal("wind_now.csv")
    assert result.category == "weather"
    assert result.zoro_metric == "wind_speed_now"
    assert result.use_weather is True


def test_pattern_battery_net_power():
    result = classify_signal("real_BatterieLeistung.csv")
    assert result.category == "battery_power"
    assert result.zoro_metric == "battery_power_net"
    assert result.use_fdd is True
    assert result.use_mpc is True


def test_pattern_hp_defrost_wp1():
    result = classify_signal("greal_WP1AbtauSek.csv")
    assert result.category == "hp_defrost"
    assert result.zoro_unit == "s"
    assert result.use_fdd is True


def test_pattern_building_power():
    result = classify_signal("greal_LeistungGebaeude.csv")
    assert result.category == "building_power"
    assert result.zoro_metric == "electrical_power_demand"


def test_pattern_outdoor_temp():
    result = classify_signal("grealTempAussenGefiltert.csv")
    assert result.category == "outdoor_temp"
    assert result.zoro_unit == "C"
    assert result.use_weather is True
    assert result.use_heatpump is True


def test_unknown_signal_returns_unknown():
    result = classify_signal("definitely_not_a_real_signal_xyz123.csv")
    assert result.category == "unknown"
    assert result.confidence == "low"
    assert result.exclude is False
    assert result.zoro_metric == ""


def test_excluded_signal_not_pipeline_ready():
    result = classify_signal("pilot.csv")
    assert result.exclude is True
    assert result.zoro_metric == ""


def test_pipeline_ready_has_all_json_v1_fields():
    result = classify_signal("greal_BatterieLadeZustand.csv")
    assert result.zoro_device_id_suffix != ""
    assert result.zoro_metric != ""
    assert result.zoro_unit != ""
