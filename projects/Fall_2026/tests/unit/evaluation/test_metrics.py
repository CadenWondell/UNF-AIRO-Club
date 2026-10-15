"""T100: binary metrics and threshold rules on hand-computed toy arrays."""

from __future__ import annotations

import numpy as np
import pytest

from clinical_ml_kits.evaluation import evaluate_binary
from clinical_ml_kits.evaluation.threshold import select_threshold

Y = np.array([0, 0, 1, 1, 0, 1, 0, 1])
P = np.array([0.1, 0.4, 0.35, 0.8, 0.2, 0.7, 0.6, 0.9])


def test_hand_computed_metrics_fixed_threshold() -> None:
    r = evaluate_binary(Y, P, threshold_rule="fixed(0.5)")
    m = r.metrics
    assert m["auroc"] == pytest.approx(14 / 16)
    assert m["auprc"] == pytest.approx(0.25 * (1 + 1 + 1 + 4 / 6))
    assert r.prevalence == pytest.approx(0.5) and m["prevalence"] == pytest.approx(0.5)
    for k in ("sensitivity", "specificity", "precision", "recall", "f1"):
        assert m[k] == pytest.approx(0.75), k
    assert r.confusion == {"tn": 3, "fp": 1, "fn": 1, "tp": 3}
    assert m["brier"] == pytest.approx(1.1325 / 8)


def test_youden_and_max_f1_chosen_on_given_data() -> None:
    assert select_threshold(Y, P, "youden") == pytest.approx(0.7)
    assert select_threshold(Y, P, "max_f1") == pytest.approx(0.7)
    assert select_threshold(Y, P, "fixed(0.25)") == pytest.approx(0.25)
    with pytest.raises(ValueError):
        select_threshold(Y, P, "magic")


def test_threshold_reused_unchanged() -> None:
    val = evaluate_binary(Y, P, threshold_rule="youden")
    other_y, other_p = Y[::-1], P
    test = evaluate_binary(other_y, other_p, threshold=val.threshold)
    assert test.threshold == val.threshold and test.threshold_rule == "reused"


def test_table() -> None:
    t = evaluate_binary(Y, P, threshold_rule="youden").table()
    assert {"auroc", "auprc", "prevalence", "sensitivity", "threshold"} <= set(t.index)
