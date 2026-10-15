"""Adapter registry: the only module outside ``adapters/<name>/`` that imports adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def validate_population_params(path: Path) -> Any:
    """Validate a synthetic population params file with the synthetic adapter's schema."""
    from clinical_ml_kits.adapters.synthetic_clinical.params import load_params

    return load_params(Path(path))
