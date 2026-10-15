"""Index-visit-bias check (ADR-002): can utilization features alone separate cases and controls?"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class VisitBiasReport:
    auroc: float
    bound: float
    features: list[str]

    @property
    def exceeded(self) -> bool:
        return self.auroc > self.bound

    def __str__(self) -> str:
        verdict = "EXCEEDS" if self.exceeded else "within"
        return (
            f"utilization-only validation AUROC {self.auroc:.3f} ({verdict} bound "
            f"{self.bound:.2f}; features {self.features})"
        )


def check_visit_bias(data: Any, utilization_columns: list[str], bound: float) -> VisitBiasReport:
    """Fit a utilization-only model on train, score AUROC on validation; warn above ``bound``."""
    cols = list(utilization_columns)
    model = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000)),
        ]
    )
    model.fit(data.train.X[cols], data.train.y)
    auroc = float(
        roc_auc_score(data.validation.y, model.predict_proba(data.validation.X[cols])[:, 1])
    )
    report = VisitBiasReport(auroc, float(bound), cols)
    if report.exceeded:
        warnings.warn(f"possible index-visit bias: {report}", UserWarning, stacklevel=2)
    return report
