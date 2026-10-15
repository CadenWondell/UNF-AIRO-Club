"""Binary evaluation: discrimination, imbalance-aware metrics, confusion matrix, Brier score."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from clinical_ml_kits.evaluation.threshold import select_threshold

ALL_METRICS = (
    "auroc",
    "auprc",
    "sensitivity",
    "specificity",
    "precision",
    "recall",
    "f1",
    "confusion_matrix",
    "brier",
)


@dataclass
class BinaryResults:
    threshold: float
    threshold_rule: str
    prevalence: float
    n: int
    metrics: dict[str, float] = field(default_factory=dict)
    confusion: dict[str, int] = field(default_factory=dict)

    def table(self) -> pd.Series:
        rows = {
            **self.metrics,
            "threshold": self.threshold,
            "n": float(self.n),
            **{f"cm_{k}": float(v) for k, v in self.confusion.items()},
        }
        return pd.Series(rows, name="value")

    def __repr__(self) -> str:
        shown = ", ".join(f"{k}={v:.3f}" for k, v in self.metrics.items())
        return f"BinaryResults(threshold={self.threshold:.3f} [{self.threshold_rule}], {shown})"


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else float("nan")


def evaluate_binary(
    y: Any,
    proba: Any,
    threshold_rule: str = "youden",
    *,
    threshold: float | None = None,
    metrics: Any = None,
) -> BinaryResults:
    """Evaluate probabilities. Pass ``threshold`` to reuse one chosen on validation data.

    AUPRC is reported together with the prevalence, its no-skill baseline.
    """
    yv, pv = np.asarray(y).astype(int), np.asarray(proba, dtype=float)
    if threshold is None:
        threshold, rule = select_threshold(yv, pv, threshold_rule), threshold_rule
    else:
        rule = "reused"
    pred = (pv >= threshold).astype(int)
    tp = int(((pred == 1) & (yv == 1)).sum())
    fp = int(((pred == 1) & (yv == 0)).sum())
    fn = int(((pred == 0) & (yv == 1)).sum())
    tn = int(((pred == 0) & (yv == 0)).sum())
    both = len(set(yv.tolist())) == 2
    sens, prec = _safe_div(tp, tp + fn), _safe_div(tp, tp + fp)
    vals = {
        "auroc": float(roc_auc_score(yv, pv)) if both else float("nan"),
        "auprc": float(average_precision_score(yv, pv)) if both else float("nan"),
        "prevalence": float(yv.mean()) if len(yv) else float("nan"),
        "sensitivity": sens,
        "specificity": _safe_div(tn, tn + fp),
        "precision": prec,
        "recall": sens,
        "f1": _safe_div(2 * prec * sens, prec + sens)
        if prec == prec and sens == sens
        else float("nan"),
        "brier": float(brier_score_loss(yv, pv)),
    }
    wanted = set(metrics or ALL_METRICS) | {"prevalence"}
    shown = {k: v for k, v in vals.items() if k in wanted}
    return BinaryResults(
        threshold=float(threshold),
        threshold_rule=rule,
        prevalence=vals["prevalence"],
        n=len(yv),
        metrics=shown,
        confusion={"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    )
