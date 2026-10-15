"""T112: completion and serialization obey the DataEnvironmentPolicy."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from clinical_ml_kits.completion.portable import export_portable_definition
from clinical_ml_kits.completion.record import CompletionRecord
from clinical_ml_kits.completion.save import save_model
from clinical_ml_kits.core.errors import PolicyViolation
from clinical_ml_kits.data.policy import policy_for
from clinical_ml_kits.preprocessing import make_preprocessor


@pytest.fixture(scope="module")
def model(toy_kit, toy_data):  # type: ignore[no-untyped-def]
    return Pipeline(
        [
            ("preprocess", make_preprocessor(toy_kit.feature_spec)),
            ("model", LogisticRegression(max_iter=1000)),
        ]
    ).fit(toy_data.train.X, toy_data.train.y)


def test_complete_always_returns_record(toy_kit, model) -> None:  # type: ignore[no-untyped-def]
    rec = toy_kit.complete(model)
    assert isinstance(rec, CompletionRecord)
    assert rec.kit_id == "toy_binary" and rec.environment == "synthetic"
    assert rec.kit_definition_hash and rec.run_manifest_hash and rec.portable is False
    assert "validation" in rec.metrics


@pytest.mark.parametrize("env", ["synthetic", "public", "all_of_us_workbench"])
def test_non_portable_save_allowed_everywhere(tmp_path: Path, model, env: str) -> None:  # type: ignore[no-untyped-def]
    p = save_model(
        model,
        tmp_path / "ws" / "m.joblib",
        policy_for(env),
        portable=False,
        metadata={"kit_id": "toy_binary"},
    )
    assert p.exists() and p.with_suffix(".json").exists()
    assert json.loads(p.with_suffix(".json").read_text())["portable"] is False


def test_portable_refused_in_workbench(tmp_path: Path, model) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(PolicyViolation):
        save_model(
            model,
            tmp_path / "m.joblib",
            policy_for("all_of_us_workbench"),
            portable=True,
            metadata={},
        )
    p = save_model(
        model,
        tmp_path / "demo.joblib",
        policy_for("synthetic"),
        portable=True,
        metadata={"demo_model": True},
    )
    assert json.loads(p.with_suffix(".json").read_text())["portable"] is True


def test_workbench_refuses_writes_inside_checkout(tmp_path: Path, model) -> None:  # type: ignore[no-untyped-def]
    repo = tmp_path / "checkout"
    (repo / ".git").mkdir(parents=True)
    with pytest.raises(PolicyViolation):
        save_model(
            model,
            repo / "kits" / "m.joblib",
            policy_for("all_of_us_workbench"),
            portable=False,
            metadata={},
        )


def test_kit_save_model_uses_policy(toy_kit, model, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    assert toy_kit.save_model(model, tmp_path / "toy.joblib", portable=True).exists()


def test_portable_definition_has_no_data_or_model(toy_kit, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    out = export_portable_definition(toy_kit, tmp_path / "export")
    names = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
    assert {"kit.yaml", "phenotype.yaml", "metadata.json"} <= names
    assert any(n.startswith("docs/") for n in names)
    assert not any(n.endswith((".joblib", ".csv", ".parquet", ".pkl")) for n in names)
    meta = json.loads((out / "metadata.json").read_text())
    assert meta["kit_id"] == "toy_binary" and "SYN-P-" not in json.dumps(meta)
