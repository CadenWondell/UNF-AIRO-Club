"""Build prediction envelopes (contracts/prediction-envelope.md) from a fitted model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from clinical_ml_kits.prediction.envelope import (
    CONTRACT_VERSION,
    DISCLAIMER,
    PredictionEnvelope,
)


def model_name(model: Any) -> str:
    est = model.steps[-1][1] if hasattr(model, "steps") else model
    inner = getattr(est, "model", None)
    if inner is not None and hasattr(inner, "steps"):
        return model_name(inner) + "_calibrated"
    return type(est).__name__.lower()


def build_envelopes(
    *,
    model: Any,
    X: pd.DataFrame,
    subject_refs: list[str],
    as_of: pd.Series,
    threshold: float,
    kit: Any,
    calibration_status: str,
    run_manifest_hash: str,
    top_k: int = 3,
) -> list[PredictionEnvelope]:
    d, ph = kit.definition, kit.phenotype
    proba = np.asarray(model.predict_proba(X)[:, 1], dtype=float)
    md = kit.adapter.metadata()
    contrib = None
    if hasattr(model, "steps") and hasattr(model.steps[-1][1], "coef_"):
        from clinical_ml_kits.evaluation.explain import contributions

        contrib = contributions(model, X)
    created = datetime.now(timezone.utc)
    out = []
    for i, (ix, row) in enumerate(X.iterrows()):
        explanation = None
        if contrib is not None:
            c = contrib.loc[ix]
            top = c.reindex(c.abs().sort_values(ascending=False).index[:top_k])
            explanation = {
                "method": "linear_contribution (coefficient x standardized value)",
                "top_features": [
                    {"feature": str(k), "contribution": float(v)} for k, v in top.items()
                ],
            }
        p = float(proba[i])
        out.append(
            PredictionEnvelope.model_validate(
                {
                    "contract_version": CONTRACT_VERSION,
                    "kit_id": kit.kit_id,
                    "model_id": f"{kit.kit_id}.{model_name(model)}",
                    "model_version": d.kit_version,
                    "target": d.target.model_dump(),
                    "prediction_type": d.prediction_type,
                    "as_of": pd.Timestamp(as_of.iloc[i]).tz_localize("UTC").isoformat(),
                    "horizon": None,
                    "dataset": {"id": md.id, "version": md.version},
                    "definition_versions": {
                        "phenotype": ph.version,
                        "cohort": d.cohort.version,
                        "kit": d.kit_version,
                        "feature_registry": kit.ctx.registry.registry_version,
                    },
                    "data_environment": kit.environment,
                    "subject_ref": subject_refs[i],
                    "payload": {
                        "payload_type": "binary_probability",
                        "probability": p,
                        "threshold": float(threshold),
                        "predicted_class": int(p >= threshold),
                        "probability_basis": "development_sample",
                    },
                    "calibration_status": calibration_status,
                    "explanation": explanation,
                    "input_metadata": {
                        "features_present": int(row.notna().sum()),
                        "features_missing": [str(c) for c in row.index[row.isna()]],
                    },
                    "model_metadata": {
                        "template_family": d.template_family,
                        "trained_on_environment": kit.environment,
                        "run_manifest_hash": run_manifest_hash,
                        "created_at": created,
                    },
                    "disclaimer": DISCLAIMER,
                }
            )
        )
    return out
