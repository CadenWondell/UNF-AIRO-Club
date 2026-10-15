"""Adapter registry: the only module outside ``adapters/<name>/`` that imports adapters."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

_ADAPTERS: dict[str, str] = {
    "synthetic_clinical": (
        "clinical_ml_kits.adapters.synthetic_clinical.adapter:SyntheticClinicalAdapter"
    ),
    "all_of_us": "clinical_ml_kits.adapters.all_of_us.adapter:AllOfUsAdapter",
}


def available_adapters() -> list[str]:
    return sorted(_ADAPTERS)


def adapter_class(name: str) -> Any:
    try:
        target = _ADAPTERS[name]
    except KeyError:
        raise KeyError(f"no adapter registered for dataset {name!r}") from None
    module, _, cls = target.partition(":")
    return getattr(importlib.import_module(module), cls)


def get_adapter(name: str, **kwargs: Any) -> Any:
    """Construct a registered adapter (``synthetic_clinical`` or ``all_of_us``)."""
    return adapter_class(name).create(**kwargs)


def validate_population_params(path: Path) -> Any:
    """Validate a synthetic population params file with the synthetic adapter's schema."""
    from clinical_ml_kits.adapters.synthetic_clinical.params import load_params

    return load_params(Path(path))
