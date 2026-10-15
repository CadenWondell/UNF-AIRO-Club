"""Clinical ML Kit Framework: leakage-safe clinical ML project kits for education."""

from __future__ import annotations

from typing import Any

__version__ = "0.1.0"
__all__ = ["__version__", "load_kit"]


def load_kit(*args: Any, **kwargs: Any) -> Any:
    """Load a kit (see :func:`clinical_ml_kits.core.kit.load_kit`)."""
    from clinical_ml_kits.core.kit import load_kit as _load_kit

    return _load_kit(*args, **kwargs)
