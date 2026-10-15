"""T104: coefficient table, permutation importance, per-row contributions."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from clinical_ml_kits.evaluation.explain import (
    coefficient_table,
    contributions,
    permutation_importance_table,
)
from clinical_ml_kits.preprocessing import make_preprocessor


def _fit(kit, data):  # type: ignore[no-untyped-def]
    return Pipeline(
        [
            ("preprocess", make_preprocessor(kit.feature_spec)),
            ("model", LogisticRegression(max_iter=1000)),
        ]
    ).fit(data.train.X, data.train.y)


def test_coefficients_mapped_to_names(toy_kit, toy_data) -> None:  # type: ignore[no-untyped-def]
    m = _fit(toy_kit, toy_data)
    t = coefficient_table(m)
    names = list(m.named_steps["preprocess"].get_feature_names_out())
    assert sorted(t.feature) == sorted(names)
    assert any(f.startswith("missingindicator_") for f in t.feature)
    assert t.abs_coefficient.is_monotonic_decreasing


def test_permutation_importance_on_validation(toy_kit, toy_data) -> None:  # type: ignore[no-untyped-def]
    m = _fit(toy_kit, toy_data)
    t = permutation_importance_table(m, toy_data.validation.X, toy_data.validation.y, seed=0)
    assert sorted(t.feature) == sorted(toy_data.validation.X.columns)
    assert {"importance_mean", "importance_std"} <= set(t.columns)


def test_contributions_sum_to_logit_minus_intercept(toy_kit, toy_data) -> None:  # type: ignore[no-untyped-def]
    m = _fit(toy_kit, toy_data)
    X = toy_data.validation.X.head(20)
    c = contributions(m, X)
    p = m.predict_proba(X)[:, 1]
    logit = np.log(p / (1 - p))
    np.testing.assert_allclose(
        c.sum(axis=1).to_numpy(), logit - m.named_steps["model"].intercept_[0], atol=1e-8
    )
