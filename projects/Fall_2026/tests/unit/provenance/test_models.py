"""T022: provenance model validation (data-model § 2, contracts/provenance.md)."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from clinical_ml_kits.provenance.models import Deviation, ProvenanceRef, SourceRecord


def _src(**over: object) -> dict[str, object]:
    d: dict[str, object] = dict(
        source_id="ada_soc_2026",
        title="Standards of Care in Diabetes",
        organization="American Diabetes Association",
        url_or_identifier="https://example.org/soc",
        priority_tier=4,
    )
    d.update(over)
    return d


def test_source_record_valid() -> None:
    s = SourceRecord.model_validate(_src())
    assert s.priority_tier == 4


@pytest.mark.parametrize("missing", ["title", "organization", "url_or_identifier", "priority_tier"])
def test_source_record_requires_fields(missing: str) -> None:
    d = _src()
    del d[missing]
    with pytest.raises(ValidationError, match=missing):
        SourceRecord.model_validate(d)


@pytest.mark.parametrize("tier", [0, 7])
def test_priority_tier_range(tier: int) -> None:
    with pytest.raises(ValidationError, match="priority_tier"):
        SourceRecord.model_validate(_src(priority_tier=tier))


def test_verified_ref_requires_verifier_and_date() -> None:
    base = dict(source_id="s", locator="§1", application="defines X")
    with pytest.raises(ValidationError, match="verified_by"):
        ProvenanceRef.model_validate({**base, "verification_status": "verified"})
    with pytest.raises(ValidationError, match="verified_on"):
        ProvenanceRef.model_validate(
            {**base, "verification_status": "verified", "verified_by": "Dr. R"}
        )
    ok = ProvenanceRef.model_validate(
        {
            **base,
            "verification_status": "verified",
            "verified_by": "Dr. R",
            "verified_on": date(2026, 1, 1),
        }
    )
    assert ok.is_verified


def test_invalid_verification_status_rejected() -> None:
    with pytest.raises(ValidationError, match="verification_status"):
        ProvenanceRef.model_validate(
            dict(source_id="s", locator="l", application="a", verification_status="approved")
        )


def test_deviation_requires_all_five_fields() -> None:
    full = dict(
        item="phenotype.case_rule",
        official_definition="X",
        deviation="Y",
        reason="Z",
        expected_impact="W",
    )
    Deviation.model_validate(full)
    for k in full:
        d = dict(full)
        del d[k]
        with pytest.raises(ValidationError, match=k):
            Deviation.model_validate(d)
