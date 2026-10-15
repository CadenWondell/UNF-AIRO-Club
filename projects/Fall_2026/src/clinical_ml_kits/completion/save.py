"""Policy-gated model serialization: joblib + JSON metadata sidecar (research R-14)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib

from clinical_ml_kits.core.errors import PolicyViolation


def save_model(
    model: Any, path: str | Path, policy: Any, *, portable: bool, metadata: dict[str, Any]
) -> Path:
    """Save inside the environment; ``portable=True`` only where the policy allows it."""
    p = Path(path)
    if portable and not policy.portable_artifacts:
        raise PolicyViolation(
            f"{policy.name}: portable model artifacts are not permitted. Research models trained "
            "here stay in this environment; complete the model with kit.complete(...) instead."
        )
    policy.check_write_path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, p)
    side = {
        **metadata,
        "portable": portable,
        "environment": policy.name,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "envelope_contract_version": "1.0.0",
        "demo_model": bool(portable and policy.name == "synthetic"),
    }
    p.with_suffix(".json").write_text(json.dumps(side, indent=2, sort_keys=True, default=str))
    return p
