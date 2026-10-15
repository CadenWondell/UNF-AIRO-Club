"""T031: provenance checks P-1…P-11 (contracts/provenance.md)."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from clinical_ml_kits.core.kit_schema import ValidationContext, load_kit_definition
from clinical_ml_kits.provenance.checks import check_document, check_kit
from clinical_ml_kits.provenance.hashing import content_hash, stamp_hashes

FIX = Path(__file__).resolve().parents[2] / "fixtures"
CTX = ValidationContext.from_root(FIX)

CASES = {
    "p1_unresolved_source": ("P-1", "error"),
    "p2_missing_provenance": ("P-2", "error"),
    "p3_verified_no_verifier": ("P-3", "error"),
    "p5_omop_unverified": ("P-5", "error"),
    "p5_synthetic_bad_code": ("P-5", "error"),
    "p6_incomplete_deviation": ("P-6", "error"),
    "p7_edited_verified": ("P-7", "error"),
    "p8_broken_chain": ("P-8", "error"),
    "p9_low_tier_no_note": ("P-9", "warning"),
    "p10_provisional_missing_pending": ("P-10", "error"),
    "p11_verification_with_status": ("P-11", "error"),
}


def _load(name: str) -> dict[str, Any]:
    return yaml.safe_load((FIX / "provenance" / f"{name}.yaml").read_text())


@pytest.mark.parametrize("name", sorted(CASES))
def test_fixture_triggers_check(name: str) -> None:
    check_id, severity = CASES[name]
    fx = _load(name)
    findings = check_document(fx["kind"], fx["doc"], CTX)
    hits = [f for f in findings if f.check_id == check_id]
    assert hits, findings
    assert all(f.severity == severity for f in hits)


def test_clean_concept_has_no_findings() -> None:
    doc = yaml.safe_load((FIX / "definitions" / "concepts" / "fx_bmi.yaml").read_text())
    assert [f for f in check_document("concept", doc, CTX) if f.severity == "error"] == []


def test_p4_blocks_approved_kit() -> None:
    kit = FIX / "kits" / "invalid" / "approved_with_provisional.yaml"
    findings = check_kit(kit, CTX)
    assert any(f.check_id == "P-4" for f in findings)


def test_p7_stamped_hash_passes_and_edit_fails() -> None:
    fx = _load("p7_edited_verified")
    doc = stamp_hashes(copy.deepcopy(fx["doc"]))
    assert not [f for f in check_document("concept", doc, CTX) if f.check_id == "P-7"]
    doc["description"] = "silently edited"
    assert [f for f in check_document("concept", doc, CTX) if f.check_id == "P-7"]


def test_content_hash_ignores_verification_metadata() -> None:
    a = {"x": 1, "provenance": [{"verification_status": "verified", "verified_by": "A"}]}
    b = {"x": 1, "provenance": [{"verification_status": "draft", "verified_by": None}]}
    assert content_hash(a) == content_hash(b)
    assert content_hash(a) != content_hash({**a, "x": 2})


def test_verified_fixture_kit_is_clean() -> None:
    findings = check_kit(FIX / "kits" / "valid" / "verified_kit" / "kit.yaml", CTX)
    assert [f for f in findings if f.severity == "error"] == []


def test_loaded_kit_hash_is_stable() -> None:
    a = load_kit_definition(FIX / "kits" / "valid" / "provisional_kit.yaml")
    b = load_kit_definition(FIX / "kits" / "valid" / "provisional_kit.yaml")
    assert a.content_hash() == b.content_hash()
