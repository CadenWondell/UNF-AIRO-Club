"""Grouped out-of-fold calibration (V-14 selected pattern, research R-26).

The calibrator is fitted on out-of-fold training predictions from a patient-grouped splitter;
validation and test data are never used. Never falls back to ungrouped folds.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict

_EPS = 1e-6


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, _EPS, 1 - _EPS)
    return np.asarray(np.log(p / (1 - p))).reshape(-1, 1)


class GroupedCalibratedModel(ClassifierMixin, BaseEstimator):  # type: ignore[misc]
    def __init__(self, model: Any, calibrator: Any, method: str) -> None:
        self.model = model
        self.calibrator = calibrator
        self.method = method
        self.classes_ = np.array([0, 1])

    def _cal(self, p: np.ndarray) -> np.ndarray:
        if self.method == "sigmoid":
            return np.asarray(self.calibrator.predict_proba(_logit(p))[:, 1])
        return np.asarray(self.calibrator.predict(p))

    def predict_proba(self, X: Any) -> np.ndarray:
        p = self._cal(self.model.predict_proba(X)[:, 1])
        return np.column_stack([1 - p, p])

    def predict(self, X: Any) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


def calibrate_grouped(
    estimator: Any, X: Any, y: Any, groups: Any, *, cv: Any, method: str = "sigmoid"
) -> GroupedCalibratedModel:
    if groups is None:
        raise ValueError("grouped calibration requires patient groups (groups=...)")
    if method not in ("sigmoid", "isotonic"):
        raise ValueError("method must be 'sigmoid' or 'isotonic'")
    oof = cross_val_predict(clone(estimator), X, y, groups=groups, cv=cv, method="predict_proba")[
        :, 1
    ]
    yv = np.asarray(y)
    if method == "sigmoid":
        calibrator: Any = LogisticRegression(C=1e6).fit(_logit(oof), yv)
    else:
        calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(oof, yv)
    final = clone(estimator).fit(X, y)
    return GroupedCalibratedModel(final, calibrator, method)
