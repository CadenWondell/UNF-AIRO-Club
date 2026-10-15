"""T063: synthetic adapter, golden backend."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from clinical_ml_kits.core.errors import PendingVerification
from clinical_ml_kits.data.registry import get_adapter

ROOT = Path(__file__).resolve().parents[3]
GOLDEN = ROOT / "synthetic" / "golden"


@pytest.fixture()
def adapter():  # type: ignore[no-untyped-def]
    return get_adapter("synthetic_clinical", backend="golden", golden=sorted(GOLDEN.glob("*.yaml")))


def test_serves_golden_fixtures(adapter) -> None:  # type: ignore[no-untyped-def]
    persons = adapter.persons()
    assert {"SYN-G-CREAT-001", "SYN-G-SD-001", "SYN-G-SPARSE-001", "SYN-G-MV-001"} <= set(
        persons.person_id
    )
    obs = adapter.observations(concepts=["creatinine"], person_ids=["SYN-G-CREAT-001"])
    assert list(obs.value_num) == [0.9, 1.0, 1.2, 1.5]
    assert set(obs.source_table) == {"synthetic_golden"}


def test_resolves_synthetic_namespace(adapter) -> None:  # type: ignore[no-untyped-def]
    real = adapter.resolve("creatinine")
    assert real.namespace == "synthetic"
    assert all(c.startswith("SYN-") for c in real.codes)
    assert adapter.metadata().namespace == "synthetic"
    assert adapter.policy().name == "synthetic"


def test_never_resolves_omop(adapter) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(PendingVerification):
        adapter.resolve_in_namespace("omop", "creatinine")


def test_filters_applied(adapter) -> None:  # type: ignore[no-untyped-def]
    t = pd.Timestamp("2025-12-31")
    obs = adapter.observations(concepts=["sodium", "potassium"], before=t)
    assert (obs.start_time < t).all()
    assert set(obs.logical_concept) <= {"sodium", "potassium"}
    assert (
        adapter.observations(domain="visit", concepts=["visit_outpatient"]).domain.eq("visit").all()
    )


def test_visits_and_index_candidates(adapter) -> None:  # type: ignore[no-untyped-def]
    v = adapter.visits(person_ids=["SYN-G-MV-001"])
    assert set(v.visit_type) == {"visit_outpatient", "visit_inpatient"}
    ic = adapter.index_candidates(["visit_outpatient"])
    assert {"person_id", "index_time", "index_visit_id", "visit_type"} <= set(ic.columns)
    assert set(ic.visit_type) == {"visit_outpatient"}


def test_unaccepted_unit_rejected(tmp_path: Path) -> None:
    text = (
        (GOLDEN / "creatinine_timeline.yaml")
        .read_text()
        .replace("value_num: 1.5, unit_raw: mg/dL", "value_num: 1.5, unit_raw: furlongs")
    )
    p = tmp_path / "g.yaml"
    p.write_text(text)
    a = get_adapter("synthetic_clinical", backend="golden", golden=[p])
    obs = a.observations(concepts=["creatinine"])
    assert 1.5 not in set(obs.value_num)
    assert a.unit_rejections == {"creatinine": 1}


def test_unknown_code_has_no_logical_concept(tmp_path: Path) -> None:
    text = (
        (GOLDEN / "creatinine_timeline.yaml")
        .read_text()
        .replace("SYN-CREATININE, value_num: 0.9", "SYN-UNMAPPED, value_num: 0.9")
    )
    p = tmp_path / "g.yaml"
    p.write_text(text)
    a = get_adapter("synthetic_clinical", backend="golden", golden=[p])
    assert 0.9 not in set(a.observations(concepts=["creatinine"]).value_num)
