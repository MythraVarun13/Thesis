"""
zoro_eda.config
===============
Load project configuration with a three-layer merge.

Priority order (highest wins):
  1. config_local.yaml  — machine-specific overrides, gitignored
  2. config.yaml        — shared project defaults, committed to git
  3. Built-in defaults  — hardcoded fallback, no files required

Usage
-----
    from zoro_eda.config import load_config

    cfg = load_config()              # auto-discovers config.yaml
    cfg = load_config("/path/to/config.yaml")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Built-in defaults — scripts work even without config.yaml or PyYAML
# ---------------------------------------------------------------------------
_DEFAULTS: dict[str, Any] = {
    "paths": {
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
        "head_rows":     30,
        "head_bytes":    6144,
        "tail_bytes":    4096,
        "sample_rows":   20,
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


# ---------------------------------------------------------------------------
# File finders
# ---------------------------------------------------------------------------

def _find_config_yaml(start: Path | None = None) -> Path | None:
    """Walk up from start to find config.yaml. Stops at .git boundary."""
    root = start or Path(__file__).resolve().parent
    for candidate in [root, *root.parents]:
        cfg = candidate / "config.yaml"
        if cfg.exists():
            return cfg
        if (candidate / ".git").exists():
            break
    return None


def _find_config_local(base_config: Path) -> Path | None:
    """Return config_local.yaml next to base_config if it exists."""
    local = base_config.parent / "config_local.yaml"
    return local if local.exists() else None


# ---------------------------------------------------------------------------
# YAML loader (graceful when PyYAML is absent)
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file. Returns {} if PyYAML is missing or file is invalid."""
    try:
        import yaml  # type: ignore[import]
        with open(path, encoding="utf-8") as fh:
            result = yaml.safe_load(fh)
        return result if isinstance(result, dict) else {}
    except ImportError:
        logger.debug("PyYAML not installed — cannot load %s", path)
    except Exception as exc:
        logger.warning("Failed to parse %s: %s", path, exc)
    return {}


# ---------------------------------------------------------------------------
# Merge helper
# ---------------------------------------------------------------------------

def _merge(base: dict, overrides: dict) -> None:
    """Shallow-merge overrides into base, section by section."""
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key].update(value)
        else:
            base[key] = value


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration and return the merged dict.

    Load order (highest priority wins):
      1. ``config_local.yaml`` next to config.yaml (gitignored, machine-specific)
      2. ``config.yaml`` (committed to git, shared defaults)
      3. Built-in defaults (always available, no files required)

    Parameters
    ----------
    config_path:
        Explicit path to config.yaml. If None, auto-discovers by walking up
        from the package directory.
    """
    import copy
    cfg = copy.deepcopy(_DEFAULTS)

    # Locate config.yaml
    if config_path is not None:
        yaml_path = Path(config_path)
    else:
        yaml_path = _find_config_yaml()

    if yaml_path is None or not yaml_path.exists():
        logger.debug("config.yaml not found — using built-in defaults")
        return cfg

    # Layer 1: config.yaml
    base_overrides = _load_yaml(yaml_path)
    if base_overrides:
        _merge(cfg, base_overrides)
        logger.debug("Loaded config.yaml from %s", yaml_path)

    # Layer 2: config_local.yaml (machine-specific, gitignored)
    local_path = _find_config_local(yaml_path)
    if local_path:
        local_overrides = _load_yaml(local_path)
        if local_overrides:
            _merge(cfg, local_overrides)
            logger.debug("Loaded config_local.yaml from %s", local_path)

    return cfg
