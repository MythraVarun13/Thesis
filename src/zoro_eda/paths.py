"""
zoro_eda.paths
==============
Centralised path resolution for the EnFa EDA project.

Usage
-----
    from zoro_eda.paths import resolve_paths

    paths = resolve_paths()          # auto-detect project root
    paths = resolve_paths(raw_dir=Path("C:/Users/.../ZE/data"))

    # Access paths
    paths.raw_data    # Path to raw CSV files (read-only)
    paths.reports     # Path to reports directory
    paths.plots       # Path to plots subdirectory
    paths.context     # Path to context markdown files
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProjectPaths:
    """Immutable set of project-relative paths.

    All paths are absolute ``Path`` objects. Pass this object between
    functions instead of reconstructing ``project_root / "reports"`` etc.
    in every script.
    """

    root:        Path   # project root (contains config.yaml, README.md)
    raw_data:    Path   # data/ — READ ONLY
    reports:     Path   # reports/
    plots:       Path   # reports/plots/
    sample_rows: Path   # reports/sample_rows/
    context:     Path   # context/
    notebooks:   Path   # notebooks/
    scripts:     Path   # scripts/
    processed:   Path   # data/processed/
    data_samples: Path  # data/samples/

    def ensure_output_dirs(self) -> None:
        """Create output directories that may not yet exist (skips raw_data)."""
        for directory in (
            self.reports,
            self.plots,
            self.sample_rows,
            self.context,
            self.notebooks,
            self.processed,
            self.data_samples,
        ):
            directory.mkdir(parents=True, exist_ok=True)


def _detect_project_root() -> Path:
    """Auto-detect project root by walking up from cwd until config.yaml found."""
    # 1. Explicit env var
    env_root = os.environ.get("ZORO_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()

    # 2. Walk up from cwd
    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "config.yaml").exists() and (candidate / "CLAUDE.md").exists():
            return candidate
        if (candidate / ".git").exists():
            return candidate

    # 3. Fallback: use parent of this file (src/zoro_eda → src → project root)
    return Path(__file__).resolve().parents[2]


def resolve_paths(
    raw_dir: Path | None = None,
    project_root: Path | None = None,
    cfg: dict[str, Any] | None = None,
) -> ProjectPaths:
    """Build a ``ProjectPaths`` from explicit inputs or auto-detection.

    Priority order for project root:
    1. ``project_root`` argument
    2. ``raw_dir.parent`` (if raw_dir provided)
    3. ``ZORO_PROJECT_ROOT`` environment variable
    4. Walk up from cwd looking for config.yaml
    5. Walk up from this file's location

    Parameters
    ----------
    raw_dir:
        Path to the raw data directory.  If given, ``project_root`` is
        inferred as its parent unless also explicitly supplied.
    project_root:
        Explicit project root path.
    cfg:
        Parsed config dict from ``load_config()``.  If provided, relative
        sub-paths from the ``paths`` section override defaults.
    """
    if project_root is not None:
        root = Path(project_root).resolve()
    elif raw_dir is not None:
        root = Path(raw_dir).resolve().parent
    else:
        root = _detect_project_root()

    # Sub-paths: prefer cfg values, fall back to hard-coded defaults
    def _sub(key: str, default: str) -> Path:
        if cfg and "paths" in cfg:
            return root / cfg["paths"].get(key, default)
        return root / default

    raw = Path(raw_dir).resolve() if raw_dir is not None else root / "data"

    return ProjectPaths(
        root=root,
        raw_data=raw,
        reports=_sub("reports", "reports"),
        plots=_sub("plots", "reports/plots"),
        sample_rows=_sub("samples", "reports/sample_rows"),
        context=_sub("context", "context"),
        notebooks=_sub("notebooks", "notebooks"),
        scripts=_sub("scripts", "scripts"),
        processed=_sub("processed", "data/processed"),
        data_samples=_sub("data_samples", "data/samples"),
    )
