"""FeatureMatrixBuilder: vectorized bulk feature construction for a cohort (no per-patient loop).

Columns are ``<feature>__<derivation>``; missing cells are NaN (indicators are added later by
Template A preprocessing). ``lineage`` records, per (person, feature), the latest source time and
visit used, so the leakage checker can verify the cutoff after the fact (R-12 step 3).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd

from clinical_ml_kits.core.values import parse_duration
from clinical_ml_kits.features import derivations
from clinical_ml_kits.temporal.cutoff import effective_upper_bound, permitted_mask
from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy

Kind = Literal["numeric", "event", "person", "person_categorical"]


@dataclass(frozen=True)
class FeatureRequest:
    name: str
    concept: str
    kind: Kind
    derivations: Sequence[str]
    window: str | None = None


@dataclass
class FeatureMatrixBuilder:
    adapter: Any
    features: Sequence[FeatureRequest]
    policy: ResolvedTemporalPolicy
    excluded_concepts: frozenset[str] = field(default_factory=frozenset)

    def build(self, cohort: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """``cohort``: one row per person with ``person_id, index_time[, index_visit_id]``."""
        persons = pd.Index(cohort.person_id, name="person_id")
        if persons.has_duplicates:
            raise ValueError("FeatureMatrixBuilder expects one row per person")
        idx = cohort.copy()
        idx["index_time"] = pd.to_datetime(idx.index_time)
        cutoff = pd.Series(
            (idx.index_time.dt.normalize() - self.policy.washout).to_numpy(), index=persons
        )
        obs_concepts = sorted(
            {f.concept for f in self.features if f.kind in ("numeric", "event")}
            - set(self.excluded_concepts)
        )
        columns: dict[str, pd.Series] = {}
        lineage: list[pd.DataFrame] = []
        obs = pd.DataFrame()
        if obs_concepts:
            bound = max(effective_upper_bound(t, self.policy) for t in idx.index_time)
            obs = self.adapter.observations(
                concepts=obs_concepts, person_ids=list(persons), before=bound
            )
            obs = obs[permitted_mask(obs, idx, self.policy)]
            obs = obs.sort_values(["person_id", "start_time"], kind="stable")
        person_tbl = None
        for f in self.features:
            if f.kind in ("person", "person_categorical"):
                if person_tbl is None:
                    person_tbl = self.adapter.persons(list(persons)).set_index("person_id")
                col = f"{f.name}__latest"
                if f.kind == "person":  # numeric person feature: age at index
                    birth = pd.to_datetime(person_tbl.birth_date).reindex(persons)
                    days = (idx.set_index("person_id").index_time.dt.normalize() - birth).dt.days
                    columns[col] = (days / 365.25).astype(float)
                else:
                    columns[col] = person_tbl["sex_at_birth"].reindex(persons).astype(object)
                continue
            rows = obs[obs.logical_concept == f.concept] if len(obs) else obs
            if f.window and len(rows):
                w = parse_duration(f.window).days
                rows = rows[derivations._days_before(rows, cutoff) < w]
            for d in f.derivations:
                if len(rows) == 0:
                    columns[f"{f.name}__{d}"] = (
                        pd.Series(0.0, index=persons)
                        if d == "count"
                        else pd.Series(np.nan, index=persons)
                    )
                else:
                    columns[f"{f.name}__{d}"] = derivations.compute(rows, cutoff, d, persons)
            if len(rows):
                last = rows.groupby("person_id", sort=False).tail(1)
                lineage.append(
                    pd.DataFrame(
                        {
                            "person_id": last.person_id.to_numpy(),
                            "feature": f.name,
                            "max_source_time": last.start_time.to_numpy(),
                            "visit_id": last.visit_id.to_numpy(),
                        }
                    )
                )
        X = pd.DataFrame(columns, index=persons)
        lin = (
            pd.concat(lineage, ignore_index=True)
            if lineage
            else pd.DataFrame(columns=["person_id", "feature", "max_source_time", "visit_id"])
        )
        return X, lin
