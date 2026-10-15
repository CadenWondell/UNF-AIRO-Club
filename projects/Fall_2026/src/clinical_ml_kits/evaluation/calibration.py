"""Calibration assessment relative to the sampled development prevalence (R-25)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

_EPS = 1e-6


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, _EPS, 1 - _EPS)
    return np.asarray(np.log(p / (1 - p)))


def reliability_bins(
    y: Any, proba: Any, bins: int = 10, strategy: str = "quantile"
) -> pd.DataFrame:
    yv, pv = np.asarray(y).astype(int), np.asarray(proba, dtype=float)
    if strategy == "quantile":
        order = np.argsort(pv, kind="stable")
        idx = np.empty(len(pv), dtype=int)
        idx[order] = np.floor(np.arange(len(pv)) * bins / len(pv)).astype(int)
    elif strategy == "uniform":
        idx = np.minimum((pv * bins).astype(int), bins - 1)
    else:
        raise ValueError("strategy must be quantile or uniform")
    df = pd.DataFrame({"bin": idx, "y": yv, "p": pv})
    g = df.groupby("bin")
    out = pd.DataFrame({"n": g.size(), "mean_predicted": g.p.mean(), "observed_rate": g.y.mean()})
    return out.reindex(range(bins)).fillna({"n": 0}).astype({"n": int}).reset_index()


@dataclass(frozen=True)
class CalibrationSummary:
    brier: float
    intercept: float  # calibration-in-the-large (logistic intercept with logit(p) offset)
    slope: float  # logistic slope on logit(p)
    n: int
    prevalence: float

    def describe(self) -> str:
        return (
            f"Brier score {self.brier:.4f}; calibration intercept {self.intercept:+.3f} "
            f"(ideal 0); slope {self.slope:.3f} (ideal 1); n={self.n}, sampled prevalence "
            f"{self.prevalence:.3f}. Probabilities are calibrated against the development sample "
            "(the kit's sampled case/control mix), not the population: this is not a clinical "
            "risk score."
        )


def calibration_summary(y: Any, proba: Any) -> CalibrationSummary:
    yv, pv = np.asarray(y).astype(int), np.asarray(proba, dtype=float)
    lp = _logit(pv).reshape(-1, 1)
    slope_model = LogisticRegression(C=1e9, max_iter=1000).fit(lp, yv)
    # intercept with logit(p) as a fixed offset: Newton iterations on one parameter
    a = 0.0
    off = lp.ravel()
    for _ in range(50):
        mu = 1 / (1 + np.exp(-(a + off)))
        grad, hess = float(np.sum(yv - mu)), float(np.sum(mu * (1 - mu)))
        step = grad / hess if hess else 0.0
        a += step
        if abs(step) < 1e-10:
            break
    return CalibrationSummary(
        brier=float(np.mean((pv - yv) ** 2)),
        intercept=float(a),
        slope=float(slope_model.coef_[0, 0]),
        n=len(yv),
        prevalence=float(yv.mean()),
    )
