"""
zoro_eda.config
===============
Load project configuration from config.yaml.

Usage
-----
    from zoro_eda.config import load_config

    cfg = load_config()              # reads config.yaml in project root
    cfg = load_config("/path/to/config.yaml")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default values used when config.yaml is absent or a key is missing.
# Mirrors the structure in config.yaml so scripts work without PyYAML.
_DEFAULTS: dict[str, Any] = {
    "paths": {
        "project_root": str(Path(__file__).resolve().parents[2]),
        "raw_data":     "data",
        "reports":      "reports",
        "plots":        "reports/plots",
        "samples":      "reports/sample_rows",
        "context":      "context",
        "notebooks":    "notebooks",
        "scripts":      "scripts",
        "processed":    "data/processed",
        "data_samples": "data/samples",
    },
    "sampling": {
        "head_rows":    30,
        "head_bytes":   6144,
        "tail_bytes":   4096,
        "sample_rows":  20,
        "plot_max_rows": 5000,
    },
    "data": {
        "delimiter":       ";",
        "encoding":        "utf-8",
        "timestamp_col":   "_time",
        "value_col":       "_value",
        "field_col":       "_field",
        "measurement_col": "_measurement",
        "timestamp_tz":    "UTC",
        "local_tz":        "Europe/Berlin",
    },
    "pipeline": {
        "required_fields":    ["timestamp", "device_id", "metric", "value", "unit"],
        "building_id_prefix": "de-enfa-main-01",
    },
    "exclude_signals": [
        "A", "_value", "pilot", "val1006", "val1007", "val1008", "val1009",
    ],
}


def _find_config_yaml(start: Path | None = None) -> Path | None:
    """Walk up from `start` (default: this file's location) to find config.yaml."""
    root = start or Path(__file__).resolve().parent
    for candidate in [root, *root.parents]:
        cfg = candidate / "config.yaml"
        if cfg.exists():
            return cfg
        if (candidate / ".git").exists():
            break  # stop at repo root
    return None


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """
    Load config.yaml and return merged configuration dict.

    Falls back to built-in defaults if PyYAML is not installed or the file
    is not found — so scripts always have sensible values.

    Parameters
    ----------
    config_path:
        Explicit path to config.yaml. If None, auto-discovers by walking up
        from the package directory.
    """
    import copy
    cfg = copy.deepcopy(_DEFAULTS)

    if config_path is not None:
        yaml_path = Path(config_path)
    else:
        yaml_path = _find_config_yaml()

    if yaml_path is None or not yaml_path.exists():
        logger.debug("config.yaml not found — using built-in defaults")
        return cfg

    try:
        import yaml  # type: ignore[import]
        with open(yaml_path, encoding="utf-8") as fh:
            user_cfg = yaml.safe_load(fh) or {}
        # Shallow merge per top-level section
        for section, values in user_cfg.items():
            if isinstance(values, dict) and section in cfg:
                cfg[section].update(values)
            else:
                cfg[section] = values
        logger.debug("Loaded config from %s", yaml_path)
    except ImportError:
        logger.debug("PyYAML not installed — using built-in defaults")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to parse %s: %s — using defaults", yaml_path, exc)

    return cfg
