"""T120: same RunManifest inputs → identical coefficients, thresholds, and metrics (SC-006)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from clinical_ml_kits import load_kit
from clinical_ml_kits.evaluation import evaluate_binary
from clinical_ml_kits.preprocessing import make_preprocessor

TOY = Path(__file__).resolve().parents[1] / "fixtures" / "kits" / "toy_binary"


def run() -> dict:
    kit = load_kit(TOY)
    data = kit.load()
    p = kit.definition.baseline.params
    lr = Pipeline(
        [
            ("preprocess", make_preprocessor(kit.feature_spec)),
            (
                "model",
                LogisticRegression(C=p.C, penalty=p.penalty, max_iter=p.max_iter, solver=p.solver),
            ),
        ]
    ).fit(data.train.X, data.train.y)
    rf = Pipeline(
        [
            ("preprocess", make_preprocessor(kit.feature_spec)),
            ("model", RandomForestClassifier(n_estimators=50, random_state=kit.definition.seed)),
        ]
    ).fit(data.train.X, data.train.y)
    res = evaluate_binary(
        data.validation.y, lr.predict_proba(data.validation.X)[:, 1], kit.definition.threshold_rule
    )
    return {
        "manifest": data.run_manifest.model_copy(update={"test_access_log": []}).content_hash(),
        "X": data.train.X,
        "coef": lr.named_steps["model"].coef_,
        "threshold": res.threshold,
        "metrics": res.metrics,
        "rf": rf.predict_proba(data.validation.X)[:, 1],
    }


def test_two_runs_identical() -> None:
    a, b = run(), run()
    assert a["manifest"] == b["manifest"]
    pd.testing.assert_frame_equal(a["X"], b["X"])
    np.testing.assert_array_equal(a["coef"], b["coef"])
    assert a["threshold"] == b["threshold"] and a["metrics"] == b["metrics"]
    np.testing.assert_array_equal(a["rf"], b["rf"])
