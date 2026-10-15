"""V-03 dissemination filter for aggregates leaving the All of Us Researcher Workbench.

Parameters come only from the V-03 SourceRecord via ``DataEnvironmentPolicy.dissemination_rule``.
Applies to anything leaving the Workbench (completion records, FR-081 evidence, repository
content); in-session display inside the Workbench is not filtered.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from clinical_ml_kits.data.policy import DisseminationRule

COUNT_KEYS = {
    "n",
    "n_pos",
    "n_neg",
    "count",
    "eligible_persons",
    "positives",
    "eligible_controls",
    "cases",
    "controls",
    "excluded",
    "tp",
    "fp",
    "fn",
    "tn",
}


def suppress_count(n: Any, rule: DisseminationRule) -> Any:
    if isinstance(n, (int, float)) and not isinstance(n, bool) and float(n).is_integer():
        return rule.marker if rule.is_restricted(int(n)) else n
    return n


def suppress_confusion(cm: dict[str, int], rule: DisseminationRule) -> dict[str, Any]:
    out: dict[str, Any] = {k: suppress_count(v, rule) for k, v in cm.items()}
    hidden = [k for k, v in out.items() if v == rule.marker]
    if len(hidden) == 1:  # one hidden cell could be derived from reported totals
        rest = sorted((v, k) for k, v in cm.items() if k not in hidden and v > 0)
        if rest:
            out[rest[0][1]] = rule.marker
    return out


def suppress_bins(
    bins: pd.DataFrame, rule: DisseminationRule, n_events: pd.Series | None = None
) -> pd.DataFrame:
    out = bins.copy().astype({"n": object})
    small = bins.n.map(lambda v: rule.is_restricted(int(v)))
    if n_events is not None:
        small |= (
            pd.Series(n_events).reset_index(drop=True).map(lambda v: rule.is_restricted(int(v)))
        )
    out.loc[small, "n"] = rule.marker
    out.loc[small, "observed_rate"] = float("nan")
    return out


def suppress_metrics(
    metrics: dict[str, Any], *, n_pos: int, n_neg: int, rule: DisseminationRule
) -> dict[str, Any]:
    """Derived metrics are withheld when computed from a group of 1–20 positives/negatives/rows."""
    if any(rule.is_restricted(int(x)) for x in (n_pos, n_neg, n_pos + n_neg)):
        return {k: f"{rule.marker} (suppressed)" for k in metrics}
    return dict(metrics)


def filter_for_export(obj: Any, rule: DisseminationRule) -> Any:
    """Recursively suppress count-like fields (keys in COUNT_KEYS) in a JSON-like structure."""
    if isinstance(obj, dict):
        if {"tn", "fp", "fn", "tp"} <= set(obj):
            return suppress_confusion(obj, rule)
        restricted = any(
            k in COUNT_KEYS and suppress_count(v, rule) == rule.marker for k, v in obj.items()
        )
        out = {}
        for k, v in obj.items():
            if k in COUNT_KEYS:
                out[k] = suppress_count(v, rule)
            elif restricted and k in ("prevalence", "rate", "observed_rate", "fraction"):
                out[k] = f"{rule.marker} (suppressed)"
            else:
                out[k] = filter_for_export(v, rule)
        return out
    if isinstance(obj, list):
        return [filter_for_export(v, rule) for v in obj]
    return obj
