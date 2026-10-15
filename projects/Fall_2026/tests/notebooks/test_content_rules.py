"""T047: notebook content rules (contracts/student-notebook.md)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from clinical_ml_kits.notebooks.checks import check_notebook

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "notebooks"
NEGATIVE = sorted((FIX / "negative").glob("*.ipynb"))
POSITIVE = sorted((FIX / "positive").glob("*.ipynb"))


def _load(p: Path) -> dict:
    return json.loads(p.read_text())


def test_fixture_sets_exist() -> None:
    assert len(NEGATIVE) >= 20 and POSITIVE


@pytest.mark.parametrize("path", POSITIVE, ids=lambda p: p.stem)
def test_positive_fixtures_pass(path: Path) -> None:
    assert check_notebook(_load(path)) == []


@pytest.mark.parametrize("path", NEGATIVE, ids=lambda p: p.stem)
def test_negative_fixtures_caught(path: Path) -> None:
    rule = path.stem.split("_", 1)[0].upper().replace("NB", "NB-")
    violations = check_notebook(_load(path))
    assert violations, f"{path.stem} not caught"
    assert any(v.rule == rule for v in violations), [str(v) for v in violations]
