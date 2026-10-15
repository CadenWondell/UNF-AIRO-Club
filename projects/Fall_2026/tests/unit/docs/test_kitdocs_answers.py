"""T053: KitDocs completeness: six files, 12 FR-156 answers with resolving links, current log."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from clinical_ml_kits.core.kit_schema import KITDOCS, ValidationContext, load_kit_definition
from clinical_ml_kits.provenance.kitdocs import FR156_QUESTIONS, readme_issues
from clinical_ml_kits.provenance.report import log_path, render_for_kit

ROOT = Path(__file__).resolve().parents[3]
FIX = ROOT / "tests" / "fixtures"
KIT_DIRS = [
    *[(p.parent, ROOT) for p in sorted((ROOT / "kits").rglob("kit.yaml"))],
    *[(p.parent, FIX) for p in sorted((FIX / "kits").rglob("kit.yaml"))],
]


def test_twelve_questions() -> None:
    assert len(FR156_QUESTIONS) == 12


@pytest.mark.parametrize("kit_dir,root", KIT_DIRS, ids=lambda x: getattr(x, "name", ""))
def test_kitdocs_complete(kit_dir: Path, root: Path) -> None:
    kit = load_kit_definition(kit_dir)
    docs = kit_dir / kit.definition.docs
    for name in KITDOCS:
        assert (docs / name).is_file(), name
    assert readme_issues(docs) == []
    assert log_path(kit).read_text() == render_for_kit(kit, ValidationContext.from_root(root))


def test_missing_answer_detected(tmp_path: Path) -> None:
    src = FIX / "kits" / "valid" / "verified_kit" / "docs"
    docs = tmp_path / "docs"
    shutil.copytree(src, docs)
    text = (docs / "README.md").read_text()
    q = "## How were controls created?"
    start = text.index(q)
    end = text.index("## ", start + 3)
    (docs / "README.md").write_text(text[:start] + q + "\n\n" + text[end:])
    issues = readme_issues(docs)
    assert any("How were controls created?" in i for i in issues)


def test_broken_link_detected(tmp_path: Path) -> None:
    src = FIX / "kits" / "valid" / "verified_kit" / "docs"
    docs = tmp_path / "docs"
    shutil.copytree(src, docs)
    text = (docs / "README.md").read_text().replace("features.md#mapping-trace", "nope.md")
    (docs / "README.md").write_text(text)
    assert any("How do raw fields map" in i for i in readme_issues(docs))


def test_approval_level_runs_readme_check(tmp_path: Path) -> None:
    from clinical_ml_kits.core.errors import KitValidationError
    from clinical_ml_kits.core.kit_schema import validate_kit

    root = tmp_path / "root"
    shutil.copytree(FIX / "definitions", root / "definitions")
    shutil.copytree(FIX / "synthetic", root / "synthetic")
    kit_dir = root / "kits" / "v"
    shutil.copytree(FIX / "kits" / "valid" / "verified_kit", kit_dir)
    readme = kit_dir / "docs" / "README.md"
    readme.write_text(readme.read_text().replace("## Which items remain unverified?", "## Other"))
    with pytest.raises(KitValidationError, match="Which items remain unverified"):
        validate_kit(load_kit_definition(kit_dir), "approval", ValidationContext.from_root(root))
