"""Index-time construction: case index (first date the case rule holds), control candidates."""

from __future__ import annotations

import pandas as pd

from clinical_ml_kits.cohort.rules import RuleEvaluator
from clinical_ml_kits.core.kit_schema import rule_concepts


def case_index(ev: RuleEvaluator, case_rule: object) -> pd.DataFrame:
    """Earliest date each person satisfies ``case_rule`` (``person_id, index_time``)."""
    concepts = rule_concepts(case_rule)
    o = ev.obs[ev.obs.logical_concept.isin(concepts)]
    cands = o[["person_id", "day"]].drop_duplicates().rename(columns={"day": "t"})
    cands = cands.sort_values(["person_id", "t"]).reset_index(drop=True)
    ok = ev.evaluate(case_rule, cands)
    first = cands[ok].groupby("person_id", sort=True).t.min()
    return first.rename("index_time").reset_index()


def case_index_visits(ev: RuleEvaluator, cases: pd.DataFrame, case_rule: object) -> pd.Series:
    """The visit on each case's index day: a case-rule observation's visit, else any visit."""
    concepts = rule_concepts(case_rule)
    o = ev.obs.merge(cases, on="person_id")
    o = o[(o.day == o.index_time) & o.visit_id.notna()]
    o = o.assign(pri=(~o.logical_concept.isin(concepts)).astype(int))
    o = o.sort_values(["person_id", "pri", "visit_id"])
    return o.groupby("person_id").visit_id.first()


def add_attributes(
    df: pd.DataFrame, ev: RuleEvaluator, persons: pd.DataFrame, visit_types: pd.Series
) -> pd.DataFrame:
    """Matching attributes at the index: visit_type, calendar_year, sex_at_birth, age_band."""
    p = persons.set_index("person_id")
    age = (df.index_time - df.person_id.map(pd.to_datetime(p.birth_date))).dt.days / 365.25
    return df.assign(
        visit_type=df.index_visit_id.map(visit_types),
        calendar_year=df.index_time.dt.year,
        sex_at_birth=df.person_id.map(p.sex_at_birth),
        age_band=(age // 10 * 10).astype("Int64"),
    )
