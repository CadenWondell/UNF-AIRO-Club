"""T038: `ckit validate` and `ckit catalog`."""

from __future__ import annotations

from pathlib import Path

import pytest

from clinical_ml_kits.cli import main

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "fixtures"
INV = FIX / "kits" / "invalid"
PROV = FIX / "kits" / "valid" / "provisional_kit.yaml"


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str]:
    code = main(list(argv))
    out = capsys.readouterr()
    return code, out.out + out.err


@pytest.mark.parametrize(
    "fixture,field",
    [
        ("bad_prediction_type", "prediction_type"),
        ("same_day_absent", "temporal_policy.same_day"),
        ("feature_also_prohibited", "prohibited"),
    ],
)
def test_invalid_fixture_exits_nonzero_naming_field(
    capsys: pytest.CaptureFixture[str], fixture: str, field: str
) -> None:
    code, out = run(capsys, "validate", str(INV / f"{fixture}.yaml"), "--root", str(FIX))
    assert code != 0
    assert field in out


def test_levels_on_provisional_fixture(capsys: pytest.CaptureFixture[str]) -> None:
    code, _ = run(capsys, "validate", str(PROV), "--root", str(FIX), "--level", "schema")
    assert code == 0
    code, _ = run(capsys, "validate", str(PROV), "--root", str(FIX), "--level", "synthetic")
    assert code == 0
    code, out = run(capsys, "validate", str(PROV), "--root", str(FIX), "--level", "workbench")
    assert code != 0
    for item in (
        "temporal_policy.same_day",
        "temporal_policy.washout",
        "phenotype.min_observation_history",
    ):
        assert item in out
    code, _ = run(capsys, "validate", str(PROV), "--root", str(FIX), "--level", "approval")
    assert code != 0


def test_validate_all_valid_fixtures(capsys: pytest.CaptureFixture[str]) -> None:
    code, out = run(
        capsys,
        "validate",
        "--all",
        str(FIX / "kits" / "valid"),
        "--root",
        str(FIX),
        "--level",
        "schema",
    )
    assert code == 0, out
    assert "fixture_provisional" in out and "fixture_verified" in out
    assert "requires_verification" in out and "level=schema" in out


def test_validate_all_fails_on_invalid(capsys: pytest.CaptureFixture[str]) -> None:
    code, _ = run(capsys, "validate", "--all", str(INV), "--root", str(FIX))
    assert code != 0


def test_catalog_table(capsys: pytest.CaptureFixture[str]) -> None:
    code, out = run(capsys, "catalog")
    assert code == 0
    assert "aou_t2d_current" in out and "candidate" in out
    assert out.count("\n") >= 26
