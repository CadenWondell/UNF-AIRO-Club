"""T059: logical concepts and per-namespace realizations (data-model § 2, R-24, P-5)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from clinical_ml_kits.core.errors import PendingVerification
from clinical_ml_kits.features.concept_sets import (
    SYNTHETIC_HEADER,
    ConceptRepository,
    ConceptSetRealization,
    LogicalConceptRef,
)

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "definitions"


@pytest.fixture()
def defs(tmp_path: Path) -> Path:
    d = tmp_path / "definitions"
    shutil.copytree(FIX, d)
    return d


def test_layout_and_resolution() -> None:
    repo = ConceptRepository(FIX)
    assert "fx_creatinine" in repo.concepts
    syn = repo.realization("synthetic", "fx_creatinine")
    assert syn.namespace == "synthetic" and syn.codes == ["SYN-FX-CREATININE"]
    assert syn.header == SYNTHETIC_HEADER
    omop = repo.realization("omop", "fx_creatinine", "0.1.0")
    assert omop.mapping_verified


def test_clinical_and_mapping_provenance_are_separate() -> None:
    repo = ConceptRepository(FIX)
    concept = repo.concept("fx_creatinine")
    real = repo.realization("synthetic", "fx_creatinine")
    assert concept.provenance is not real.provenance
    assert concept.provenance[0].application != real.provenance[0].application


def test_pinned_versions() -> None:
    ref = LogicalConceptRef(id="fx_bmi", version="0.1.0")
    assert ref.version == "0.1.0"
    with pytest.raises(ValidationError):
        LogicalConceptRef(id="fx_bmi", version="latest")
    with pytest.raises(PendingVerification):
        ConceptRepository(FIX).realization("synthetic", "fx_bmi", "9.9.9")


def test_unverified_omop_never_resolves(defs: Path) -> None:
    p = defs / "concept_sets" / "omop" / "fx_bmi" / "0.1.0.yaml"
    data = yaml.safe_load(p.read_text())
    data["provenance"][0]["verification_status"] = "requires_verification"
    data["provenance"][0].pop("content_hash", None)
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(PendingVerification):
        ConceptRepository(defs).realization("omop", "fx_bmi")


def test_missing_namespace_realization_raises(defs: Path) -> None:
    shutil.rmtree(defs / "concept_sets" / "omop" / "fx_sodium")
    with pytest.raises(PendingVerification):
        ConceptRepository(defs).realization("omop", "fx_sodium")


def test_synthetic_members_must_be_syn_codes() -> None:
    base = yaml.safe_load(
        (FIX / "concept_sets" / "synthetic" / "fx_bmi" / "0.1.0.yaml").read_text()
    )
    base["members"] = [{"concept_id": "3038553"}]
    with pytest.raises(ValidationError, match="SYN-"):
        ConceptSetRealization.model_validate(base)
    base["members"] = [{"concept_id": "SYN-FX-BMI"}]
    base["header"] = None
    with pytest.raises(ValidationError, match="header"):
        ConceptSetRealization.model_validate(base)


def test_domain_must_match_logical_concept(defs: Path) -> None:
    p = defs / "concept_sets" / "synthetic" / "fx_bmi" / "0.1.0.yaml"
    data = yaml.safe_load(p.read_text())
    data["domain"] = "condition"
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="domain"):
        ConceptRepository(defs).realization("synthetic", "fx_bmi")


def test_path_must_match_content(defs: Path) -> None:
    src = defs / "concept_sets" / "synthetic" / "fx_bmi" / "0.1.0.yaml"
    shutil.copy(src, defs / "concept_sets" / "synthetic" / "fx_bmi" / "0.2.0.yaml")
    with pytest.raises(ValueError, match="path"):
        _ = ConceptRepository(defs).realizations
