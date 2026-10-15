"""Patient view: PatientTimeline and the immutable CutoffView (contracts/patient-feature-api.md).

Teaching/EDA entry point for one patient. It shares the derivation library with the bulk
``FeatureMatrixBuilder``, so both produce identical values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd

from clinical_ml_kits.core.errors import ProhibitedFeatureError
from clinical_ml_kits.core.values import parse_duration
from clinical_ml_kits.features import derivations
from clinical_ml_kits.temporal.cutoff import permitted_mask
from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy

MissingReason = Literal["no_observation", "outside_lookback", "excluded_by_policy", "unit_rejected"]


@dataclass(frozen=True)
class Missing:
    """Typed missing value: never 0 and never a "normal" value (FR-059)."""

    reason: MissingReason

    def __bool__(self) -> bool:
        return False


@dataclass(frozen=True)
class Obs:
    value: float | None
    unit: str | None
    time: pd.Timestamp
    domain: str
    concept_id: str
    source_table: str
    mapping_version: str | None
    visit_id: str | None = None


def _obs(row: Any) -> Obs:
    v = row.value_num
    return Obs(
        value=None if pd.isna(v) else float(v),
        unit=None if pd.isna(row.unit) else row.unit,
        time=pd.Timestamp(row.start_time),
        domain=row.domain,
        concept_id=row.concept_id,
        source_table=row.source_table,
        mapping_version=row.mapping_version,
        visit_id=row.visit_id,
    )


@dataclass(frozen=True)
class PatientTimeline:
    person: dict[str, Any]
    observations: pd.DataFrame = field(repr=False)

    @classmethod
    def from_adapter(cls, adapter: Any, person_id: str) -> PatientTimeline:
        persons = adapter.persons([person_id])
        if persons.empty:
            raise KeyError(f"unknown person {person_id!r}")
        obs = adapter.observations(person_ids=[person_id])
        return cls(persons.iloc[0].to_dict(), obs)

    def as_of(
        self,
        index_time: pd.Timestamp,
        policy: ResolvedTemporalPolicy,
        index_visit_id: str | None = None,
        prohibited: set[str] | frozenset[str] = frozenset(),
    ) -> CutoffView:
        idx = pd.DataFrame(
            {
                "person_id": [self.person["person_id"]],
                "index_time": [pd.Timestamp(index_time)],
                "index_visit_id": [index_visit_id],
            }
        )
        mask = permitted_mask(self.observations, idx, policy)
        return CutoffView(
            person=dict(self.person),
            index_time=pd.Timestamp(index_time),
            index_visit_id=index_visit_id,
            policy=policy,
            _frame=self.observations[mask].reset_index(drop=True),
            _all=self.observations,
            prohibited=frozenset(prohibited),
        )


@dataclass(frozen=True)
class CutoffView:
    """Only observations permitted by the effective cutoff. Immutable."""

    person: dict[str, Any]
    index_time: pd.Timestamp
    index_visit_id: str | None
    policy: ResolvedTemporalPolicy
    _frame: pd.DataFrame = field(repr=False)
    _all: pd.DataFrame = field(repr=False)
    prohibited: frozenset[str] = frozenset()

    @property
    def frame(self) -> pd.DataFrame:
        return self._frame.copy()

    @property
    def cutoff_day(self) -> pd.Timestamp:
        return self.index_time.normalize() - self.policy.washout

    def _rows(self, concept: str) -> pd.DataFrame:
        if concept in self.prohibited:
            raise ProhibitedFeatureError(f"{concept!r} is prohibited/label-defining for this kit")
        return self._frame[self._frame.logical_concept == concept]

    def _missing(self, concept: str) -> Missing:
        rows = self._all[self._all.logical_concept == concept]
        upper = self.index_time.normalize() - self.policy.washout
        pre = rows[rows.start_time.dt.normalize() <= upper]
        if pre.empty:
            return Missing("no_observation")
        start = self.index_time.normalize() - self.policy.lookback
        if (pre.start_time.dt.normalize() < start).all():
            return Missing("outside_lookback")
        return Missing("excluded_by_policy")

    def history(self, concept: str) -> list[Obs]:
        return [_obs(r) for r in self._rows(concept).itertuples()]

    def latest(self, concept: str) -> Obs | Missing:
        h = [o for o in self.history(concept) if o.value is not None]
        return h[-1] if h else self._missing(concept)

    def previous(self, concept: str) -> Obs | Missing:
        h = [o for o in self.history(concept) if o.value is not None]
        if len(h) >= 2:
            return h[-2]
        return self._missing(concept) if not h else Missing("no_observation")

    def derive(self, concept: str, derivation: str) -> float | str | Missing:
        if concept == "age":
            if concept in self.prohibited:
                raise ProhibitedFeatureError("age is prohibited for this kit")
            birth = pd.Timestamp(self.person["birth_date"])
            return float((self.index_time.normalize() - birth).days) / 365.25
        if concept == "sex_at_birth":
            v = self.person.get("sex_at_birth")
            return str(v) if v is not None and not pd.isna(v) else Missing("no_observation")
        rows = self._rows(concept)
        pid = self.person["person_id"]
        out = derivations.compute(
            rows, pd.Series({pid: self.cutoff_day}), derivation, pd.Index([pid])
        ).iloc[0]
        if pd.isna(out):
            return self._missing(concept) if rows.empty else Missing("no_observation")
        return float(out)

    def has_condition(self, concept: str, within: str | None = None) -> bool:
        rows = self._rows(concept)
        if within:
            start = self.cutoff_day - parse_duration(within)
            rows = rows[rows.start_time.dt.normalize() > start]
        return not rows.empty

    def medication_history(self, concept: str) -> list[Obs]:
        return [o for o in self.history(concept) if o.domain == "drug"]

    def prior_visits(self, type: str | None = None, within: str | None = None) -> list[Obs]:
        rows = self._frame[self._frame.domain == "visit"]
        if type:
            rows = rows[rows.logical_concept == type]
        if within:
            start = self.cutoff_day - parse_duration(within)
            rows = rows[rows.start_time.dt.normalize() > start]
        return [_obs(r) for r in rows.itertuples()]
