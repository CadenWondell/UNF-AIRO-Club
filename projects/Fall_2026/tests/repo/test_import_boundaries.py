"""T069: adapter internals are imported only by their own package and data/registry.py."""

from __future__ import annotations

import ast
import shutil
from pathlib import Path

PKG = Path(__file__).resolve().parents[2] / "src" / "clinical_ml_kits"


def violations(pkg: Path) -> list[str]:
    out: list[str] = []
    for f in sorted(pkg.rglob("*.py")):
        rel = f.relative_to(pkg).as_posix()
        for node in ast.walk(ast.parse(f.read_text())):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            for m in mods:
                if not m.startswith("clinical_ml_kits.adapters."):
                    continue
                name = m.split(".")[2]
                if rel == "data/registry.py" or rel.startswith(f"adapters/{name}/"):
                    continue
                out.append(f"{rel} imports {m}")
    return out


def test_no_boundary_violations() -> None:
    assert violations(PKG) == []


def test_planted_bad_import_is_caught(tmp_path: Path) -> None:
    copy = tmp_path / "clinical_ml_kits"
    shutil.copytree(PKG, copy, ignore=shutil.ignore_patterns("__pycache__"))
    (copy / "cohort" / "bad.py").write_text(
        "from clinical_ml_kits.adapters.all_of_us.adapter import AllOfUsAdapter\n"
    )
    (copy / "adapters" / "synthetic_clinical" / "bad2.py").write_text(
        "import clinical_ml_kits.adapters.all_of_us.adapter\n"
    )
    v = violations(copy)
    assert any("cohort/bad.py" in x for x in v)
    assert any("synthetic_clinical/bad2.py" in x for x in v)
