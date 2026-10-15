"""Plotting helpers returning matplotlib Figures."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

from clinical_ml_kits.evaluation.calibration import reliability_bins


def plot_roc_pr(y: Any, proba: Any, title: str = "") -> Figure:
    """ROC and precision-recall curves; ``proba`` may be one array or {label: array}."""
    curves = proba if isinstance(proba, dict) else {"model": proba}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    yv = np.asarray(y)
    for label, p in curves.items():
        fpr, tpr, _ = roc_curve(yv, p)
        ax1.plot(fpr, tpr, label=f"{label} (AUROC {roc_auc_score(yv, p):.3f})")
        prec, rec, _ = precision_recall_curve(yv, p)
        ax2.plot(rec, prec, label=f"{label} (AUPRC {average_precision_score(yv, p):.3f})")
    ax1.plot([0, 1], [0, 1], "k--", lw=0.8)
    ax2.axhline(yv.mean(), color="k", ls="--", lw=0.8, label=f"prevalence {yv.mean():.3f}")
    ax1.set(xlabel="False positive rate", ylabel="True positive rate", title="ROC")
    ax2.set(xlabel="Recall", ylabel="Precision", title="Precision-recall")
    ax1.legend(fontsize=8)
    ax2.legend(fontsize=8)
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    plt.close(fig)
    return fig


def plot_calibration(
    y: Any,
    proba: Any,
    bins: int = 10,
    strategy: str = "quantile",
    title: str = "Reliability (development-sample probabilities)",
) -> Figure:
    b = reliability_bins(y, proba, bins=bins, strategy=strategy)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="perfect calibration")
    ax.plot(b.mean_predicted, b.observed_rate, "o-", label="model")
    ax.set(xlabel="Mean predicted probability", ylabel="Observed fraction positive", title=title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    plt.close(fig)
    return fig
