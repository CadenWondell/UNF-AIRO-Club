"""T029: DataEnvironmentPolicy matrix (contracts/dataset-adapter.md) and the V-03 rule source."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from clinical_ml_kits.core.errors import PendingVerification, PolicyViolation
from clinical_ml_kits.data.policy import (
    POLICIES,
    DisseminationRule,
    policy_for,
)
from clinical_ml_kits.provenance.models import SourceRecord

ROOT = Path(__file__).resolve().parents[3]
V03 = ROOT / "definitions" / "sources" / "aou_dissemination_policy.yaml"


def test_policy_matrix() -> None:
    syn, pub, aou = (policy_for(e) for e in ("synthetic", "public", "all_of_us_workbench"))
    assert set(POLICIES) == {"synthetic", "public", "all_of_us_workbench"}
    assert (syn.participant_level, aou.participant_level) == (False, True)
    assert syn.serialize_in_environment and pub.serialize_in_environment
    assert aou.serialize_in_environment
    assert syn.portable_artifacts is True
    assert aou.portable_artifacts is False
    assert syn.required_validation_level == "synthetic"
    assert pub.required_validation_level == "synthetic"
    assert aou.required_validation_level == "workbench"
    assert syn.dissemination_source_id is None and pub.dissemination_source_id is None
    assert aou.dissemination_source_id == "aou_dissemination_policy"


def test_unknown_environment() -> None:
    with pytest.raises(KeyError):
        policy_for("laptop_with_real_data")


def test_rule_built_only_from_v03_record() -> None:
    rec = SourceRecord.model_validate(yaml.safe_load(V03.read_text()))
    rule = DisseminationRule.from_source(rec)
    assert rule.source_id == "aou_dissemination_policy"
    assert rule.is_restricted(0) is False
    assert rule.is_restricted(rec.parameters["suppress_min"]) is True  # type: ignore[index]
    assert rule.is_restricted(rec.parameters["suppress_max"]) is True  # type: ignore[index]
    assert rule.is_restricted(rec.parameters["suppress_max"] + 1) is False  # type: ignore[index,operator]


def test_unresolved_v03_blocks_workbench_export(tmp_path: Path) -> None:
    data = yaml.safe_load(V03.read_text())
    data.update(verification_status="requires_verification", verified_by=None, verified_on=None)
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "aou_dissemination_policy.yaml").write_text(yaml.safe_dump(data))
    with pytest.raises(PendingVerification) as exc:
        policy_for("all_of_us_workbench").dissemination_rule(tmp_path)
    assert exc.value.item_id == "V-03"
    # missing record is equally blocking
    with pytest.raises(PendingVerification):
        policy_for("all_of_us_workbench").dissemination_rule(tmp_path / "nowhere")


def test_synthetic_has_no_rule() -> None:
    assert policy_for("synthetic").dissemination_rule(ROOT / "definitions") is None


def test_workbench_refuses_writes_inside_git_checkout(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    aou = policy_for("all_of_us_workbench")
    with pytest.raises(PolicyViolation):
        aou.check_write_path(repo / "kits" / "model.joblib")
    aou.check_write_path(tmp_path / "workspace" / "model.joblib")
    policy_for("synthetic").check_write_path(repo / "kits" / "model.joblib")


def test_policy_module_has_no_threshold_literal() -> None:
    src = (ROOT / "src" / "clinical_ml_kits" / "data" / "policy.py").read_text()
    import re

    assert not re.search(r"\b(19|20|21)\b", src)
