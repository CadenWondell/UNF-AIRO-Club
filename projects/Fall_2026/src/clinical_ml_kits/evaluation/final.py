"""Single, logged evaluation on the held-out test partition (research R-11)."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from clinical_ml_kits.evaluation.calibration import CalibrationSummary, calibration_summary
from clinical_ml_kits.evaluation.metrics import BinaryResults, evaluate_binary
from clinical_ml_kits.leakage.checks import check_preprocessing_fit
from clinical_ml_kits.splitting.guard import release_test


@dataclass
class FinalReport:
    threshold: float
    validation: BinaryResults
    test: BinaryResults
    test_calibration: CalibrationSummary
    test_ci: dict[str, tuple[float, float]] = field(default_factory=dict)

    def table(self) -> Any:
        import pandas as pd

        return pd.DataFrame({"validation": self.validation.table(), "test": self.test.table()})


def _bootstrap_ci(y: np.ndarray, p: np.ndarray, seed: int, n_boot: int = 200) -> dict[str, Any]:
    from sklearn.metrics import average_precision_score, roc_auc_score

    rng = np.random.default_rng(seed)
    stats: dict[str, list[float]] = {"auroc": [], "auprc": []}
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i].tolist())) < 2:
            continue
        stats["auroc"].append(float(roc_auc_score(y[i], p[i])))
        stats["auprc"].append(float(average_precision_score(y[i], p[i])))
    return {
        k: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))
        for k, v in stats.items()
        if v
    }


def run_final_evaluation(
    model: Any, data: Any, threshold_rule: str, metrics: Any, seed: int
) -> FinalReport:
    if hasattr(model, "steps"):
        check_preprocessing_fit(model, n_train=len(data.train.X))
    else:
        warnings.warn(
            "final_evaluation received a model that is not a scikit-learn Pipeline: the "
            "preprocessing-isolation check cannot verify that preprocessing was fitted on the "
            "training partition only",
            UserWarning,
            stacklevel=3,
        )
    val_p = model.predict_proba(data.validation.X)[:, 1]
    val = evaluate_binary(data.validation.y, val_p, threshold_rule, metrics=metrics)
    test = release_test(data)
    if data.run_manifest is not None:
        data.run_manifest.record_test_access()
    p = np.asarray(model.predict_proba(test.X)[:, 1])
    y = np.asarray(test.y)
    res = evaluate_binary(y, p, threshold=val.threshold, metrics=metrics)
    return FinalReport(
        val.threshold, val, res, calibration_summary(y, p), _bootstrap_ci(y, p, seed)
    )
