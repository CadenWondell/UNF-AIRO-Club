"""T035: kit catalog (FR-080, FR-084)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from clinical_ml_kits.core.catalog import STATUSES, Catalog, CatalogEntry

ROOT = Path(__file__).resolve().parents[3]


def _entry(**over: object) -> dict[str, object]:
    d: dict[str, object] = dict(
        candidate_id="aou_x",
        name="X",
        dataset="all_of_us",
        status="candidate",
        reference=False,
        decision_rationale="",
        evaluation=None,
        decided_on=None,
        reviewer=None,
    )
    d.update(over)
    return d


def test_statuses() -> None:
    assert set(STATUSES) == {
        "candidate",
        "approved",
        "revised",
        "merged",
        "postponed",
        "replaced",
        "rejected",
    }


def test_invalid_status_rejected() -> None:
    with pytest.raises(ValidationError, match="status"):
        CatalogEntry.model_validate(_entry(status="shipped"))


@pytest.mark.parametrize(
    "status", ["approved", "revised", "merged", "postponed", "replaced", "rejected"]
)
def test_decision_needs_rationale_date_reviewer(status: str) -> None:
    with pytest.raises(ValidationError, match="decision_rationale"):
        CatalogEntry.model_validate(_entry(status=status))
    CatalogEntry.model_validate(
        _entry(
            status=status,
            decision_rationale="Insufficient positives",
            decided_on="2026-10-01",
            reviewer="Reviewer A",
            evaluation="kits/all_of_us/x/evidence/fr081.yaml",
        )
    )


def test_approved_needs_evaluation() -> None:
    with pytest.raises(ValidationError, match="evaluation"):
        CatalogEntry.model_validate(
            _entry(
                status="approved",
                decision_rationale="ok",
                decided_on="2026-10-01",
                reviewer="Reviewer A",
            )
        )


def test_candidate_may_carry_blockers() -> None:
    e = CatalogEntry.model_validate(
        _entry(verification_state="requires_verification", blockers=["V-21"])
    )
    assert e.blockers == ["V-21"]


def test_duplicate_ids_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        Catalog.model_validate({"catalog_version": 1, "entries": [_entry(), _entry()]})


def test_repository_catalog_loads() -> None:
    cat = Catalog.load(ROOT / "kits" / "catalog.yaml")
    assert len(cat.entries) == 25
    assert sum(e.reference for e in cat.entries) == 3
    assert {e.candidate_id for e in cat.entries if e.reference} == {
        "aou_t2d_current",
        "aou_ckd_current",
        "aou_htn_current",
    }
