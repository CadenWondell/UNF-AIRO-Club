"""T082: RuleExpr predicates and combinators on golden patients."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from clinical_ml_kits.cohort.rules import RuleEvaluator
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
from clinical_ml_kits.data.registry import get_adapter

FIX = Path(__file__).resolve().parents[2] / "fixtures"
A = get_adapter(
    "synthetic_clinical", backend="golden", golden=[FIX / "golden" / "cohort_rules.yaml"], root=FIX
)
EV = RuleEvaluator(A.observations(), A.persons())
NOTE = "Test value for synthetic execution and tests only; not an approved clinical rule."


def prov(v: object) -> dict:
    return {"provisional": v, "note": NOTE, "pending": "V-21"}


def at(pid: str, day: str) -> pd.DataFrame:
    return pd.DataFrame({"person_id": [pid], "t": [pd.Timestamp(day)]})


def ev(rule: object, pid: str, day: str) -> bool:
    return bool(EV.evaluate(rule, at(pid, day)).iloc[0])


DX2 = HasEventRule.model_validate(
    {"has_event": {"concept": "fx_dx", "min_count": prov(2), "distinct_days": True}}
)


def test_has_event_counts_distinct_days_as_of_t() -> None:
    assert not ev(DX2, "SYN-C-CASE", "2024-05-31")
    assert ev(DX2, "SYN-C-CASE", "2024-06-01")
    assert not ev(DX2, "SYN-C-NEARMISS", "2026-01-01")


def test_has_event_within_window() -> None:
    r = HasEventRule.model_validate(
        {"has_event": {"concept": "fx_comorbidity", "within": prov("P30D")}}
    )
    assert ev(r, "SYN-C-LATECASE", "2024-02-01")
    assert not ev(r, "SYN-C-LATECASE", "2024-04-01")
    assert not ev(r, "SYN-C-LATECASE", "2024-01-19")  # before the event


def test_measurement_predicate() -> None:
    lt = MeasurementRule.model_validate(
        {"measurement": {"concept": "fx_marker", "op": "<", "value": prov(5.0), "unit": "mg/dL"}}
    )
    ge = MeasurementRule.model_validate(
        {"measurement": {"concept": "fx_marker", "op": ">=", "value": prov(5.0), "unit": "mg/dL"}}
    )
    assert ev(lt, "SYN-C-CONTROL", "2024-05-01") and not ev(lt, "SYN-C-CONTROL", "2024-04-30")
    assert not ev(ge, "SYN-C-CONTROL", "2024-09-01")


def test_age_and_history() -> None:
    age = AgeRule.model_validate({"age_at_index": {"op": ">=", "years": prov(18)}})
    assert ev(age, "SYN-C-CONTROL", "2024-05-01") and not ev(age, "SYN-C-MINOR", "2024-05-01")
    hist = HistoryRule.model_validate({"observation_history": {"min": prov("P365D")}})
    assert ev(hist, "SYN-C-CONTROL", "2024-05-01")
    assert not ev(hist, "SYN-C-SHORTHIST", "2025-12-01")


def test_visit_predicate() -> None:
    v = VisitRule.model_validate(
        {"visit": {"type_concept": "fx_visit_outpatient", "min_count": prov(2)}}
    )
    assert ev(v, "SYN-C-CONTROL", "2024-05-01") and not ev(v, "SYN-C-CONTROL", "2024-04-01")


def test_combinators() -> None:
    no_comorb = Not.model_validate(
        {"not": {"has_event": {"concept": "fx_comorbidity", "within": prov("P30D")}}}
    )
    case = AllOf(all_of=[DX2, no_comorb])
    assert not ev(case, "SYN-C-LATECASE", "2024-02-01")
    assert ev(case, "SYN-C-LATECASE", "2024-04-01")
    either = AnyOf.model_validate(
        {"any_of": [DX2.model_dump(), {"has_event": {"concept": "fx_marker"}}]}
    )
    assert ev(either, "SYN-C-CONTROL", "2024-05-01") and ev(either, "SYN-C-CASE", "2024-06-01")
    assert not ev(either, "SYN-C-NOEVIDENCE", "2024-05-01")


def test_vectorized_over_many_candidates() -> None:
    cands = pd.DataFrame(
        {
            "person_id": ["SYN-C-CASE"] * 3 + ["SYN-C-NEARMISS"],
            "t": pd.to_datetime(["2024-03-01", "2024-06-01", "2025-01-01", "2025-01-01"]),
        }
    )
    assert list(EV.evaluate(DX2, cands)) == [False, True, True, False]


def test_unverified_threshold_refused() -> None:
    r = MeasurementRule.model_validate(
        {"measurement": {"concept": "fx_marker", "op": "<", "value": "UNVERIFIED"}}
    )
    with pytest.raises(ValueError, match="UNVERIFIED"):
        EV.evaluate(r, at("SYN-C-CONTROL", "2024-05-01"))
