"""Execution-environment detection. All of Us Workbench detection fails closed until V-10."""

from __future__ import annotations

import importlib.util
import os
import platform
import sys
from pathlib import Path
from typing import Any

import yaml

V10_SOURCE_ID = "aou_workbench_access"


def is_colab() -> bool:
    if "google.colab" in sys.modules:
        return True
    try:
        return importlib.util.find_spec("google.colab") is not None
    except ModuleNotFoundError:  # no "google" namespace package at all
        return False


def workbench_markers(definitions_dir: Path) -> list[str] | None:
    """Environment variables that identify the Workbench, from the verified V-10 record only."""
    from clinical_ml_kits.provenance.models import SourceRecord

    p = Path(definitions_dir) / "sources" / f"{V10_SOURCE_ID}.yaml"
    if not p.is_file():
        return None
    rec = SourceRecord.model_validate(yaml.safe_load(p.read_text()))
    if rec.verification_status != "verified" or not rec.parameters:
        return None
    markers = rec.parameters.get("required_env_vars") or []
    if not isinstance(markers, list):
        return None
    return [str(m) for m in markers] or None


def is_all_of_us_workbench(definitions_dir: Path) -> bool:
    """True only when V-10 is verified and every verified marker is present. Otherwise False."""
    markers = workbench_markers(definitions_dir)
    return bool(markers) and all(os.environ.get(m) for m in markers or [])


def describe_environment(definitions_dir: Path) -> dict[str, Any]:
    from clinical_ml_kits.core.run_manifest import library_versions

    markers = workbench_markers(definitions_dir)
    return {
        "python": platform.python_version(),
        "colab": is_colab(),
        "all_of_us_workbench": is_all_of_us_workbench(definitions_dir),
        "workbench_detection": "verified markers" if markers else "unavailable (V-10 pending)",
        "libraries": library_versions(),
    }
