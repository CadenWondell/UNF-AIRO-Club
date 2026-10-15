"""T051: generated, read-only verification logs (`ckit docs`)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from clinical_ml_kits.cli import main
from clinical_ml_kits.core.kit_schema import ValidationContext, load_kit_definition
from clinical_ml_kits.core.values import PROVISIONAL_BANNER
from clinical_ml_kits.provenance.report import load_verification_notes, render_verification_log

FIX = Path(__file__).resolve().parents[2] / "fixtures"
CTX = ValidationContext.from_root(FIX)
PROV = FIX / "kits" / "valid" / "provisional_kit.yaml"
VER = FIX / "kits" / "valid" / "verified_kit"


def test_deterministic_and_lists_states() -> None:
    kit = load_kit_definition(PROV)
    a = render_verification_log(kit, CTX, notes={})
    assert a == render_verification_log(kit, CTX, notes={})
    assert "GENERATED" in a and "Do not edit" in a
    assert PROVISIONAL_BANNER in a
    for item in ("temporal_policy.same_day", "phenotype.min_observation_history"):
        assert item in a
    assert "UNVERIFIED / REQUIRES REVIEW" in a and "dataset.version" in a


def test_notes_from_verification_yaml() -> None:
    kit = load_kit_definition(VER / "kit.yaml")
    notes = load_verification_notes(VER / "verification.yaml")
    text = render_verification_log(kit, CTX, notes=notes)
    assert "method_decision" in text and "diagnostic-workup leakage" in text
    assert "Fixture Reviewer" in text


def test_status_fields_rejected(tmp_path: Path) -> None:
    p = tmp_path / "verification.yaml"
    p.write_text("items:\n  x:\n    category: method_decision\n    note: n\n    status: verified\n")
    with pytest.raises(ValueError, match="P-11"):
        load_verification_notes(p)


def test_cli_docs_check_detects_hand_edit(tmp_path: Path) -> None:
    root = tmp_path / "root"
    shutil.copytree(FIX / "definitions", root / "definitions")
    shutil.copytree(FIX / "synthetic", root / "synthetic")
    shutil.copytree(VER, root / "kits" / "fixture" / "verified_kit")
    log = root / "kits" / "fixture" / "verified_kit" / "docs" / "verification_log.md"
    assert main(["docs", "--root", str(root)]) == 0
    assert main(["docs", "--root", str(root), "--check"]) == 0
    log.write_text(log.read_text() + "\nhand edit\n")
    assert main(["docs", "--root", str(root), "--check"]) != 0
    assert main(["docs", "--root", str(root), "--kit", "fixture_verified"]) == 0
    assert main(["docs", "--root", str(root), "--check"]) == 0


def test_committed_fixture_log_is_current() -> None:
    kit = load_kit_definition(VER / "kit.yaml")
    notes = load_verification_notes(VER / "verification.yaml")
    assert (VER / "docs" / "verification_log.md").read_text() == render_verification_log(
        kit, CTX, notes=notes
    )
