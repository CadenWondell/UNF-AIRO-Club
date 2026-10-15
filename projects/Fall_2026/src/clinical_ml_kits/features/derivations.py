"""Derivation library shared by CutoffView and FeatureMatrixBuilder (identical semantics).

Every function takes a long frame of already-permitted rows (columns ``person_id``,
``start_time``, ``value_num``) sorted by ``person_id, start_time`` and a Series of effective cutoff
days per person; it returns one value per person (NaN = missing). Vectorized with groupby.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from clinical_ml_kits.core.values import parse_duration

ROLLING = re.compile(r"^rolling_mean\((P\d+[DW])\)$")
NUMERIC = (
    "latest",
    "previous",
    "delta",
    "pct_change",
    "mean",
    "min",
    "max",
    "std",
    "slope",
    "count",
    "time_since_last",
)


def _days_before(frame: pd.DataFrame, cutoff: pd.Series) -> pd.Series:
    """Days from each row to its person's effective cutoff day (>= 0 for permitted rows)."""
    c = frame.person_id.map(cutoff)
    return (c - frame.start_time.dt.normalize()).dt.days.astype(float)


def compute(
    frame: pd.DataFrame, cutoff: pd.Series, derivation: str, persons: pd.Index
) -> pd.Series:
    """One derivation for every person in ``persons`` (NaN where undefined; count -> 0)."""
    f = frame[frame.value_num.notna()] if derivation not in ("count", "time_since_last") else frame
    g = f.groupby("person_id", sort=False)
    m = ROLLING.match(derivation)
    if m:
        window = parse_duration(m.group(1)).days
        recent = f[_days_before(f, cutoff) < window]
        out = recent.groupby("person_id", sort=False).value_num.mean()
    elif derivation == "count":
        return g.size().reindex(persons, fill_value=0).astype(float)
    elif derivation in ("latest", "previous", "delta", "pct_change"):
        rank = g.cumcount(ascending=False)
        last = f[rank == 0].set_index("person_id").value_num
        prev = f[rank == 1].set_index("person_id").value_num
        if derivation == "latest":
            out = last
        elif derivation == "previous":
            out = prev
        else:
            last, prev = last.reindex(persons), prev.reindex(persons)
            delta = last - prev
            out = delta if derivation == "delta" else (delta / prev.where(prev != 0))
    elif derivation in ("mean", "min", "max"):
        out = getattr(g.value_num, derivation)()
    elif derivation == "std":
        out = g.value_num.std(ddof=1)
    elif derivation == "time_since_last":
        last_day = g.start_time.max().dt.normalize()
        out = (cutoff.reindex(last_day.index) - last_day).dt.days.astype(float)
    elif derivation == "slope":
        x = -_days_before(f, cutoff)
        tmp = pd.DataFrame(
            {"person_id": f.person_id, "x": x, "y": f.value_num, "xx": x * x, "xy": x * f.value_num}
        )
        s = tmp.groupby("person_id", sort=False).agg(
            n=("x", "size"), sx=("x", "sum"), sy=("y", "sum"), sxx=("xx", "sum"), sxy=("xy", "sum")
        )
        den = s.n * s.sxx - s.sx**2
        out = (s.n * s.sxy - s.sx * s.sy) / den.where((s.n >= 2) & (den.abs() > 1e-12))
    else:
        raise ValueError(f"unknown derivation {derivation!r}")
    return out.reindex(persons).astype(float).replace([np.inf, -np.inf], np.nan)
