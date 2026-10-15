"""Effective-cutoff computation, vectorized over a long observation table."""

from __future__ import annotations

import pandas as pd

from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy


def effective_upper_bound(index_time: pd.Timestamp, policy: ResolvedTemporalPolicy) -> pd.Timestamp:
    """Exclusive ``before`` bound for adapter pushdown (rule 1 only)."""
    day = pd.Timestamp(index_time).normalize() - policy.washout
    return day + pd.Timedelta(days=1) if policy.same_day == "include" else day


def permitted_mask(
    obs: pd.DataFrame, index: pd.DataFrame, policy: ResolvedTemporalPolicy
) -> pd.Series:
    """Boolean mask over ``obs`` rows permitted for their person's index (rules 1–4).

    ``index`` has columns ``person_id, index_time`` and optionally ``index_visit_id``; persons
    without an index row get no observations.
    """
    cols = ["person_id", "index_time"] + (["index_visit_id"] if "index_visit_id" in index else [])
    m = obs[["person_id"]].join(
        index[cols].drop_duplicates("person_id").set_index("person_id"), on="person_id"
    )
    has_index = m.index_time.notna()
    idx_day = pd.to_datetime(m.index_time).dt.normalize()
    o_day = pd.to_datetime(obs.start_time).dt.normalize()
    upper = idx_day - policy.washout
    ok = (o_day <= upper) if policy.same_day == "include" else (o_day < upper)
    ok &= o_day >= idx_day - policy.lookback
    if policy.exclude_index_encounter and "index_visit_id" in m:
        same_visit = obs.visit_id.notna() & (obs.visit_id == m.index_visit_id)
        ok &= ~same_visit
    for w in policy.windowed_exclusions:
        target = obs.logical_concept == w.concept if w.concept else obs.domain == w.domain
        inside = (o_day >= idx_day - w.before) & (o_day <= idx_day + w.after)
        ok &= ~(target & inside)
    return (ok & has_index).fillna(False).astype(bool)
