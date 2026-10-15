"""Vectorized RuleExpr evaluation over adapter data (data-model § 3).

``evaluate(rule, candidates)`` answers, for each candidate ``(person_id, t)``, whether the rule
holds using observations dated on or before ``t`` (date precision). Label logic lives here, in
``cohort/``, separate from feature construction in ``features/``.
"""

from __future__ import annotations

import operator
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from clinical_ml_kits.core.kit_schema import (
    AgeRule,
    AllOf,
    AnyOf,
    HasEventRule,
    HistoryRule,
    MeasurementRule,
    Not,
    VisitRule,
)
from clinical_ml_kits.core.values import parse_duration, resolve

OPS: dict[str, Callable[[Any, Any], Any]] = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
}


class RuleEvaluator:
    def __init__(self, observations: pd.DataFrame, persons: pd.DataFrame) -> None:
        obs = observations.copy()
        obs["day"] = pd.to_datetime(obs.start_time).dt.normalize()
        self.obs = obs
        p = persons.set_index("person_id")
        start = pd.to_datetime(p.observation_start)
        first = obs.groupby("person_id").day.min()
        # Observation-period start when the dataset provides it; otherwise the earliest record.
        self.history_start = start.fillna(first.reindex(start.index))
        self.birth = pd.to_datetime(p.birth_date)

    def evaluate(self, rule: object, candidates: pd.DataFrame) -> pd.Series:
        """Boolean per candidate row (``person_id``, ``t``), aligned to ``candidates.index``."""
        c = candidates[["person_id", "t"]].copy()
        c["t"] = pd.to_datetime(c.t).dt.normalize()
        return self._eval(rule, c).reindex(candidates.index).fillna(False).astype(bool)

    # ------------------------------------------------------------------ internals
    def _eval(self, rule: object, c: pd.DataFrame) -> pd.Series:
        if isinstance(rule, AllOf):
            out = pd.Series(True, index=c.index)
            for r in rule.all_of:
                out &= self._eval(r, c)
            return out
        if isinstance(rule, AnyOf):
            out = pd.Series(False, index=c.index)
            for r in rule.any_of:
                out |= self._eval(r, c)
            return out
        if isinstance(rule, Not):
            return ~self._eval(rule.not_, c)
        if isinstance(rule, HasEventRule):
            e = rule.has_event
            return self._count(
                c, self.obs.logical_concept == e.concept, e.within, e.distinct_days
            ) >= int(resolve(e.min_count))
        if isinstance(rule, MeasurementRule):
            m = rule.measurement
            op = OPS[m.op]
            sel = (self.obs.logical_concept == m.concept) & self.obs.value_num.notna()
            if m.unit is not None:
                sel &= self.obs.unit == m.unit
            sel &= op(self.obs.value_num, float(resolve(m.value))).fillna(False)
            return self._count(c, sel, m.within, m.distinct_days) >= int(resolve(m.min_count))
        if isinstance(rule, AgeRule):
            years = float(resolve(rule.age_at_index.years))
            age = (c.t - c.person_id.map(self.birth)).dt.days / 365.25
            return OPS[rule.age_at_index.op](age, years).fillna(False)
        if isinstance(rule, HistoryRule):
            need = parse_duration(resolve(rule.observation_history.min))
            start = c.person_id.map(self.history_start)
            return ((c.t - start) >= need).fillna(False)
        if isinstance(rule, VisitRule):
            v = rule.visit
            sel = self.obs.domain == "visit"
            if v.type_concept:
                sel &= self.obs.logical_concept == v.type_concept
            return self._count(c, sel, v.within, True) >= int(resolve(v.min_count))
        raise TypeError(f"unsupported rule node {type(rule).__name__}")

    def _count(
        self, c: pd.DataFrame, sel: pd.Series, within: object, distinct_days: bool
    ) -> pd.Series:
        rows = self.obs.loc[sel, ["person_id", "day"]]
        if rows.empty or c.empty:
            return pd.Series(0, index=c.index)
        cand = c.reset_index().rename(columns={"index": "_cid"})
        m = cand.merge(rows, on="person_id", how="inner")
        keep = m.day <= m.t
        if within is not None:
            keep &= m.day > m.t - parse_duration(resolve(within))
        m = m[keep]
        if distinct_days:
            counts = m.drop_duplicates(["_cid", "day"]).groupby("_cid").size()
        else:
            counts = m.groupby("_cid").size()
        return counts.reindex(c.index, fill_value=0).astype(np.int64)
