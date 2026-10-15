"""T078: feature registry, unit handling, plausible ranges, and V-25 traceability."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from clinical_ml_kits.adapters.synthetic_clinical.adapter import SyntheticClinicalAdapter
from clinical_ml_kits.core.errors import PendingVerification
from clinical_ml_kits.core.values import Provisional, Sourced, Unverified
from clinical_ml_kits.features.registry import FeatureRegistry, flag_out_of_range

ROOT = Path(__file__).resolve().parents[3]
FIX = ROOT / "tests" / "fixtures"
REG = FeatureRegistry.load(ROOT / "definitions" / "features" / "registry.yaml")
FREG = FeatureRegistry.load(FIX / "definitions" / "features" / "registry.yaml")


def _fixture_adapter(rows: list[dict]) -> SyntheticClinicalAdapter:
    persons = pd.DataFrame(
        {
            "person_id": ["SYN-T-1"],
            "birth_date": [pd.Timestamp("1970-01-01")],
            "sex_at_birth": ["SYN-SEX-F"],
            "observation_start": [pd.NaT],
            "observation_end": [pd.NaT],
        }
    )
    obs = pd.DataFrame(
        [
            {
                "person_id": "SYN-T-1",
                "domain": "measurement",
                "start_time": pd.Timestamp("2025-01-01"),
                **r,
            }
            for r in rows
        ]
    )
    return SyntheticClinicalAdapter(
        persons, obs, definitions_dir=FIX / "definitions", source_label="test"
    )


def test_entry_fields() -> None:
    e = REG.get("creatinine")
    assert (e.domain, e.value_type, e.concept.id) == ("measurement", "numeric", "creatinine")
    assert e.provenance
    for key in (
        "systolic_bp",
        "hba1c",
        "ldl",
        "hemoglobin",
        "ast",
        "sodium",
        "tsh",
        "age",
        "sex_at_birth",
        "outpatient_visits",
    ):
        assert key in REG


def test_accepted_unit_converted_and_unaccepted_rejected() -> None:
    a = _fixture_adapter(
        [
            {"concept_id": "SYN-FX-CREATININE", "value_num": 2.0, "unit_raw": "fx-half-unit"},
            {"concept_id": "SYN-FX-CREATININE", "value_num": 1.1, "unit_raw": "mg/dL"},
            {"concept_id": "SYN-FX-CREATININE", "value_num": 9.0, "unit_raw": "bogus"},
        ]
    )
    obs = a.observations(concepts=["fx_creatinine"])
    assert sorted(obs.value_num) == [1.0, 1.1]
    assert set(obs.unit) == {"mg/dL"}
    assert a.unit_rejections == {"fx_creatinine": 1}


def test_out_of_range_flagged_not_clamped() -> None:
    a = _fixture_adapter(
        [
            {"concept_id": "SYN-FX-BMI", "value_num": 500.0, "unit_raw": "kg/m2"},
            {"concept_id": "SYN-FX-BMI", "value_num": 25.0, "unit_raw": "kg/m2"},
        ]
    )
    flagged = flag_out_of_range(a.observations(concepts=["fx_bmi"]), FREG, {"fx_bmi": "fx_bmi"})
    assert list(flagged.value_num) == [25.0, 500.0] or list(flagged.value_num) == [500.0, 25.0]
    assert flagged.set_index("value_num").out_of_range.to_dict() == {500.0: True, 25.0: False}


def test_units_and_ranges_traceable_to_v25() -> None:
    for e in REG.features:
        for name in ("canonical_unit", "plausible_range"):
            v = getattr(e, name)
            if v is None:
                continue
            if isinstance(v, Sourced):
                assert any(r.is_verified for r in v.provenance)
            else:
                assert isinstance(v, (Provisional, Unverified)), (e.feature_key, name)
                if isinstance(v, Provisional):
                    assert v.pending == "V-25"
    # no clinical range is asserted as verified without a source in the project registry
    assert not any(isinstance(e.plausible_range, Sourced) for e in REG.features)


def test_unverified_omop_raises_under_aou_but_synthetic_resolves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from clinical_ml_kits.adapters.all_of_us import adapter as aou
    from clinical_ml_kits.data.registry import get_adapter

    monkeypatch.setattr(aou, "is_all_of_us_workbench", lambda _d: True)
    with pytest.raises(PendingVerification):
        REG.resolve("creatinine", aou.AllOfUsAdapter.create())
    syn = get_adapter(
        "synthetic_clinical",
        backend="golden",
        golden=[ROOT / "synthetic" / "golden" / "creatinine_timeline.yaml"],
    )
    assert REG.resolve("creatinine", syn).codes == ["SYN-CREATININE"]


def test_no_numeric_concept_ids_under_definitions() -> None:
    import re

    for p in (ROOT / "definitions").rglob("*.yaml"):
        assert not re.search(r"concept_id:\s*['\"]?\d+", p.read_text()), p
