"""T116: Template A notebook rendered for the toy kit."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest
import yaml

from clinical_ml_kits.cli import render_kit_notebook_text
from clinical_ml_kits.core.kit_schema import ValidationContext
from clinical_ml_kits.core.values import PROVISIONAL_BANNER
from clinical_ml_kits.notebooks.builder import SECTIONS
from clinical_ml_kits.notebooks.checks import check_notebook

FIX = Path(__file__).resolve().parents[1] / "fixtures"
TOY = FIX / "kits" / "toy_binary"
CTX = ValidationContext.from_root(FIX)


def nb_for(kit_yaml: Path) -> dict:
    return json.loads(render_kit_notebook_text(kit_yaml, CTX))


NB = nb_for(TOY / "kit.yaml")


def cells(role: str | None = None, section: int | None = None) -> list[str]:
    out = []
    for c in NB["cells"]:
        m = c["metadata"]
        if (role is None or m["ckit_role"] == role) and (
            section is None or m.get("ckit_section") == section
        ):
            out.append("".join(c["source"]))
    return out


def test_sections_in_contract_order() -> None:
    heads = [c for c in cells("markdown") if c.startswith("## ")]
    assert [h.splitlines()[0] for h in heads] == [f"## {n}. {t}" for n, t in SECTIONS]


def test_baseline_code_visible() -> None:
    src = "\n".join(cells("baseline"))
    for needle in (
        "from sklearn.linear_model import LogisticRegression",
        "from sklearn.pipeline import Pipeline",
        "make_preprocessor(kit.feature_spec)",
        "Pipeline([",
        ".fit(data.train.X, data.train.y)",
        ".predict_proba(data.validation.X)[:, 1]",
    ):
        assert needle in src, needle
    assert not re.search(r"fit_baseline\(|build_baseline\(", "\n".join(cells()))


def test_baseline_params_rendered_literally_and_track_kit_yaml(tmp_path: Path) -> None:
    params = yaml.safe_load((TOY / "kit.yaml").read_text())["baseline"]["params"]
    src = "\n".join(cells("baseline", 5))
    assert f"C={params['C']}" in src and f'penalty="{params["penalty"]}"' in src
    assert f"max_iter={params['max_iter']}" in src and "class_weight=None" in src
    root = tmp_path / "root"
    shutil.copytree(FIX, root, ignore=shutil.ignore_patterns("*.ipynb"))
    k = root / "kits" / "toy_binary" / "kit.yaml"
    k.write_text(k.read_text().replace("C: 1.0", "C: 0.25"))
    a = render_kit_notebook_text(k, ValidationContext.from_root(root))
    assert a == render_kit_notebook_text(k, ValidationContext.from_root(root))
    assert "LogisticRegression(C=0.25," in a and "LogisticRegression(C=1.0," not in a


def test_student_starters() -> None:
    src = "\n".join(cells("student"))
    for est in ("RandomForestClassifier(", "SVC(probability=True", "KNeighborsClassifier("):
        assert est in src, est
    assert "HistGradientBoostingClassifier(" in src or "GradientBoostingClassifier(" in src


def test_tuning_is_grouped_and_test_free() -> None:
    tuning = "\n".join(cells(section=8))
    assert "GridSearchCV(" in tuning and "kit.cv_splitter()" in tuning
    assert "groups=data.train.groups" in tuning
    for sec in (7, 8, 9, 10, 11):
        code = "\n".join(c for c in cells(section=sec) if c.startswith("# "))
        assert not re.search(r"\.test\b|final_evaluation|release_test", code), sec


def test_calibration_section() -> None:
    sec = "\n".join(cells(section=10))
    assert "kit.calibrate_grouped(" in sec and "CalibratedClassifierCV" not in sec
    assert "sampled development prevalence" in sec.lower() and "population" in sec.lower()


def test_provisional_banner() -> None:
    md = "\n".join(cells("markdown"))
    assert PROVISIONAL_BANNER in md
    assert "temporal_policy.same_day" in md and "pending V-20" in md


def test_content_rules_pass() -> None:
    assert check_notebook(NB) == []


@pytest.mark.parametrize("role", ["framework", "baseline"])
def test_no_placeholders(role: str) -> None:
    src = "\n".join(cells(role))
    assert "TODO" not in src and "NotImplementedError" not in src
