"""T080: feature → logical concept → realization → domain/source table → SourceRecord (P-8)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from clinical_ml_kits.core.kit_schema import ValidationContext
from clinical_ml_kits.provenance.trace import TraceError, trace_feature

ROOT = Path(__file__).resolve().parents[3]
CTX = ValidationContext.from_root(ROOT)


@pytest.mark.parametrize("key", ["creatinine", "bmi", "outpatient_visits", "age"])
def test_chain_resolves_for_synthetic(key: str) -> None:
    chain = trace_feature(key, "synthetic", CTX)
    assert chain.logical_id and chain.concept_sources and chain.mapping_sources
    assert chain.source_table == "synthetic_observations"


def test_every_registry_feature_traces() -> None:
    for e in CTX.registry.features:
        trace_feature(e.feature_key, "synthetic", CTX)


def test_omop_chain_breaks_at_realization_until_verified() -> None:
    with pytest.raises(TraceError) as exc:
        trace_feature("creatinine", "omop", CTX)
    assert exc.value.link == "realization"


def test_fixture_omop_chain_resolves_with_table() -> None:
    chain = trace_feature(
        "fx_creatinine", "omop", ValidationContext.from_root(ROOT / "tests" / "fixtures")
    )
    assert chain.source_table == "measurement"


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    r = tmp_path / "root"
    shutil.copytree(ROOT / "definitions", r / "definitions")
    return r


def test_broken_concept_link(root: Path) -> None:
    (root / "definitions" / "concepts" / "creatinine.yaml").unlink()
    with pytest.raises(TraceError) as exc:
        trace_feature("creatinine", "synthetic", ValidationContext.from_root(root))
    assert exc.value.link == "logical_concept"


def test_broken_source_link(root: Path) -> None:
    (root / "definitions" / "sources" / "loinc.yaml").unlink()
    with pytest.raises(TraceError) as exc:
        trace_feature("creatinine", "synthetic", ValidationContext.from_root(root))
    assert exc.value.link == "concept_source"


def test_unknown_feature(root: Path) -> None:
    with pytest.raises(TraceError) as exc:
        trace_feature("nope", "synthetic", ValidationContext.from_root(root))
    assert exc.value.link == "feature"


def test_broken_mapping_source(root: Path) -> None:
    p = root / "definitions" / "concept_sets" / "synthetic" / "bmi" / "0.1.0.yaml"
    data = yaml.safe_load(p.read_text())
    data["provenance"][0]["source_id"] = "ghost_source"
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(TraceError) as exc:
        trace_feature("bmi", "synthetic", ValidationContext.from_root(root))
    assert exc.value.link == "mapping_source"
