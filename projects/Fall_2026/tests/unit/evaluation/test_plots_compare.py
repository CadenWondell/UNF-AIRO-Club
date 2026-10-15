"""T106: plots return Figures on Agg; compare_models returns one row per model."""

from __future__ import annotations

import matplotlib
from matplotlib.figure import Figure
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from clinical_ml_kits.evaluation import compare_models, plot_calibration, plot_roc_pr
from clinical_ml_kits.preprocessing import make_preprocessor


def test_plots_and_compare(toy_kit, toy_data) -> None:  # type: ignore[no-untyped-def]
    assert matplotlib.get_backend().lower() == "agg"
    pre = make_preprocessor(toy_kit.feature_spec)
    lr = Pipeline([("p", pre), ("m", LogisticRegression(max_iter=1000))]).fit(
        toy_data.train.X, toy_data.train.y
    )
    rf = Pipeline(
        [
            ("p", make_preprocessor(toy_kit.feature_spec)),
            ("m", RandomForestClassifier(n_estimators=50, random_state=0)),
        ]
    ).fit(toy_data.train.X, toy_data.train.y)
    v = toy_data.validation
    p = lr.predict_proba(v.X)[:, 1]
    assert isinstance(plot_roc_pr(v.y, p), Figure)
    assert isinstance(plot_roc_pr(v.y, {"lr": p, "rf": rf.predict_proba(v.X)[:, 1]}), Figure)
    assert isinstance(plot_calibration(v.y, p, bins=10, strategy="quantile"), Figure)
    t = compare_models({"baseline": lr, "forest": rf}, v, metrics=["auroc", "auprc", "brier"])
    assert list(t.index) == ["baseline", "forest"]
    assert {"auroc", "auprc", "brier", "threshold"} <= set(t.columns)
