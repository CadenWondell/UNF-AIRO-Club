"""T049: committed notebooks equal their regenerated form (outputs stripped)."""

from __future__ import annotations

from pathlib import Path

import pytest

from clinical_ml_kits.cli import render_kit_notebook_text
from clinical_ml_kits.core.kit_schema import ValidationContext

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "fixtures"
NOTEBOOKS = [
    *[(p, ROOT) for p in sorted((ROOT / "kits").rglob("kit.ipynb"))],
    *[(p, FIX) for p in sorted((FIX / "kits").rglob("kit.ipynb"))],
]


@pytest.mark.parametrize("nb_path,root", NOTEBOOKS, ids=lambda x: getattr(x, "parent", x).name)
def test_no_drift(nb_path: Path, root: Path) -> None:
    expected = render_kit_notebook_text(
        nb_path.parent / "kit.yaml", ValidationContext.from_root(root)
    )
    assert nb_path.read_text() == expected, "regenerate with `ckit notebooks`"


def test_setup_check_no_drift() -> None:
    from clinical_ml_kits.notebooks.builder import build_setup_check, notebook_text

    p = ROOT / "kits" / "00_setup_check.ipynb"
    if p.exists():
        assert p.read_text() == notebook_text(build_setup_check())
