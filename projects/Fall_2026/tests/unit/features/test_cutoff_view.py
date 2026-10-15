"""T072: CutoffView (contracts/patient-feature-api.md) on golden patients."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pandas as pd
import pytest

from clinical_ml_kits.core.errors import ProhibitedFeatureError
from clinical_ml_kits.data.registry import get_adapter
from clinical_ml_kits.features.timeline import Missing, Obs, PatientTimeline
from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy

GOLDEN = Path(__file__).resolve().parents[3] / "synthetic" / "golden"
A = get_adapter("synthetic_clinical", backend="golden", golden=sorted(GOLDEN.glob("*.yaml")))
INDEX = pd.Timestamp("2026-01-01")


def pol(same_day: str = "include", lookback: str = "P3650D", **kw) -> ResolvedTemporalPolicy:  # type: ignore[no-untyped-def]
    return ResolvedTemporalPolicy.from_values(
        same_day=same_day,
        washout=kw.get("washout", "P0D"),
        lookback=lookback,
        exclude_index_encounter=kw.get("exclude_index_encounter", False),
        windowed_exclusions=kw.get("windowed_exclusions"),
    )


def timeline(pid: str) -> PatientTimeline:
    return PatientTimeline.from_adapter(A, pid)


def test_creatinine_include() -> None:
    v = timeline("SYN-G-CREAT-001").as_of(INDEX, pol("include"))
    latest, previous = v.latest("creatinine"), v.previous("creatinine")
    assert isinstance(latest, Obs) and latest.value == 1.2
    assert isinstance(previous, Obs) and previous.value == 1.0
    assert v.derive("creatinine", "delta") == pytest.approx(0.2)
    assert v.derive("creatinine", "count") == 3
    assert 1.5 not in [o.value for o in v.history("creatinine")]


def test_creatinine_exclude_index_day() -> None:
    v = timeline("SYN-G-CREAT-001").as_of(INDEX, pol("exclude_index_day"))
    assert v.latest("creatinine").value == 1.0  # type: ignore[union-attr]
    assert v.previous("creatinine").value == 0.9  # type: ignore[union-attr]
    assert v.derive("creatinine", "delta") == pytest.approx(0.1)
    assert all(o.value != 1.5 for o in v.history("creatinine"))


def test_obs_carries_provenance_fields() -> None:
    o = timeline("SYN-G-CREAT-001").as_of(INDEX, pol()).latest("creatinine")
    assert isinstance(o, Obs)
    assert o.unit == "mg/dL" and o.domain == "measurement" and o.concept_id == "SYN-CREATININE"
    assert o.source_table == "synthetic_golden" and o.mapping_version == "0.1.0"
    assert o.time == pd.Timestamp("2026-01-01")


def test_view_is_immutable() -> None:
    v = timeline("SYN-G-CREAT-001").as_of(INDEX, pol())
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        v.index_time = pd.Timestamp("2030-01-01")  # type: ignore[misc]
    frame = v.frame
    frame.loc[:, "value_num"] = -1.0
    assert v.latest("creatinine").value == 1.2  # type: ignore[union-attr]


def test_missing_reasons() -> None:
    sparse = timeline("SYN-G-SPARSE-001").as_of(INDEX, pol())
    m = sparse.latest("creatinine")
    assert isinstance(m, Missing) and m.reason == "no_observation"
    assert isinstance(sparse.previous("bmi"), Missing)
    sd = timeline("SYN-G-SD-001")
    lb = sd.as_of(INDEX, pol(lookback="P365D")).latest("creatinine")
    assert isinstance(lb, Missing) and lb.reason == "outside_lookback"
    ex = sd.as_of(INDEX, pol("exclude_index_day")).latest("potassium")
    assert isinstance(ex, Missing) and ex.reason == "excluded_by_policy"


def test_visits_and_conditions() -> None:
    v = timeline("SYN-G-MV-001").as_of(INDEX, pol())
    assert len(v.prior_visits()) == 4
    assert len(v.prior_visits(type="visit_inpatient")) == 1
    assert len(v.prior_visits(within="P100D")) == 1  # 2025-12-01 only
    assert len(v.prior_visits(within="P200D")) == 2  # + 2025-07-01 (184 days)
    assert v.has_condition("bmi") is True
    assert v.has_condition("ldl") is False
    assert v.medication_history("creatinine") == []  # not a drug concept → empty


def test_prohibited_raises() -> None:
    v = timeline("SYN-G-CREAT-001").as_of(INDEX, pol(), prohibited={"creatinine"})
    with pytest.raises(ProhibitedFeatureError):
        v.latest("creatinine")
