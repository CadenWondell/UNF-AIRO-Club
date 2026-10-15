"""Model comparison on the validation partition."""

from __future__ import annotations

from typing import Any

import pandas as pd

from clinical_ml_kits.evaluation.metrics import evaluate_binary


def compare_models(
    models: dict[str, Any], dataset: Any, metrics: Any = None, threshold_rule: str = "youden"
) -> pd.DataFrame:
    """One row per fitted model, evaluated on ``dataset`` (use validation, never test)."""
    rows = {}
    for name, m in models.items():
        r = evaluate_binary(
            dataset.y, m.predict_proba(dataset.X)[:, 1], threshold_rule, metrics=metrics
        )
        rows[name] = {**r.metrics, "threshold": r.threshold}
    return pd.DataFrame(rows).T
