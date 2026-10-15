"""Framework logging: one logger namespace and structured event helpers."""

from __future__ import annotations

import logging as _logging
from datetime import datetime, timezone
from typing import Any

ROOT = "clinical_ml_kits"


def get_logger(name: str | None = None) -> _logging.Logger:
    """Return the framework logger, or a child logger ``clinical_ml_kits.<name>``."""
    return _logging.getLogger(f"{ROOT}.{name}" if name else ROOT)


def _emit(
    event: str, level: int, message: str, *, kit_id: str, environment: str, **extra: Any
) -> None:
    payload = {
        "ckit_event": event,
        "kit_id": kit_id,
        "environment": environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
    get_logger("events").log(level, message, extra=payload)


def log_final_test_access(*, kit_id: str, environment: str, **extra: Any) -> None:
    _emit(
        "final_test_access",
        _logging.INFO,
        "Held-out test partition accessed",
        kit_id=kit_id,
        environment=environment,
        **extra,
    )


def log_environment_selected(*, kit_id: str, environment: str, **extra: Any) -> None:
    _emit(
        "environment_selected",
        _logging.INFO,
        f"Data environment selected: {environment}",
        kit_id=kit_id,
        environment=environment,
        **extra,
    )


def log_model_completed(*, kit_id: str, environment: str, **extra: Any) -> None:
    _emit(
        "model_completed",
        _logging.INFO,
        "Model completed",
        kit_id=kit_id,
        environment=environment,
        **extra,
    )


def log_validation_failed(*, kit_id: str, environment: str, **extra: Any) -> None:
    _emit(
        "validation_failed",
        _logging.WARNING,
        "Validation failed",
        kit_id=kit_id,
        environment=environment,
        **extra,
    )
