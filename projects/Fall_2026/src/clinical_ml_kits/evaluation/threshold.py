"""Decision-threshold rules. Selected on validation data, then reused unchanged on test."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
from sklearn.metrics import precision_recall_curve, roc_curve

FIXED = re.compile(r"^fixed\(([0-9]*\.?[0-9]+)\)$")


def select_threshold(y: Any, proba: Any, rule: str) -> float:
    m = FIXED.match(rule)
    if m:
        return float(m.group(1))
    y, proba = np.asarray(y), np.asarray(proba)
    if rule == "youden":
        fpr, tpr, thr = roc_curve(y, proba)
        j = tpr - fpr
        i = int(np.argmax(j[1:])) + 1  # skip the +inf sentinel threshold
        return float(thr[i])
    if rule == "max_f1":
        prec, rec, thr = precision_recall_curve(y, proba)
        f1 = np.where(
            prec[:-1] + rec[:-1] > 0, 2 * prec[:-1] * rec[:-1] / (prec[:-1] + rec[:-1]), 0
        )
        return float(thr[int(np.argmax(f1))])
    raise ValueError(f"unknown threshold rule {rule!r}; use youden, max_f1, or fixed(<value>)")
