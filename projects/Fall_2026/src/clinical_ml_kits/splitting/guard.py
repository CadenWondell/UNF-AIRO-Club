"""Held-out test partition guard (research R-11).

Test rows and groups live in a module-private vault, not on ``KitData``; they are reachable only
through ``release_test`` (used by ``kit.final_evaluation``), which logs every access and warns on
repeats.
"""

from __future__ import annotations

import warnings
from datetime import datetime, timezone
from typing import Any

from clinical_ml_kits.core.logging import log_final_test_access

_VAULT: dict[str, Any] = {}


def deposit(token: str, test: Any) -> None:
    _VAULT[token] = test


def release_test(data: Any) -> Any:
    if data.run_log:
        warnings.warn(
            "the held-out test partition is being accessed again; test results must not drive "
            "model selection",
            UserWarning,
            stacklevel=2,
        )
    data.run_log.append(datetime.now(timezone.utc))
    log_final_test_access(
        kit_id=data.kit_id, environment=data.environment, access_number=len(data.run_log)
    )
    return _VAULT[data._token]
