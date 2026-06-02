"""
09_create_grafana_dashboard.py
==============================
Build and register the EnFa Overview dashboard in Grafana via the HTTP API.

Creates a multi-panel dashboard with:
  1. HP COP daily trend  (3.5 years)
  2. WP1 / WP2 / WP3 defrost comparison (weekly sum)
  3. Energy balance monthly  (PV generation vs building demand)
  4. Battery SOC — all 4 clusters
  5. Outdoor temperature full time series
  6. Signal browser — dropdown lets you pick any of the 215 signals

Prerequisites
-------------
- Grafana running at localhost:3000 (admin / zoro)
- TimescaleDB populated by scripts/08_load_to_timescaledb.py
  (tenant_id = 'enfa-01', datapoints.pin = signal name)

Usage
-----
    python scripts/09_create_grafana_dashboard.py
    python scripts/09_create_grafana_dashboard.py --grafana-url http://localhost:3000

After running, open http://localhost:3000/dashboards and look for "EnFa Building Analysis".
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

TENANT_ID   = "enfa-01"
DS_UID      = "zoro-timescaledb"   # must match provisioning/datasources/timescaledb.yml uid

# ── SQL template helpers ───────────────────────────────────────────────────────

def _obs_query(pin: str, agg: str = "AVG(o.value)", bucket: str = "1 day") -> str:
    """Single-signal time-series query for Grafana time-series panels."""
    return (
        f"SELECT\n"
        f"  time_bucket('{bucket}', o.ts) AS time,\n"
        f"  {agg} AS value\n"
        f"FROM observations o\n"
        f"JOIN datapoints dp ON dp.hash = o.dp_hash\n"
        f"WHERE dp.tenant_id = '{TENANT_ID}'\n"
        f"  AND dp.pin = '{pin}'\n"
        f"  AND o.ts BETWEEN $__timeFrom() AND $__timeTo()\n"
        f"GROUP BY 1 ORDER BY 1"
    )


# ── Panel builders ─────────────────────────────────────────────────────────────

def _base_panel(panel_id: int, title: str, grid: dict) -> dict:
    return {
        "id":          panel_id,
        "title":       title,
        "type":        "timeseries",
        "gridPos":     grid,
        "datasource":  {"type": "postgres", "uid": DS_UID},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"lineWidth": 1.5, "fillOpacity": 8},
            },
            "overrides": [],
        },
        "options": {
            "legend":  {"displayMode": "list", "placement": "bottom"},
            "tooltip": {"mode": "multi"},
        },
    }


def panel_hp_cop(panel_id: int, grid: dict) -> dict:
    panel = _base_panel(panel_id, "Heat Pump COP — daily (heat output / electrical input)", grid)
    panel["description"] = (
        "COP = thermal energy produced / electrical energy consumed. "
        "Values < 1 indicate sensor issues or non-HP heating. Seasonal dip in deep winter is normal."
    )
    panel["targets"] = [
        {
            "datasource": {"type": "postgres", "uid": DS_UID},
            "rawSql": (
                "WITH daily AS (\n"
                "  SELECT\n"
                "    time_bucket('1 day', o.ts) AS day,\n"
                "    SUM(CASE WHEN dp.pin = 'greal_E__WMZ_WP'     THEN o.value ELSE 0 END) AS heat_kwh,\n"
                "    SUM(CASE WHEN dp.pin = 'greal_AZ_WP_Energie' THEN o.value ELSE 0 END) AS elec_kwh\n"
                "  FROM observations o\n"
                "  JOIN datapoints dp ON dp.hash = o.dp_hash\n"
                "  WHERE dp.tenant_id = 'enfa-01'\n"
                "    AND dp.pin IN ('greal_E__WMZ_WP', 'greal_AZ_WP_Energie')\n"
                "    AND o.ts BETWEEN $__timeFrom() AND $__timeTo()\n"
                "  GROUP BY 1\n"
                ")\n"
                "SELECT day AS time,\n"
                "       heat_kwh / NULLIF(elec_kwh, 0) AS \"HP COP (daily)\"\n"
                "FROM daily\n"
                "WHERE elec_kwh > 0\n"
                "ORDER BY 1"
            ),
            "format":  "time_series",
            "refId":   "A",
        }
    ]
    panel["fieldConfig"]["overrides"] = [
        {"matcher": {"id": "byName", "options": "HP COP (daily)"},
         "properties": [
             {"id": "unit",   "value": "none"},
             {"id": "min",    "value": 0},
             {"id": "max",    "value": 8},
             {"id": "thresholds", "value": {
                 "mode": "absolute",
                 "steps": [
                     {"color": "red",    "value": 0},
                     {"color": "yellow", "value": 2},
                     {"color": "green",  "value": 3},
                 ],
             }},
         ]},
    ]
    return panel


def panel_defrost(panel_id: int, grid: dict) -> dict:
    panel = _base_panel(panel_id, "Heat Pump Defrost Duration — weekly sum per unit (seconds)", grid)
    panel["description"] = "Total defrost time per week per heat pump. WP2 higher than WP1/WP3 suggests accelerated icing."
    targets = []
    for i, (sig, label) in enumerate([
        ("greal_WP1AbtauSek", "WP1"),
        ("greal_WP2AbtauSek", "WP2"),
        ("greal_WP3AbtauSek", "WP3"),
    ]):
        targets.append({
            "datasource": {"type": "postgres", "uid": DS_UID},
            "rawSql": _obs_query(sig, agg="SUM(o.value)", bucket="1 week"),
            "format": "time_series",
            "refId":  chr(65 + i),
            "legendFormat": label,
        })
    panel["targets"] = targets
    panel["fieldConfig"]["defaults"]["custom"]["lineWidth"] = 2
    return panel


def panel_energy_balance(panel_id: int, grid: dict) -> dict:
    panel = _base_panel(panel_id, "Monthly Energy Balance — PV + BHKW vs Building Demand (kWh delta)", grid)
    panel["type"] = "barchart"
    panel["description"] = "Monthly energy delta (MAX-MIN) per source. Positive self-sufficiency = PV+BHKW ≥ demand."
    targets = []
    signals = [
        ("greal_E_ErzeugungEnFa",   "PV Generation",     "A"),
        ("greal_E_bhkw1",           "BHKW Generation",   "B"),
        ("greal_E_Gesamtverbrauch", "Building Demand",    "C"),
    ]
    for sig, label, ref in signals:
        targets.append({
            "datasource": {"type": "postgres", "uid": DS_UID},
            "rawSql": (
                f"SELECT\n"
                f"  time_bucket('1 month', o.ts) AS time,\n"
                f"  GREATEST(MAX(o.value) - MIN(o.value), 0) AS \"{label}\"\n"
                f"FROM observations o\n"
                f"JOIN datapoints dp ON dp.hash = o.dp_hash\n"
                f"WHERE dp.tenant_id = '{TENANT_ID}'\n"
                f"  AND dp.pin = '{sig}'\n"
                f"  AND o.ts BETWEEN $__timeFrom() AND $__timeTo()\n"
                f"GROUP BY 1 ORDER BY 1"
            ),
            "format": "time_series",
            "refId":  ref,
        })
    panel["targets"] = targets
    panel["fieldConfig"]["defaults"]["unit"] = "kwatth"
    return panel


def panel_battery_soc(panel_id: int, grid: dict) -> dict:
    panel = _base_panel(panel_id, "Battery State of Charge — all clusters (%)", grid)
    panel["description"] = "SOC for all 4 battery clusters. Divergence between clusters indicates cell imbalance."
    targets = []
    for i, sig in enumerate([
        "greal_BatterieLadeZustand",
        "grealCluster_1_Ladung",
        "grealCluster_2_Ladung",
        "grealCluster_3_Ladung",
        "grealCluster_4_Ladung",
    ]):
        label = "Battery SOC" if "BatterieLade" in sig else f"Cluster {i}"
        targets.append({
            "datasource": {"type": "postgres", "uid": DS_UID},
            "rawSql": _obs_query(sig, agg="AVG(o.value)", bucket="1 hour"),
            "format": "time_series",
            "refId":  chr(65 + i),
            "legendFormat": label,
        })
    panel["targets"] = targets
    panel["fieldConfig"]["defaults"]["unit"] = "percent"
    panel["fieldConfig"]["defaults"]["min"]  = 0
    panel["fieldConfig"]["defaults"]["max"]  = 100
    return panel


def panel_outdoor_temp(panel_id: int, grid: dict) -> dict:
    panel = _base_panel(panel_id, "Outdoor Temperature (°C) — 3.5 year record", grid)
    panel["targets"] = [
        {
            "datasource": {"type": "postgres", "uid": DS_UID},
            "rawSql": _obs_query("greal_TempAussen", agg="AVG(o.value)", bucket="6 hours"),
            "format": "time_series",
            "refId":  "A",
            "legendFormat": "Outdoor temp (6h mean)",
        }
    ]
    panel["fieldConfig"]["defaults"]["unit"] = "celsius"
    return panel


def panel_signal_browser(panel_id: int, grid: dict) -> dict:
    panel = _base_panel(panel_id, "Signal Browser — select any EnFa signal", grid)
    panel["description"] = (
        "Use the $signal dropdown at the top of the dashboard to explore any of the 215 signals. "
        "Each data point is an hourly aggregated value stored in TimescaleDB."
    )
    panel["targets"] = [
        {
            "datasource": {"type": "postgres", "uid": DS_UID},
            "rawSql": (
                "SELECT\n"
                "  o.ts AS time,\n"
                "  o.value AS \"$signal\"\n"
                "FROM observations o\n"
                "JOIN datapoints dp ON dp.hash = o.dp_hash\n"
                "WHERE dp.tenant_id = 'enfa-01'\n"
                "  AND dp.pin = '$signal'\n"
                "  AND o.ts BETWEEN $__timeFrom() AND $__timeTo()\n"
                "ORDER BY 1"
            ),
            "format": "time_series",
            "refId":  "A",
        }
    ]
    return panel


# ── Dashboard assembler ────────────────────────────────────────────────────────

def build_dashboard() -> dict:
    """Assemble the full Grafana dashboard JSON."""
    panels = [
        panel_hp_cop(       1, {"x": 0,  "y": 0,  "w": 24, "h": 8}),
        panel_defrost(      2, {"x": 0,  "y": 8,  "w": 12, "h": 8}),
        panel_outdoor_temp( 3, {"x": 12, "y": 8,  "w": 12, "h": 8}),
        panel_energy_balance(4,{"x": 0,  "y": 16, "w": 12, "h": 8}),
        panel_battery_soc(  5, {"x": 12, "y": 16, "w": 12, "h": 8}),
        panel_signal_browser(6,{"x": 0,  "y": 24, "w": 24, "h": 8}),
    ]

    return {
        "uid":           "enfa-overview",
        "title":         "EnFa Building Analysis",
        "description":   "Heat pump COP, energy balance, battery, and full signal browser. Data: 2022-12 → 2026-05.",
        "tags":          ["enfa", "heat-pump", "battery", "energy"],
        "timezone":      "browser",
        "fiscalYearStartMonth": 0,
        "refresh":       "5m",
        "schemaVersion": 39,
        "time":          {"from": "2022-12-01T00:00:00Z", "to": "now"},
        "timepicker":    {},
        "panels":        panels,
        "templating": {
            "list": [
                {
                    "name":        "signal",
                    "label":       "Signal",
                    "type":        "query",
                    "datasource":  {"type": "postgres", "uid": DS_UID},
                    "query":       f"SELECT DISTINCT pin FROM datapoints WHERE tenant_id = '{TENANT_ID}' ORDER BY pin",
                    "refresh":     1,
                    "multi":       False,
                    "includeAll":  False,
                    "current":     {"text": "greal_BatterieLadeZustand", "value": "greal_BatterieLadeZustand"},
                    "sort":        1,
                }
            ]
        },
        "annotations": {
            "list": [
                {
                    "builtIn": 1, "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                    "enable": True, "hide": True, "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts", "type": "dashboard",
                }
            ]
        },
        "links": [],
        "version": 1,
    }


# ── Grafana API ────────────────────────────────────────────────────────────────

def push_dashboard(grafana_url: str, user: str, password: str, dash: dict) -> str:
    url  = f"{grafana_url.rstrip('/')}/api/dashboards/db"
    resp = requests.post(
        url,
        auth=(user, password),
        headers={"Content-Type": "application/json"},
        json={"dashboard": dash, "overwrite": True, "folderId": 0},
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    slug = result.get("url", "/dashboards")
    return f"{grafana_url.rstrip('/')}{slug}"


def also_save_json(dash: dict, out_path: Path) -> None:
    """Save the dashboard JSON to the provisioning folder (auto-loaded on restart)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(dash, fh, indent=2)
    logger.info("Dashboard JSON saved: %s", out_path)


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Create the EnFa Overview dashboard in Grafana.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--grafana-url", default="http://localhost:3000")
    p.add_argument("--user",        default="admin")
    p.add_argument("--password",    default="zoro")
    p.add_argument("--save-json",   action="store_true",
                   help="Also write JSON to grafana/provisioning/dashboards/enfa_overview.json")
    return p


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    args = build_arg_parser().parse_args()

    dash = build_dashboard()
    logger.info("Dashboard JSON built: %d panels", len(dash["panels"]))

    if args.save_json:
        # Resolve relative to this script's repo root
        _scripts_dir = Path(__file__).resolve().parent
        # Walk up to find ZoroEnergyPlatform sibling
        ze_root   = _scripts_dir.parent
        zep_root  = ze_root.parent / "ZoroEnergyPlatform"
        json_path = zep_root / "cloud" / "grafana" / "provisioning" / "dashboards" / "enfa_overview.json"
        also_save_json(dash, json_path)

    try:
        dashboard_url = push_dashboard(
            args.grafana_url, args.user, args.password, dash
        )
        print(f"\n{'='*60}")
        print(f"Dashboard created successfully!")
        print(f"URL: {dashboard_url}")
        print(f"\nDefault time range: Dec 2022 -> now (3.5 years of EnFa data)")
        print(f"Use the 'Signal' dropdown to browse all 215 signals.")
    except requests.exceptions.ConnectionError:
        logger.error(
            "Cannot connect to Grafana at %s\n"
            "Make sure the Docker stack is running:\n"
            "  docker compose -f cloud/docker-compose.cloud.yml up -d",
            args.grafana_url,
        )
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        logger.error("Grafana API error: %s\n%s", exc, exc.response.text)
        sys.exit(1)


if __name__ == "__main__":
    main()
