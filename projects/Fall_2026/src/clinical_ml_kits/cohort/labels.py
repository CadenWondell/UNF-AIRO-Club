"""Phenotype labels: cases, positive-evidence controls, index times, control sampling.

Label construction (here) and feature construction (``features/``) share only the adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from clinical_ml_kits.cohort.index import add_attributes, case_index, case_index_visits
from clinical_ml_kits.cohort.rules import RuleEvaluator
from clinical_ml_kits.cohort.sampling import sample_controls
from clinical_ml_kits.core.kit_schema import HistoryRule, ObservationHistory
from clinical_ml_kits.core.logging import get_logger

_log = get_logger("cohort")
COLUMNS = [
    "person_id",
    "index_time",
    "index_visit_id",
    "label",
    "visit_type",
    "calendar_year",
    "sex_at_birth",
    "age_band",
    "matched_case",
]


@dataclass
class CohortResult:
    table: pd.DataFrame  # one row per person
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def sampled_prevalence(self) -> float:
        n = len(self.table)
        return float(self.table.label.sum() / n) if n else float("nan")


def _cohort_ok(ev: RuleEvaluator, cohort: Any, cands: pd.DataFrame) -> pd.Series:
    ok = pd.Series(True, index=cands.index)
    for r in cohort.inclusion:
        ok &= ev.evaluate(r, cands)
    for r in cohort.exclusion:
        ok &= ~ev.evaluate(r, cands)
    return ok


def build_cohort(phenotype: Any, cohort: Any, adapter: Any) -> CohortResult:
    concepts = sorted(phenotype.concepts() | cohort.concepts())
    obs = adapter.observations(concepts=concepts)
    persons = adapter.persons()
    ev = RuleEvaluator(obs, persons)
    visits = adapter.visits()
    visit_types = visits.drop_duplicates("visit_id").set_index("visit_id").visit_type
    history = HistoryRule(
        observation_history=ObservationHistory(min=phenotype.min_observation_history)
    )
    counts: dict[str, int] = {}

    # ---------------------------------------------------------------- cases
    ever = case_index(ev, phenotype.case_rule)
    cand = ever.rename(columns={"index_time": "t"})
    in_cohort = _cohort_ok(ev, cohort, cand)
    hist_ok = ev.evaluate(history, cand)
    cases = ever[in_cohort & hist_ok].copy()
    counts["case_rule_satisfied"] = len(ever)
    counts["cases_excluded_cohort"] = int((~in_cohort).sum())
    excluded_hist = int((in_cohort & ~hist_ok).sum())
    cases["index_visit_id"] = cases.person_id.map(case_index_visits(ev, cases, phenotype.case_rule))
    cases = add_attributes(cases, ev, persons, visit_types).assign(label=1, matched_case=None)

    # ---------------------------------------------------------------- controls
    vtypes = phenotype.control_index_rule.visit_types or None
    cv = adapter.index_candidates(vtypes)
    cv = cv[~cv.person_id.isin(ever.person_id)].reset_index(drop=True)
    cc = cv.rename(columns={"index_time": "t"})
    rule_ok = ev.evaluate(phenotype.control_rule, cc) & _cohort_ok(ev, cohort, cc)
    hist_c = ev.evaluate(history, cc)
    eligible = cv[rule_ok & hist_c].drop(columns=["visit_type"])
    hist_only = set(cv[rule_ok & ~hist_c].person_id) - set(eligible.person_id)
    counts["excluded_min_history"] = excluded_hist + len(hist_only)
    eligible = add_attributes(eligible, ev, persons, visit_types)
    controls, scounts = sample_controls(cases, eligible, phenotype.control_sampling)
    counts.update(scounts)
    controls = controls.assign(label=0)
    table = pd.concat([cases[COLUMNS], controls[COLUMNS]], ignore_index=True)
    table = table.sort_values("person_id").reset_index(drop=True)
    if not table.person_id.is_unique:
        raise AssertionError("cohort construction produced more than one row for a person")
    counts["cases"] = int(table.label.sum())
    counts["controls"] = int((table.label == 0).sum())
    _log.info("cohort built: %s", counts)
    return CohortResult(table, counts)
