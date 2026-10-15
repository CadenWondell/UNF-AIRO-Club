"""Evaluation helpers for Template A."""

from clinical_ml_kits.evaluation.calibration import calibration_summary, reliability_bins
from clinical_ml_kits.evaluation.compare import compare_models
from clinical_ml_kits.evaluation.explain import (
    coefficient_table,
    contributions,
    permutation_importance_table,
)
from clinical_ml_kits.evaluation.metrics import BinaryResults, evaluate_binary
from clinical_ml_kits.evaluation.plots import plot_calibration, plot_roc_pr

__all__ = [
    "BinaryResults",
    "calibration_summary",
    "coefficient_table",
    "compare_models",
    "contributions",
    "evaluate_binary",
    "permutation_importance_table",
    "plot_calibration",
    "plot_roc_pr",
    "reliability_bins",
]
