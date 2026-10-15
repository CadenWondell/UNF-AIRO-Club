"""Explainability with scikit-learn only: coefficients, permutation importance, contributions."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance


def _split(model: Any) -> tuple[Any, Any]:
    steps = getattr(model, "steps", None)
    if not steps:
        raise TypeError("expected a fitted Pipeline ending in a linear model")
    from sklearn.pipeline import Pipeline

    return Pipeline(steps[:-1]), steps[-1][1]


def coefficient_table(model: Any) -> pd.DataFrame:
    """Standardized coefficients (inputs are scaled) mapped to transformed feature names."""
    pre, est = _split(model)
    names = pre.get_feature_names_out()
    coef = np.asarray(est.coef_).ravel()
    t = pd.DataFrame({"feature": names, "coefficient": coef, "abs_coefficient": np.abs(coef)})
    return t.sort_values("abs_coefficient", ascending=False, kind="stable").reset_index(drop=True)


def permutation_importance_table(
    model: Any,
    X: pd.DataFrame,
    y: Any,
    *,
    scoring: str = "average_precision",
    n_repeats: int = 10,
    seed: int = 0,
) -> pd.DataFrame:
    """Permutation importance on held-in validation data (never the test partition)."""
    r = permutation_importance(model, X, y, scoring=scoring, n_repeats=n_repeats, random_state=seed)
    t = pd.DataFrame(
        {
            "feature": list(X.columns),
            "importance_mean": r.importances_mean,
            "importance_std": r.importances_std,
        }
    )
    return t.sort_values("importance_mean", ascending=False, kind="stable").reset_index(drop=True)


def contributions(model: Any, X: pd.DataFrame) -> pd.DataFrame:
    """Per-row signed contributions (coefficient × transformed value); rows sum to logit − b."""
    pre, est = _split(model)
    Z = pre.transform(X)
    Z = Z.toarray() if hasattr(Z, "toarray") else np.asarray(Z, dtype=float)
    c = Z * np.asarray(est.coef_).ravel()
    return pd.DataFrame(c, columns=pre.get_feature_names_out(), index=X.index)
